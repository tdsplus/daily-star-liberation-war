"""Candidate discovery: listings, tag pages, sitemaps, search results, snowball.

Usage:
    python -m dstar.discover listings
    python -m dstar.discover tags
    python -m dstar.discover sitemaps
    python -m dstar.discover packages
    python -m dstar.discover search search_hits.csv
    python -m dstar.discover snowball
"""
import csv
import json
import os
import re
import sys
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from .fetch import BASE, Fetcher
from .store import ROOT, Candidates, canonical, is_article, is_priority_section, node_id

STATE = os.path.join(ROOT, "cache", "discover_state.json")
MAX_PAGES = 2000  # hard stop for any single listing

LISTINGS = {
    "listing:slow-reads": BASE + "/slow-reads",
    "listing:in-focus": BASE + "/slow-reads/focus",
    "listing:views-in-focus": BASE + "/views/in-focus",
    "listing:in-focus-legacy": BASE + "/in-focus",
}

# Tag pages seen in search results; more are harvested from fetched articles.
SEED_TAGS = {
    BASE + "/tags/1971-bangladesh-liberation-war": "1971 Bangladesh Liberation War",
    BASE + "/tags/liberation-war-bangladesh": "Liberation War of Bangladesh",
    BASE + "/tags/war-liberation": "War of Liberation",
    BASE + "/tags/operation-searchlight": "Operation Searchlight",
    BASE + "/tags/liberation-war": "Liberation War",
    BASE + "/tags/1971-liberation-war": "1971 Liberation War",
    BASE + "/tags/bijoy-dibosh": "Bijoy Dibosh",
    BASE + "/tags/tajuddin-ahmad": "Tajuddin Ahmad",
    BASE + "/tags/bangladesh-war-crimes-trial": "Bangladesh war crimes trial",
    BASE + "/tags/international-crimes-tribunal": "International Crimes Tribunal",
}

# Themed listings seen in search results that no candidate path reveals.
SEED_PACKAGES = [
    BASE + "/1971-liberation-war-interviews",
    BASE + "/supplements/martyred-intellectuals-day-2017",
]

# Tag names we look for; matched against the tag's slug and its visible label.
TAG_TERMS = re.compile(
    r"liberation[- ]war|1971|muktijuddh|mukti[- ]?bahini|genocide|freedom[- ]fighter|"
    r"mujibnagar|victory[- ]day|bijoy|razakar|al[- ]badr|war[- ]crime|birangona|"
    r"martyred[- ]intellectual|operation[- ]searchlight|independence[- ]day|"
    r"bangabandhu|6[- ]point|six[- ]point|7[- ]march|march[- ]7|language[- ]movement",
    re.I,
)


# Outside Slow Reads the site has far too many articles to fetch them all, so
# sitemap URLs from other sections are kept only when the slug signals the topic.
SLUG_TERMS = re.compile(
    r"liberation-war|1971|muktijuddh|mukti-bahini|genocide|razakar|al-badr|al-shams|"
    r"freedom-fighter|birangona|mujibnagar|searchlight|victory-day|bijoy-dibos|"
    r"war-crime|war-criminal|ict-|tribunal|martyred-intellectual|intellectuals-day|"
    r"tajuddin|archer-blood|kissinger|six-point|6-point|7-march|march-7|"
    r"pakistan-army|surrender|independence-day|swadhinata|1970-election",
    re.I,
)


def _state():
    if os.path.exists(STATE):
        with open(STATE, encoding="utf-8") as fh:
            return json.load(fh)
    return {"done_pages": {}, "tags": {}}


def _save_state(st):
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(st, fh, indent=1)
    os.replace(tmp, STATE)


def article_links(html, page_url):
    soup = BeautifulSoup(html, "lxml")
    out = []
    for a in soup.find_all("a", href=True):
        u = canonical(a["href"], page_url)
        if is_article(u):
            out.append(u)
    return list(dict.fromkeys(out))


def tag_links(html, page_url):
    soup = BeautifulSoup(html, "lxml")
    out = {}
    for a in soup.find_all("a", href=True):
        u = canonical(a["href"], page_url)
        if urlsplit(u).path.startswith("/tags/"):
            out[u] = a.get_text(" ", strip=True)
    return out


def paginate(fetcher, cands, st, base_url, source, priority_only=False):
    """Walk ?page=0,1,2... until a page 404s or yields no new article links."""
    start = st["done_pages"].get(base_url, -1) + 1
    seen_on_listing = set()
    empty_streak = 0
    for page in range(start, MAX_PAGES):
        url = base_url if page == 0 else f"{base_url}?page={page}"
        status, html, _ = fetcher.get(url)
        if status != 200:
            print(f"  {source}: stop at page {page} (HTTP {status})")
            break
        links = [u for u in article_links(html, url)
                 if not priority_only or is_priority_section(u)]
        fresh = [u for u in links if node_id(u) not in seen_on_listing]
        seen_on_listing.update(node_id(u) for u in links)
        added = sum(cands.add(u, source) for u in fresh)
        print(f"  {source} p{page}: {len(links)} links, {len(fresh)} new on listing, "
              f"{added} new candidates (total {len(cands)})")
        st["done_pages"][base_url] = page
        cands.save()
        _save_state(st)
        # Listing pages also carry site-wide nav/"most read" links, so judge the
        # end of pagination by whether the page produced anything new.
        empty_streak = empty_streak + 1 if not fresh else 0
        if empty_streak >= 2:
            print(f"  {source}: no new links for 2 pages, stopping at page {page}")
            break


SUBSECTION_RE = re.compile(r"^/slow-reads/[a-z0-9-]+(?:/[a-z0-9-]+)?$")


def slow_reads_subsections(fetcher, cands):
    """Slow Reads subsection/package listings, from the landing page's links
    and from the paths of candidates already found."""
    found = set()
    status, html, _ = fetcher.get(LISTINGS["listing:slow-reads"])
    if status == 200:
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            u = canonical(a["href"])
            if SUBSECTION_RE.match(urlsplit(u).path) and not is_article(u):
                found.add(u)
    for row in cands.rows.values():
        path = urlsplit(row["url"]).path
        if path.startswith("/slow-reads/") and "/news/" in path:
            found.add(BASE + path.split("/news/", 1)[0])
    return sorted(found - set(LISTINGS.values()))


def run_listings(fetcher, cands):
    st = _state()
    for source, url in LISTINGS.items():
        paginate(fetcher, cands, st, url, source, priority_only=True)
    subs = slow_reads_subsections(fetcher, cands)
    print(f"{len(subs)} Slow Reads subsections: {subs}")
    for url in subs:
        paginate(fetcher, cands, st, url, "listing:" + urlsplit(url).path[1:],
                 priority_only=True)


def collect_tags_from_cache(cands):
    """Find tag pages linked from already-fetched candidate articles."""
    from .fetch import FETCH_LOG
    tags = {}
    if not os.path.exists(FETCH_LOG):
        return tags
    with open(FETCH_LOG, encoding="utf-8") as fh:
        recs = [json.loads(line) for line in fh if line.strip()]
    for rec in recs:
        if rec.get("status") != 200 or not rec.get("cache") or not is_article(rec["url"]):
            continue
        with open(os.path.join(ROOT, rec["cache"]), encoding="utf-8") as fh:
            for u, label in tag_links(fh.read(), rec["url"]).items():
                tags.setdefault(u, label)
    return tags


def run_tags(fetcher, cands):
    st = _state()
    found = dict(SEED_TAGS)
    found.update(collect_tags_from_cache(cands))
    for u, label in found.items():
        slug = urlsplit(u).path.split("/tags/", 1)[1]
        if TAG_TERMS.search(slug) or TAG_TERMS.search(label):
            st["tags"].setdefault(u, label)
    _save_state(st)
    print(f"{len(st['tags'])} relevant tag pages: {sorted(st['tags'])}")
    for u in sorted(st["tags"]):
        # Tag pages are site-wide; keep every article (non-priority ones feed
        # the "Other sections" sheet).
        paginate(fetcher, cands, st, u, "tag:" + urlsplit(u).path.split("/tags/", 1)[1])


def package_listings(cands):
    """Themed listings (supplements, special series) that hold relevant articles,
    inferred from the paths of candidates, e.g. /supplements/victory-day-special-2021."""
    found = set()
    for row in cands.rows.values():
        path = urlsplit(row["url"]).path
        parent = path.split("/news/", 1)[0] if "/news/" in path else path.rsplit("/", 1)[0]
        if parent and parent != "/" and SLUG_TERMS.search(parent) \
                and not parent.startswith("/slow-reads"):
            found.add(BASE + parent)
    return sorted(found)


def run_packages(fetcher, cands):
    st = _state()
    pkgs = sorted(set(package_listings(cands)) | set(SEED_PACKAGES))
    print(f"{len(pkgs)} themed package listings: {pkgs}")
    for url in pkgs:
        paginate(fetcher, cands, st, url, "package:" + urlsplit(url).path[1:])


def _sitemap_locs(text):
    soup = BeautifulSoup(text, "xml")
    return [l.get_text(strip=True) for l in soup.find_all("loc")]


def run_sitemaps(fetcher, cands):
    roots = set()
    robots = fetcher.robots()
    roots.update(getattr(robots, "site_maps", lambda: None)() or [])
    roots.add(BASE + "/sitemap.xml")
    queue, seen = list(roots), set()
    while queue:
        sm = queue.pop(0)
        if sm in seen:
            continue
        seen.add(sm)
        status, text, _ = fetcher.get(sm)
        if status != 200:
            print(f"  sitemap {sm}: HTTP {status}")
            continue
        locs = _sitemap_locs(text)
        if "<sitemapindex" in text[:2000]:
            queue.extend(locs)
            print(f"  sitemap index {sm}: {len(locs)} child sitemaps")
            continue
        added = 0
        for loc in locs:
            u = canonical(loc)
            if is_priority_section(u):
                added += cands.add(u, "sitemap")
            elif SLUG_TERMS.search(urlsplit(u).path):
                added += cands.add(u, "sitemap:slug")
        cands.save()
        print(f"  sitemap {sm}: {len(locs)} urls, {added} new candidates")


def run_search(cands, path):
    """Import search hits gathered outside this crawler (url,keyword per row)."""
    added = 0
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            added += cands.add(row["url"], "search:" + row["keyword"], loose=True)
    cands.save()
    print(f"search: {added} new candidates (total {len(cands)})")


def run_snowball(fetcher, cands):
    """Add Daily Star article links found inside Core/Borderline articles."""
    from .classify import load_labels
    from .extract import load_records
    labels = load_labels()
    recs = load_records()
    added = 0
    for key, lab in labels.items():
        if lab["label"] not in ("Core", "Borderline") or key not in recs:
            continue
        for u in recs[key].get("body_links", []):
            added += cands.add(u, "snowball:" + key)
    cands.save()
    print(f"snowball: {added} new candidates (total {len(cands)})")


def main(argv):
    cmd = argv[1] if len(argv) > 1 else ""
    cands = Candidates()
    if cmd == "search":
        return run_search(cands, argv[2])
    fetcher = Fetcher()
    fetcher.robots()
    {"listings": run_listings, "tags": run_tags,
     "sitemaps": run_sitemaps, "snowball": run_snowball,
     "packages": run_packages}[cmd](fetcher, cands)


if __name__ == "__main__":
    main(sys.argv)
