"""Fetch every candidate and extract metadata + full text.

Order of preference for each field: JSON-LD -> og:/meta tags -> visible HTML.
Results go to cache/articles.jsonl (one record per node id, resumable) and the
article text to cache/text/<node_id>.txt.

Usage:  python -m dstar.extract
"""
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone

from bs4 import BeautifulSoup

from .fetch import BlockedError, Fetcher
from .store import ROOT, Candidates, canonical, is_article, is_priority_section, node_id

RECORDS = os.path.join(ROOT, "cache", "articles.jsonl")
TEXT_DIR = os.path.join(ROOT, "cache", "text")
DHAKA = timezone(timedelta(hours=6))
BOILERPLATE = re.compile(r"^(Read More|Editor's Pick|Related News|Send your articles for Slow Reads|"
                         r"Follow The Daily Star|Check out our submission guidelines)", re.I)
BOILERPLATE_ANY = re.compile(r"Google News channel|as a trusted source", re.I)
ARTICLE_TYPES = {"NewsArticle", "Article", "ReportageNewsArticle", "OpinionNewsArticle",
                 "AnalysisNewsArticle", "BlogPosting"}


def text_path(nid):
    """Cache file for an article's text; id-less pages get a hashed name."""
    import hashlib
    name = nid if nid.isdigit() else "u_" + hashlib.sha1(nid.encode()).hexdigest()[:16]
    return os.path.join(TEXT_DIR, name + ".txt")


def load_records():
    recs = {}
    if os.path.exists(RECORDS):
        with open(RECORDS, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    r = json.loads(line)
                    recs[r["node_id"]] = r
    return recs


def _jsonld_articles(soup):
    found = []

    def walk(obj):
        if isinstance(obj, list):
            for o in obj:
                walk(o)
        elif isinstance(obj, dict):
            t = obj.get("@type")
            types = set(t) if isinstance(t, list) else {t}
            if types & ARTICLE_TYPES:
                found.append(obj)
            for k in ("@graph", "mainEntity"):
                if k in obj:
                    walk(obj[k])

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            walk(json.loads(tag.string or tag.get_text() or ""))
        except ValueError:
            continue
    return found


def _names(author):
    if not author:
        return []
    if isinstance(author, (str, dict)):
        author = [author]
    out = []
    for a in author:
        name = a.get("name") if isinstance(a, dict) else a
        if isinstance(name, str) and name.strip():
            out.append(re.sub(r"\s+", " ", name).strip())
    return out


def _meta(soup, *keys):
    for k in keys:
        tag = soup.find("meta", attrs={"property": k}) or soup.find("meta", attrs={"name": k})
        if tag and tag.get("content", "").strip():
            return tag["content"].strip()
    return ""


def _body(soup):
    """Return (container, text) for the article body.

    Current templates (all years, as re-rendered by the site's Drupal theme)
    keep the body in .block-field-blocknodenewsbody; the surrounding <article>
    also wraps the sidebar ("Editor's Pick", most-viewed cards), so it is only
    a last resort."""
    node = None
    for sel in (".block-field-blocknodenewsbody", "[itemprop=articleBody]", ".article-body"):
        node = soup.select_one(sel)
        if node and len(node.get_text(" ", strip=True)) > 50:
            break
        node = None
    if node is None:
        best = 0
        for div in soup.find_all(["div", "section"]):
            n = sum(len(p.get_text(strip=True)) for p in div.find_all("p", recursive=False))
            if n > best:
                best, node = n, div
    if node is None:
        return None, ""
    for junk in node.select("script, style, aside, nav, form, iframe, .related, .social, .share"):
        junk.decompose()
    full = node.get_text("\n", strip=True)
    paras = [p.get_text(" ", strip=True) for p in node.find_all(["p", "h2", "h3", "blockquote", "li"])]
    # Older articles use <br> line breaks rather than <p>; fall back to full text.
    if sum(len(p) for p in paras) < 0.6 * len(full):
        paras = [l.strip() for l in full.split("\n")]
    paras = [p for p in paras
             if p and not BOILERPLATE.match(p) and not BOILERPLATE_ANY.search(p)]
    return node, "\n\n".join(paras)


def _ga(html, key):
    m = re.search(r'"tds_ga_dimensions":\{[^}]*?"%s":"([^"]*)"' % key, html)
    return m.group(1) if m else ""


def parse(html, url):
    soup = BeautifulSoup(html, "lxml")
    lds = _jsonld_articles(soup)
    ld = lds[0] if lds else {}
    flags = []

    canon_tag = soup.find("link", rel="canonical")
    canon = canonical(canon_tag["href"]) if canon_tag and canon_tag.get("href") else ""
    canon = canon or canonical(_meta(soup, "og:url") or url)

    title = (ld.get("headline") or _meta(soup, "og:title") or
             (soup.h1.get_text(" ", strip=True) if soup.h1 else ""))
    title = re.sub(r"\s+", " ", title).strip()
    title = re.sub(r"\s*\|\s*The Daily Star\s*$", "", title)

    date = ld.get("datePublished") or _meta(
        soup, "article:published_time", "og:article:published_time", "publish-date",
        "pubdate", "datePublished")
    date_src = "jsonld" if ld.get("datePublished") else ("meta" if date else "")
    if not date:
        t = soup.find(attrs={"itemprop": "datePublished"})
        if t:
            date = t.get("content") or t.get("datetime") or ""
            date_src = "html-itemprop" if date else ""
    if not date:
        # Drupal node "created" (authored-on) timestamp in the page's analytics
        # config. The visible "Updated : ..." line is deliberately ignored.
        m = re.search(r'"tds_ga_dimensions":\{[^}]*?"created":"(\d{9,11})"', html)
        if m:
            date = datetime.fromtimestamp(int(m.group(1)), DHAKA).isoformat()
            date_src = "drupal-created"
    if not date:
        m = re.search(r'"created":"\w{3}, (\d{2})\\?/(\d{2})\\?/(\d{4}) - (\d{2}):(\d{2})"', html)
        if m:
            mo, d, y, hh, mm = m.groups()
            date = f"{y}-{mo}-{d}T{hh}:{mm}:00+06:00"
            date_src = "drupal-created"
    if not date:
        flags.append("no-date")

    authors = _names(ld.get("author"))
    author_src = "jsonld" if authors else ""
    if not authors:
        m = _meta(soup, "author", "article:author", "dable:author")
        if m and not m.startswith("http"):
            authors, author_src = [m], "meta"
    if not authors:
        # Only the article's own author block -- pages also carry ".author"
        # names on related-article cards, which must not be picked up.
        block = soup.select_one(".block-author-info-block")
        if block:
            names = [a.get_text(" ", strip=True) for a in block.select("a[href*='/author/']")]
            if not names:
                names = [n.get_text(" ", strip=True) for n in block.select(".font-medium")]
            authors = [n for n in dict.fromkeys(names) if n]
            author_src = "html:author-block" if authors else ""
    authors = [a for a in authors if a.lower() not in ("the daily star", "daily star")] or authors
    if not authors:
        flags.append("no-author")

    section = ld.get("articleSection") or _meta(soup, "article:section")
    if isinstance(section, list):
        section = ", ".join(section)
    crumbs = [a.get_text(strip=True) for a in soup.select(".breadcrumb a, nav.breadcrumb a")]

    node, text = _body(soup)
    body_links = []
    if node is not None:
        for a in node.find_all("a", href=True):
            u = canonical(a["href"], url)
            if is_article(u):
                body_links.append(u)
    tags = [a.get_text(strip=True) for a in soup.select("a[href*='/tags/']")]
    if len(text) < 300:
        flags.append("short-text")
    og_type = _meta(soup, "og:type").lower()
    if not lds and og_type not in ("article", "news", "newsarticle"):
        flags.append("not-article")

    return {
        "node_id": node_id(canon if is_article(canon) else url),
        "fetched_url": url,
        "canonical_url": canon,
        "title": title,
        "date_published": date,
        "date_source": date_src,
        "date_modified": ld.get("dateModified") or _meta(soup, "article:modified_time"),
        "author": "; ".join(dict.fromkeys(authors)),
        "author_source": author_src,
        "section": section or "",
        "news_type": _ga(html, "NewsType"),
        "desk": _ga(html, "Desk"),
        "ld_type": ld.get("@type", "") if isinstance(ld.get("@type", ""), str)
                   else ", ".join(ld["@type"]),
        "breadcrumbs": crumbs,
        "tags": list(dict.fromkeys(tags)),
        "description": ld.get("description") or _meta(soup, "description", "og:description"),
        "body_links": list(dict.fromkeys(body_links)),
        "text_chars": len(text),
        "word_count": len(text.split()),
        "flags": flags,
    }, text


def main(argv):
    os.makedirs(TEXT_DIR, exist_ok=True)
    fetcher = Fetcher()
    fetcher.robots()
    cands = Candidates()
    recs = load_records()
    done = {r["node_id"] for r in recs.values()} | {
        node_id(r["fetched_url"]) for r in recs.values()}
    todo = [row for key, row in cands.rows.items() if key not in done]
    # Priority section (Slow Reads / In Focus) first, so the main sheet can be
    # built before the rest of the site is finished.
    todo.sort(key=lambda row: not is_priority_section(row["url"]))
    print(f"{len(cands)} candidates, {len(todo)} still to extract")
    with open(RECORDS, "a", encoding="utf-8") as out:
        for i, row in enumerate(todo, 1):
            try:
                status, html, final = fetcher.get(row["url"])
            except BlockedError as exc:
                print(f"BLOCKED: {exc}\nStopping -- not attempting to bypass.")
                sys.exit(2)
            if status != 200:
                print(f"[{i}/{len(todo)}] FAILED {status} {row['url']}")
                continue
            rec, text = parse(html, final or row["url"])
            rec["discovered_via"] = row["source_of_discovery"]
            with open(text_path(rec["node_id"]), "w", encoding="utf-8") as fh:
                fh.write(f"{rec['title']}\n{rec['date_published']} | {rec['author']}\n"
                         f"{rec['canonical_url']}\n\n{text}\n")
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{i}/{len(todo)}] {rec['date_published'][:10]} {rec['title'][:70]}")


if __name__ == "__main__":
    main(sys.argv)
