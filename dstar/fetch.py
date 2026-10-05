"""Polite, cached, resumable HTTP fetcher for thedailystar.net.

Rules enforced here:
  * robots.txt is fetched first and every URL is checked against it
  * one request at a time, at least MIN_DELAY seconds apart
  * retries with exponential backoff on 429 / 5xx / connection errors
  * any sign of bot protection (403, captcha, Cloudflare challenge) raises
    BlockedError and the run stops -- we never try to get round it
  * every response is cached on disk and logged, so nothing is re-fetched
"""
import gzip
import hashlib
import json
import os
import time
import urllib.robotparser
from datetime import datetime, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE_DIR = os.path.join(ROOT, "cache", "html")
FETCH_LOG = os.path.join(ROOT, "cache", "fetch_log.jsonl")

USER_AGENT = (
    "LiberationWar1971-ArchiveIndexer/1.0 "
    "(non-commercial research index of Daily Star articles; "
    "polite crawler, 1 request every 2.5s)"
)
MIN_DELAY = 2.5
MAX_RETRIES = 4
BASE = "https://www.thedailystar.net"

CHALLENGE_MARKERS = (
    "cf-chl-",
    "challenge-platform",
    "Just a moment...",
    "Attention Required! | Cloudflare",
    "g-recaptcha",
    "h-captcha",
    "captcha-delivery",
)


class BlockedError(RuntimeError):
    """The site (or the network) refused automated access. Stop the run."""


def _now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _cache_path(url):
    return os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".html")


class Fetcher:
    def __init__(self):
        os.makedirs(CACHE_DIR, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en",
        })
        self._last = 0.0
        self._log = self._load_log()
        self._robots = None

    # ---- log -------------------------------------------------------------
    def _load_log(self):
        log = {}
        if os.path.exists(FETCH_LOG):
            with open(FETCH_LOG, encoding="utf-8") as fh:
                for line in fh:
                    try:
                        rec = json.loads(line)
                    except ValueError:
                        continue
                    log[rec["url"]] = rec
        return log

    def _write_log(self, rec):
        self._log[rec["url"]] = rec
        with open(FETCH_LOG, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")

    def failures(self):
        return [r for r in self._log.values() if r.get("status") != 200]

    # ---- robots ----------------------------------------------------------
    def robots(self):
        if self._robots is None:
            rp = urllib.robotparser.RobotFileParser()
            status, text, _ = self.get(BASE + "/robots.txt", check_robots=False)
            if status != 200:
                raise BlockedError(f"robots.txt returned HTTP {status}")
            # Python's parser ends a group at a blank line, which would drop the
            # site's trailing "Disallow: /tags/" for "*". Per RFC 9309 blank
            # lines do not end a group, so parse without them (the stricter reading).
            rp.parse([l for l in text.splitlines() if l.strip()])
            self._robots = rp
            delay = rp.crawl_delay(USER_AGENT) or rp.crawl_delay("*")
            global MIN_DELAY
            if delay and float(delay) > MIN_DELAY:
                MIN_DELAY = float(delay)
        return self._robots

    def allowed(self, url):
        return self.robots().can_fetch(USER_AGENT, url)

    # ---- fetch -----------------------------------------------------------
    def _wait(self):
        gap = time.monotonic() - self._last
        if gap < MIN_DELAY:
            time.sleep(MIN_DELAY - gap)
        self._last = time.monotonic()

    def get(self, url, check_robots=True, refresh=False):
        """Return (status, text, final_url). Served from cache when possible."""
        path = _cache_path(url)
        rec = self._log.get(url)
        if not refresh and rec and rec.get("status") == 200 and os.path.exists(path):
            with open(path, encoding="utf-8") as fh:
                return 200, fh.read(), rec.get("final_url", url)
        if not refresh and rec and rec.get("status") == 404:
            return 404, "", url
        if check_robots and not self.allowed(url):
            self._write_log({"url": url, "status": "robots-disallowed", "at": _now()})
            return None, "", url

        last_err = None
        for attempt in range(MAX_RETRIES + 1):
            self._wait()
            try:
                resp = self.session.get(url, timeout=30)
            except requests.exceptions.ProxyError as exc:
                raise BlockedError(f"network/proxy refused connection to {url}: {exc}")
            except requests.RequestException as exc:
                last_err = str(exc)
                time.sleep(2 ** (attempt + 1))
                continue

            if resp.content[:2] == b"\x1f\x8b":  # raw .gz sitemap
                body = gzip.decompress(resp.content).decode("utf-8", "replace")
            else:
                body = resp.text
            if resp.status_code == 403 or any(m in body[:20000] for m in CHALLENGE_MARKERS):
                self._write_log({"url": url, "status": resp.status_code, "at": _now(),
                                 "note": "blocked/challenge"})
                raise BlockedError(f"HTTP {resp.status_code} / bot challenge at {url}")
            if resp.status_code == 429 or resp.status_code >= 500:
                last_err = f"HTTP {resp.status_code}"
                retry_after = resp.headers.get("Retry-After", "")
                time.sleep(int(retry_after) if retry_after.isdigit() else 2 ** (attempt + 2))
                continue

            rec = {"url": url, "status": resp.status_code, "final_url": resp.url, "at": _now()}
            if resp.status_code == 200:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(body)
                rec["cache"] = os.path.relpath(path, ROOT)
            self._write_log(rec)
            return resp.status_code, body if resp.status_code == 200 else "", resp.url

        self._write_log({"url": url, "status": "error", "error": last_err, "at": _now()})
        return None, "", url
