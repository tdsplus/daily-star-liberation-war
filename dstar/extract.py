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

from bs4 import BeautifulSoup

from .fetch import BlockedError, Fetcher
from .store import ROOT, Candidates, canonical, is_article, node_id

RECORDS = os.path.join(ROOT, "cache", "articles.jsonl")
TEXT_DIR = os.path.join(ROOT, "cache", "text")
ARTICLE_TYPES = {"NewsArticle", "Article", "ReportageNewsArticle", "OpinionNewsArticle",
                 "AnalysisNewsArticle", "BlogPosting"}


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
    """Return (container, text). Tries known Daily Star selectors, then the
    element holding the most paragraph text."""
    for sel in ("article .article-body", ".article-body", "[itemprop=articleBody]",
                ".section-content .clearfix", ".pb-20.clearfix", "article"):
        node = soup.select_one(sel)
        if node and len(node.get_text(" ", strip=True)) > 400:
            break
    else:
        best, node = 0, None
        for div in soup.find_all(["div", "section", "article"]):
            n = sum(len(p.get_text(strip=True)) for p in div.find_all("p", recursive=False))
            if n > best:
                best, node = n, div
    if node is None:
        return None, ""
    for junk in node.select("script, style, aside, figure figcaption ~ *, .related, .tags, "
                            "nav, form, iframe, .social, .share"):
        junk.decompose()
    paras = [p.get_text(" ", strip=True) for p in node.find_all(["p", "h2", "h3", "blockquote"])]
    text = "\n\n".join(p for p in paras if p)
    return node, text or node.get_text("\n", strip=True)


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
        flags.append("no-date")

    authors = _names(ld.get("author"))
    author_src = "jsonld" if authors else ""
    if not authors:
        m = _meta(soup, "author", "article:author", "dable:author")
        if m and not m.startswith("http"):
            authors, author_src = [m], "meta"
    if not authors:
        for sel in (".author-name", ".byline", "[rel=author]", ".author a", ".author"):
            node = soup.select_one(sel)
            if node and node.get_text(strip=True):
                authors, author_src = [node.get_text(" ", strip=True)], "html:" + sel
                break
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
        "breadcrumbs": crumbs,
        "tags": list(dict.fromkeys(tags)),
        "description": ld.get("description") or _meta(soup, "description", "og:description"),
        "body_links": list(dict.fromkeys(body_links)),
        "text_chars": len(text),
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
            with open(os.path.join(TEXT_DIR, rec["node_id"] + ".txt"), "w", encoding="utf-8") as fh:
                fh.write(f"{rec['title']}\n{rec['date_published']} | {rec['author']}\n"
                         f"{rec['canonical_url']}\n\n{text}\n")
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            out.flush()
            print(f"[{i}/{len(todo)}] {rec['date_published'][:10]} {rec['title'][:70]}")


if __name__ == "__main__":
    main(sys.argv)
