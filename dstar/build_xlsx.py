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

from .classify import load_labels
from .extract import load_records
from .store import ROOT, is_priority_section

OUT = os.path.join(ROOT, "liberation_war_articles.xlsx")
DATE_FMT = "DD-MMM-YYYY"
KEEP = ("Core", "Borderline")
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


def rows():
    recs, labels = load_records(), load_labels()
    out = []
    for nid, lab in labels.items():
        if lab["label"] not in KEEP:
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
            "date": d, "author": r["author"], "title": r["title"],
            "url": r["canonical_url"], "label": lab["label"], "reason": lab["reason"],
            "section": r["section"] or "/".join(r["canonical_url"].split("/")[3:5]),
            "priority": is_priority_section(r["canonical_url"]),
            "problems": problems,
        })
    key = lambda x: (x["date"] is None, x["date"] or date.min, x["title"].lower())
    return sorted(out, key=key)


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


def write_article_sheet(ws, items, extra=()):
    ws.append(["Serial Number", "Date", "Author", "Title", "Link", "Relevance", *extra])
    for n, it in enumerate(items, 1):
        ws.append([n, it["date"], it["author"] or None, it["title"], it["url"], it["label"],
                   *[it[e.lower()] for e in extra]])
        r = ws.max_row
        ws.cell(r, 2).number_format = DATE_FMT
        if not it["date"]:
            ws.cell(r, 2).fill = NEED_DATE
        if not it["author"]:
            ws.cell(r, 3).fill = NEED_AUTHOR
        link = ws.cell(r, 5)
        link.hyperlink = it["url"]
        link.style = "Hyperlink"
    style(ws, [9, 14, 26, 60, 55, 12, *[22] * len(extra)], ["C", "D"])


def main():
    items = rows()
    main_items = [i for i in items if i["priority"]]
    other_items = [i for i in items if not i["priority"]]
    review = [i for i in items if i["problems"]]

    wb = Workbook()
    ws = wb.active
    ws.title = "Articles"
    write_article_sheet(ws, main_items)

    ws = wb.create_sheet("Needs review")
    ws.append(["Date", "Author", "Title", "Link", "Relevance", "Sheet", "Why it needs review"])
    for it in review:
        ws.append([it["date"], it["author"] or None, it["title"], it["url"], it["label"],
                   "Articles" if it["priority"] else "Other sections", "; ".join(it["problems"])])
        r = ws.max_row
        if it["date"]:
            ws.cell(r, 1).number_format = DATE_FMT
        ws.cell(r, 4).hyperlink = it["url"]
        ws.cell(r, 4).style = "Hyperlink"
    style(ws, [14, 26, 55, 50, 12, 16, 60], ["C", "G"])

    ws = wb.create_sheet("Other sections")
    write_article_sheet(ws, other_items, extra=("Section",))

    ws = wb.create_sheet("Summary")
    ws.append(["Metric", "Value"])
    ws.append(["Articles (Slow Reads / In Focus)", len(main_items)])
    ws.append(["Other sections", len(other_items)])
    ws.append(["Needs review (also listed on their main sheet)", len(review)])
    ws.append(["Rows needing a date added (amber Date cell)",
               sum(i["date"] is None for i in items)])
    ws.append(["Rows needing an author added (yellow Author cell)",
               sum(not i["author"] for i in items)])
    ws.append([])
    ws.append(["By label", "Articles", "Other sections"])
    for lab in KEEP:
        ws.append([lab, sum(i["label"] == lab for i in main_items),
                   sum(i["label"] == lab for i in other_items)])
    ws.append([])
    ws.append(["By year", "Articles", "Other sections"])
    ya = Counter(i["date"].year if i["date"] else "Undated" for i in main_items)
    yo = Counter(i["date"].year if i["date"] else "Undated" for i in other_items)
    for y in sorted(set(ya) | set(yo), key=lambda y: (isinstance(y, str), y)):
        ws.append([y, ya.get(y, 0), yo.get(y, 0)])
    ws.append([])
    for name, group in (("Articles", main_items), ("Other sections", other_items)):
        dated = [i["date"] for i in group if i["date"]]
        ws.append([f"Date range – {name}",
                   f"{min(dated):%d-%b-%Y} to {max(dated):%d-%b-%Y}" if dated else "n/a"])
    for row in ws.iter_rows():
        if row[0].value in ("Metric", "By label", "By year"):
            for c in row:
                c.font = Font(bold=True)
    ws.column_dimensions["A"].width = 48
    ws.column_dimensions["B"].width = 28
    ws.column_dimensions["C"].width = 16
    ws.freeze_panes = "A2"

    wb.save(OUT)
    print(f"wrote {OUT}: {len(main_items)} articles, {len(other_items)} other, "
          f"{len(review)} needs-review")


if __name__ == "__main__":
    main()
