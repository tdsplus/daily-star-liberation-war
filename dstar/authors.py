"""Author listing pages as a discovery route.

Some 1971 series carry no 1971 term in their URLs (e.g. the 2021 "Road to
Freedom" entries are slugged by headline), so the sitemap filter misses them.
/author/<slug> listings are allowed by robots.txt and list a writer's pieces
newest first, with titles. Each page is fetched with the same polite Fetcher
(robots.txt, one request at a time, cache, stop on 403/challenge), and every
article link is recorded with its link text in discovery/author_listings.csv
for title-based triage. Nothing is added to candidates.csv here.

Usage:  python -m dstar.authors <author-slug> [<author-slug> ...]
"""
import csv
import os
import sys

from bs4 import BeautifulSoup

from .fetch import BASE, BlockedError, Fetcher
from .store import ROOT, canonical, is_article

OUT = os.path.join(ROOT, "discovery", "author_listings.csv")
MAX_PAGES = 150


def links(html, page_url):
    """Article links on a listing page, with the longest link text seen for each."""
    found = {}
    for a in BeautifulSoup(html, "lxml").find_all("a", href=True):
        u = canonical(a["href"], page_url)
        if is_article(u):
            t = a.get_text(" ", strip=True)
            if len(t) >= len(found.get(u, "")):
                found[u] = t
    return found


def crawl(fetcher, slug, writer):
    base = f"{BASE}/author/{slug}"
    seen, empty = set(), 0
    for page in range(MAX_PAGES):
        url = base if page == 0 else f"{base}?page={page}"
        status, html, _ = fetcher.get(url)
        if status != 200:
            print(f"{slug}: stop at page {page} (HTTP {status})")
            return
        found = links(html, url)
        fresh = {u: t for u, t in found.items() if u not in seen}
        seen.update(found)
        for u, t in fresh.items():
            writer.writerow([slug, page, u, t])
        print(f"{slug} p{page}: {len(found)} links, {len(fresh)} new")
        # Header/"most read" links repeat on every page, so the end of the
        # listing shows up as pages that add nothing new.
        empty = empty + 1 if not fresh else 0
        if empty >= 2:
            return


def main(argv):
    fetcher = Fetcher()
    fetcher.robots()
    new = not os.path.exists(OUT)
    with open(OUT, "a", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["author_slug", "page", "url", "link_text"])
        for slug in argv[1:]:
            try:
                crawl(fetcher, slug, w)
            except BlockedError as exc:
                print(f"BLOCKED: {exc}\nStopping -- not attempting to bypass.")
                sys.exit(2)
            fh.flush()


if __name__ == "__main__":
    main(sys.argv)
