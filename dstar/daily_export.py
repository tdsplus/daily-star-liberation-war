"""Export the Daily Reports tab on its own, in order of the day each entry describes,
from 1 January to 16 December 1971.

The main workbook sorts every tab by publication date. For the chronicle
series that reads oddly: the 2014 War Calendar was posted in bulk from
31 December back to 1 January, so its January 1971 entries come after its
December ones. This export adds the date covered and the series, and sorts
on the date covered.

Usage:  python -m dstar.daily_export
"""
import os
import re
from datetime import date

from openpyxl import Workbook
from openpyxl.styles import Font

from .build_xlsx import DATE_FMT, TABS, rows, style, tab_key
from .classify import load_labels
from .extract import text_path
from .store import ROOT

OUT = os.path.join(ROOT, "daily_reports.xlsx")
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august",
          "september", "october", "november", "december"]
DAY = re.compile(r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})\b", re.I)
DAY_FIRST = re.compile(r"\b(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+1971\b", re.I)


def series(it):
    p = it["date"]
    if p.year == 2014 and p.month >= 11:
        return "War Calendar (2014)"
    return {
        (2013, 3): "On this day in 1971 (Syed Badrul Ahsan, 2013)",
        (2014, 3): "On this day in 1971 (March 2014)",
        (2017, 3): "Declassified US documents (March 2017)",
        (2017, 10): "Timeline (2017)",
        (2018, 3): "MARCH ..., 1971 series (2018)",
        (2019, 3): "MARCH ..., 1971 series (2019)",
        (2019, 12): "On this day in 1971 (December 2019)",
        (2024, 3): "Indomitable March (2024)",
    }.get((p.year, p.month), "Road to Freedom (2021)" if p.year == 2021 else "Other")


# Series that publish each entry on the anniversary of the day it describes.
SAME_DAY = ("On this day in 1971 (March 2014)", "MARCH ..., 1971 series (2018)",
            "MARCH ..., 1971 series (2019)", "On this day in 1971 (December 2019)",
            "Road to Freedom (2021)", "Indomitable March (2024)")


def covered(it, reason):
    """First day the entry describes: from the title, the opening line, our label, a
    longer stretch of text, and finally the anniversary rule for same-day series."""
    if it["series"] == "Timeline (2017)":
        return date(1970, 12, 7)    # "From 1970 elections to March 7" opens on 7 December 1970
    with open(text_path(it["nid"]), encoding="utf-8") as fh:
        body = fh.read().split("\n\n", 1)[-1]
    texts = [it["title"], reason, body[:150]]   # our label names the day when the title does not
    if it["series"] not in SAME_DAY:   # deeper text may mention other dates; the anniversary is safer
        texts.append(body[:800])
    for text in texts:
        m = DAY_FIRST.search(text)
        if m:
            return date(1971, MONTHS.index(m.group(2).lower()) + 1, int(m.group(1)))
        m = DAY.search(text)
        if m:
            return date(1971, MONTHS.index(m.group(1).lower()) + 1, int(m.group(2)))
    if it["series"] in SAME_DAY:
        return date(1971, it["date"].month, it["date"].day)
    return None


def main():
    labels = load_labels()
    items, _ = rows()
    daily = [i for i in items if TABS[tab_key(i)] == "Daily Reports"]
    for it in daily:
        it["series"] = series(it)
        it["covered"] = covered(it, labels[it["nid"]]["reason"])
    daily.sort(key=lambda i: (i["covered"] is None, i["covered"] or date.max, i["date"]))
    # Chronological from 1 January to Victory Day; entries outside that span are reported, not exported.
    left_out = [i for i in daily if not (i["covered"] and date(1971, 1, 1) <= i["covered"] <= date(1971, 12, 16))]
    daily = [i for i in daily if i not in left_out]
    wb = Workbook()
    ws = wb.active
    ws.title = "Daily Reports"
    ws.append(["Serial Number", "Date covered", "Series", "Date published", "Author", "Title",
               "Link", "Author note"])
    for n, it in enumerate(daily, 1):
        ws.append([n, it["covered"], it["series"], it["date"], it["author"], it["title"], it["url"],
                   it["author_note"] or None])
        r = ws.max_row
        for c in (2, 4):
            ws.cell(r, c).number_format = DATE_FMT
        ws.cell(r, 7).hyperlink = it["url"]
        ws.cell(r, 7).style = "Hyperlink"
    style(ws, [9, 14, 30, 14, 22, 55, 60, 40], ["F", "H"])
    ws["A1"].font = Font(bold=True)
    wb.save(OUT)
    missing = [(str(i["covered"]), i["title"]) for i in left_out]
    print(f"wrote {OUT}: {len(daily)} entries, "
          f"{min(i['covered'] for i in daily if i['covered'])} to {max(i['covered'] for i in daily if i['covered'])}; "
          f"left out ({len(missing)}): {missing}")


if __name__ == "__main__":
    main()
