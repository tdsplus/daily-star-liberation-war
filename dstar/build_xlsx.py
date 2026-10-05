"""Build liberation_war_articles.xlsx from extracted records + classification log.

Usage:  python -m dstar.build_xlsx
"""
import os
import re
from collections import Counter
from datetime import date, datetime

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .classify import NEWS, load_labels
from .extract import load_records, text_path
from .store import ROOT, is_priority_section

OUT = os.path.join(ROOT, "liberation_war_articles.xlsx")
DATE_FMT = "DD-MMM-YYYY"
KEEP = ("Core", "Pre-1971", "Present Day", "Language Movement")   # Borderline is logged but not listed
LW, LM, PRE, PD = "Core", "Language Movement", "Pre-1971", "Present Day"
# Excel sheet names: max 31 characters, no "/" allowed.
TABS = {(LW, True): "Slow Reads - Liberation War", (LW, False): "Other - Liberation War",
        (LM, True): "Slow Reads - Language Movement", (LM, False): "Other - Language Movement",
        (PRE, None): "Pre-1971", (PD, None): "Present Day Discussions"}   # None: both sections on one tab


def tab_key(it):
    key = (it["label"], it["priority"])
    return key if key in TABS else (it["label"], None)
# Cells you need to fill in by hand: missing date (amber), missing author (pale yellow).
NEED_DATE = PatternFill("solid", fgColor="FFC000")
NEED_AUTHOR = PatternFill("solid", fgColor="FFF2CC")


def pub_date(raw):
    """Calendar date as published (site local time), or None. Never guessed."""
    if not raw:
        return None
    raw = raw.strip()
    try:
        return datetime.fromisoformat(raw.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", raw)
    if m:
        return date(*map(int, m.groups()))
    for fmt in ("%a %b %d, %Y %I:%M %p", "%a %b %d, %Y", "%d %B %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _words(it):
    try:
        with open(text_path(it["nid"]), encoding="utf-8") as fh:
            body = fh.read().split("\n\n", 1)[-1]
    except OSError:
        return set()
    w = re.findall(r"[a-z]+", body.lower()[:4000])
    return {" ".join(w[i:i + 5]) for i in range(len(w) - 4)}


def same_text(a, b, threshold=0.5):
    """Do two items share most of their opening text (5-word shingles)?"""
    wa, wb = _words(a), _words(b)
    if not wa or not wb:
        return True   # no text to compare: fall back to title + author
    return len(wa & wb) / min(len(wa), len(wb)) >= threshold


def rows():
    recs, labels = load_records(), load_labels()
    out = []
    for nid, lab in labels.items():
        # News reports are out of scope even if mislabelled (defence in depth).
        if lab["label"] not in KEEP or lab.get("content_type") == NEWS:
            continue
        r = recs.get(nid)
        if r is None:
            continue
        d = pub_date(r["date_published"])
        problems = []
        if d is None:
            problems.append("publication date missing/unparseable"
                            + (f" (raw: {r['date_published']!r})" if r["date_published"] else ""))
        if not r["author"]:
            problems.append("author not found in JSON-LD, meta tags or byline")
        if lab.get("unsure_note"):
            problems.append("relevance uncertain: " + lab["unsure_note"])
        out.append({
            "nid": nid, "date": d, "author": r["author"], "title": r["title"],
            "url": r["canonical_url"], "label": lab["label"], "reason": lab["reason"],
            "section": r["section"] or "/".join(r["canonical_url"].split("/")[3:5]),
            "priority": is_priority_section(r["canonical_url"]),
            "problems": problems,
        })
    key = lambda x: (x["date"] is None, x["date"] or date.min, x["title"].lower())
    out = sorted(out, key=key)
    # The site occasionally republishes an article under a new node id. Same
    # normalised title + author AND largely the same text => keep one copy
    # (the Slow Reads one if any) and report the rest. The text check stops
    # series with a fixed title (e.g. "On this day in 1971") being merged.
    seen, kept, dupes = {}, [], []
    for it in out:
        k = (re.sub(r"[^a-z0-9]+", " ", it["title"].lower()).strip(), it["author"].lower())
        keep = next((c for c in seen.get(k, []) if same_text(c, it)), None)
        if keep is not None:
            if it["priority"] and not keep["priority"]:
                # Prefer the Slow Reads / In Focus copy of a republished article.
                kept[kept.index(keep)] = it
                seen[k][seen[k].index(keep)] = it
                keep, it = it, keep
            it["problems"] = [f"likely duplicate of {keep['url']} (same title, author and text)"]
            dupes.append(it)
        else:
            seen.setdefault(k, []).append(it)
            kept.append(it)
    # A swapped-in priority copy may have a later date than the one it replaced.
    return sorted(kept, key=key), dupes


def style(ws, widths, wrap_cols):
    for c in ws[1]:
        c.font = Font(bold=True)
        c.alignment = Alignment(vertical="center", wrap_text=True)
    ws.freeze_panes = "A2"
    ws.auto_filter.ref = ws.dimensions
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    for col in wrap_cols:
        for cell in ws[col][1:]:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def write_article_sheet(ws, items, with_section=False):
    ws.append(["Serial Number", "Date", "Author", "Title", "Link"] + (["Section"] if with_section else []))
    for n, it in enumerate(items, 1):
        ws.append([n, it["date"], it["author"] or None, it["title"], it["url"]]
                  + (["Slow Reads" if it["priority"] else "Other"] if with_section else []))
        r = ws.max_row
        ws.cell(r, 2).number_format = DATE_FMT
        if not it["date"]:
            ws.cell(r, 2).fill = NEED_DATE
        if not it["author"]:
            ws.cell(r, 3).fill = NEED_AUTHOR
        link = ws.cell(r, 5)
        link.hyperlink = it["url"]
        link.style = "Hyperlink"
    style(ws, [9, 14, 26, 60, 70, 12], ["C", "D"])


def main():
    import csv
    from .classify import load_labels
    from .store import Candidates, node_id
    items, dupes = rows()
    groups = {k: [i for i in items if tab_key(i) == k] for k in TABS}
    review = [i for i in items if i["problems"]] + dupes

    # Relevant pages that could not be fetched (e.g. off-site interactive
    # microsites): listed for review with blank date/author, never guessed.
    unfetched = os.path.join(ROOT, "discovery", "unfetchable_relevant.csv")
    if os.path.exists(unfetched):
        with open(unfetched, newline="", encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                review.append({"date": None, "author": "", "title": row["title"], "url": row["url"],
                               "label": row["label"], "priority": True,
                               "problems": ["not extracted: " + row["why"]], "unfetched": True})

    wb = Workbook()
    for n, (key, name) in enumerate(TABS.items()):
        ws = wb.active if n == 0 else wb.create_sheet()
        ws.title = name
        write_article_sheet(ws, groups[key], with_section=key[1] is None)

    ws = wb.create_sheet("Needs review")
    ws.append(["Date", "Author", "Title", "Link", "Tab", "Why it needs review"])
    for it in review:
        tab = TABS.get(tab_key(it), "") if it.get("label") in KEEP else ""
        if it in dupes:
            tab = "(not listed - duplicate)"
        elif it.get("unfetched"):
            tab = "(not listed - could not be fetched)"
        ws.append([it["date"], it["author"] or None, it["title"], it["url"], tab,
                   "; ".join(it["problems"])])
        r = ws.max_row
        if it["date"]:
            ws.cell(r, 1).number_format = DATE_FMT
        ws.cell(r, 4).hyperlink = it["url"]
        ws.cell(r, 4).style = "Hyperlink"
    style(ws, [14, 26, 55, 50, 30, 60], ["C", "F"])

    labels = load_labels()
    ws = wb.create_sheet("Summary")
    ws.append(["Metric", "Value"])
    for key, name in TABS.items():
        ws.append([name, len(groups[key])])
    ws.append(["Needs review (also listed on their tab, except duplicates)", len(review)])
    ws.append(["Likely duplicates left off (see Needs review)", len(dupes)])
    ws.append(["Borderline - 1971 significant but not the central theme (not listed)",
               sum(l["label"] == "Borderline" for l in labels.values())])
    ws.append(["News reports excluded (listed in classification_log.csv)",
               sum(l.get("content_type") == NEWS for l in labels.values())])
    ws.append(["Rows needing a date added (amber Date cell)", sum(i["date"] is None for i in items)])
    ws.append(["Rows needing an author added (yellow Author cell)", sum(not i["author"] for i in items)])
    ws.append([])
    ws.append(["By year"] + list(TABS.values()))
    years = {k: Counter(i["date"].year if i["date"] else "Undated" for i in g) for k, g in groups.items()}
    allyears = set().union(*[set(c) for c in years.values()])
    for y in sorted(allyears, key=lambda y: (isinstance(y, str), y)):
        ws.append([y] + [years[k].get(y, 0) for k in TABS])
    ws.append([])
    for key, name in TABS.items():
        dated = [i["date"] for i in groups[key] if i["date"]]
        ws.append([f"Date range - {name}",
                   f"{min(dated):%d-%b-%Y} to {max(dated):%d-%b-%Y}" if dated else "n/a"])
    # Coverage: how much of each section's candidate list was actually read.
    cands = Candidates()
    recs = load_records()
    done = {r["node_id"] for r in recs.values()} | {node_id(r["fetched_url"]) for r in recs.values()}
    pri = [k for k, r in cands.rows.items() if is_priority_section(r["url"])]
    oth = [k for k, r in cands.rows.items() if not is_priority_section(r["url"])]
    ws.append([])
    ws.append(["Coverage", "Candidates read", "Candidates found"])
    ws.append(["Slow Reads / In Focus", sum(k in done for k in pri), len(pri)])
    ws.append(["Other sections", sum(k in done for k in oth), len(oth)])
    unread = len(pri) + len(oth) - sum(k in done for k in pri) - sum(k in done for k in oth)
    if unread:
        ws.append(["Note", f"{unread} candidate pages could not be fetched (HTTP 403/404 or redirects "
                           "to other sites); they are listed in REPORT.md."])
    for row in ws.iter_rows():
        if row[0].value in ("Metric", "By year", "Coverage"):
            for c in row:
                c.font = Font(bold=True)
    ws.column_dimensions["A"].width = 62
    for col in "BCDE":
        ws.column_dimensions[col].width = 18
    ws.freeze_panes = "A2"

    wb.save(OUT)
    print(f"wrote {OUT}: " + ", ".join(f"{n}: {len(groups[k])}" for k, n in TABS.items())
          + f", needs review: {len(review)}")


if __name__ == "__main__":
    main()
