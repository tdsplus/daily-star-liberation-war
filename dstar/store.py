"""URL canonicalisation and the candidates.csv staging file."""
import csv
import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, urlunsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES = os.path.join(ROOT, "candidates.csv")
BASE = "https://www.thedailystar.net"

# Daily Star article URLs end in a numeric node id. Current form:
# /<section>/news/<slug>-1234567; older forms omit "news" (/<slug>-52351).
ARTICLE_RE = re.compile(r"^/(?:[a-z0-9-]+/)*[a-z0-9%-]+-(\d{4,})/?$", re.I)
NOT_ARTICLE = re.compile(r"^/(?:tags|author|topic|topics|search|archive)/", re.I)
# Search engines sometimes return id-less aliases (/news/<slug>, or
# /<section>/<long-slug>); they are resolved to the canonical URL at
# extraction time, which also flags any that turn out not to be articles.
LOOSE_ARTICLE_RE = re.compile(
    r"^/(?:(?:[a-z0-9-]+/)*news/[a-z0-9%-]+-[a-z0-9%-]+|"
    r"(?:[a-z0-9-]+/)+[a-z0-9%]+(?:-[a-z0-9%]+){3,})/?$", re.I)
NODE_RE = re.compile(r"-(\d{4,})/?$")


def canonical(url, base=BASE):
    """Absolute https URL on www.thedailystar.net, no query/fragment/trailing slash."""
    url = urljoin(base, url.strip())
    parts = urlsplit(url)
    host = parts.netloc.lower()
    # Old archive print view: archive.thedailystar.net/...print_news.php?nid=N
    m = re.search(r"(?:^|&)nid=(\d+)", parts.query)
    if host == "archive.thedailystar.net" and m:
        return f"{BASE}/news-detail-{m.group(1)}"
    if host in ("thedailystar.net", "m.thedailystar.net", "www.thedailystar.net",
                "images.thedailystar.net", "online.thedailystar.net",
                "sandbox.thedailystar.net"):  # these serve mirror copies of www pages
        host = "www.thedailystar.net"
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    return urlunsplit(("https", host, path, "", ""))


def is_article(url, loose=False):
    parts = urlsplit(url)
    if parts.netloc != "www.thedailystar.net" or NOT_ARTICLE.match(parts.path):
        return False
    m = ARTICLE_RE.match(parts.path)
    if m and len(m.group(1)) == 4 and 1900 <= int(m.group(1)) <= 2099:
        m = None  # a trailing year (e.g. /supplements/victory-day-2017), not a node id
    return bool(m or (loose and LOOSE_ARTICLE_RE.match(parts.path)))


def node_id(url):
    """The article's numeric id -- the de-duplication key across URL variants."""
    m = NODE_RE.search(urlsplit(url).path)
    if m and not (len(m.group(1)) == 4 and 1900 <= int(m.group(1)) <= 2099):
        return m.group(1)
    return canonical(url)


def is_priority_section(url):
    """Slow Reads (incl. In Focus) or In Focus under its older paths."""
    p = urlsplit(url).path.lower()
    return p.startswith(("/slow-reads/", "/views/in-focus/", "/in-focus/"))


class Candidates:
    FIELDS = ["url", "source_of_discovery", "first_seen"]

    def __init__(self, path=CANDIDATES):
        self.path = path
        self.rows = {}  # node_id -> row
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    self.rows[node_id(row["url"])] = row

    def add(self, url, source, loose=False):
        url = canonical(url)
        if not is_article(url, loose):
            return False
        key = node_id(url)
        if key in self.rows:
            row = self.rows[key]
            sources = row["source_of_discovery"].split("|")
            if source not in sources:
                row["source_of_discovery"] = "|".join(sources + [source])
            return False
        self.rows[key] = {
            "url": url,
            "source_of_discovery": source,
            "first_seen": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        return True

    def save(self):
        tmp = self.path + ".tmp"
        with open(tmp, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=self.FIELDS)
            w.writeheader()
            for row in self.rows.values():
                w.writerow(row)
        os.replace(tmp, self.path)

    def __len__(self):
        return len(self.rows)
