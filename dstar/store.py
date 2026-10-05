"""URL canonicalisation and the candidates.csv staging file."""
import csv
import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, urlunsplit

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANDIDATES = os.path.join(ROOT, "candidates.csv")
BASE = "https://www.thedailystar.net"

# Daily Star article URLs end in a numeric node id: .../news/<slug>-1234567
ARTICLE_RE = re.compile(r"^/(?:[a-z0-9-]+/)*news/[a-z0-9%-]+-(\d{4,})/?$", re.I)
NODE_RE = re.compile(r"-(\d{4,})/?$")


def canonical(url, base=BASE):
    """Absolute https URL on www.thedailystar.net, no query/fragment/trailing slash."""
    url = urljoin(base, url.strip())
    parts = urlsplit(url)
    host = parts.netloc.lower()
    if host in ("thedailystar.net", "m.thedailystar.net", "www.thedailystar.net"):
        host = "www.thedailystar.net"
    path = re.sub(r"/{2,}", "/", parts.path).rstrip("/") or "/"
    return urlunsplit(("https", host, path, "", ""))


def is_article(url):
    parts = urlsplit(url)
    return parts.netloc.endswith("thedailystar.net") and bool(ARTICLE_RE.match(parts.path))


def node_id(url):
    """The article's numeric id -- the de-duplication key across URL variants."""
    m = NODE_RE.search(urlsplit(url).path)
    return m.group(1) if m else canonical(url)


def is_priority_section(url):
    """Slow Reads (incl. In Focus) or the legacy Views > In Focus path."""
    p = urlsplit(url).path.lower()
    return p.startswith("/slow-reads/") or p.startswith("/views/in-focus/")


class Candidates:
    FIELDS = ["url", "source_of_discovery", "first_seen"]

    def __init__(self, path=CANDIDATES):
        self.path = path
        self.rows = {}  # node_id -> row
        if os.path.exists(path):
            with open(path, newline="", encoding="utf-8") as fh:
                for row in csv.DictReader(fh):
                    self.rows[node_id(row["url"])] = row

    def add(self, url, source):
        url = canonical(url)
        if not is_article(url):
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
