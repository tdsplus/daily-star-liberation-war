# Daily Star 1971 Liberation War index: final report

Deliverable: `liberation_war_articles.xlsx`. Audit trail: `classification_log.csv`
(label, content type and reason for every page read, including excluded ones),
`candidates.csv`, `discovery/pruned_candidates.csv`, `discovery/decisions/`.

## What is listed, and where

Only articles whose **central theme** is the subject of the tab are listed. News
reports (observances, speeches, court and tribunal reports, obituaries, release
announcements) are never listed, whatever the topic.

| Tab | Rows | What it holds |
|---|---|---|
| Slow Reads - Liberation War | 112 | Slow Reads / In Focus pieces about 1971 itself |
| Other - Liberation War | 351 | The same, from every other section |
| Daily reports | 418 | Day-by-day 1971 chronicle entries (see below) |
| Slow Reads - Language Movement | 15 | Slow Reads pieces about the 1948-52 Language Movement |
| Other - Language Movement | 61 | The same, from every other section |
| Pre-1971 | 11 | The run-up before 1971: Six Points, 1969, 1970 election, Bhola cyclone |
| Present Day Discussions | 111 | Present-day debates where 1971 is the subject |
| Needs review | 21 | Items flagged for a human look (see below) |
| Summary | | Counts, years, date ranges, coverage |

- Every listed row has a publication date and an author taken from the page. Nothing
  was guessed, so no cells needed highlighting.
- Each tab is sorted oldest first; dates are real dates shown as DD-MMM-YYYY; links
  are clickable.
- Recall check: **7/7** known Slow Reads articles are on the Slow Reads tab.

### Rules applied (from your answers)
- **Central theme only.** 147 pieces where 1971 matters but is not the subject
  (biographies, tributes, Victory Day editorials, present-day politics citing 1971)
  are labelled Borderline in the log and not listed.
- **March 1971 counts as 1971.** The 7 March speech and the March 1971
  non-cooperation movement are on the Liberation War tabs, not Pre-1971.
- **Present Day Discussions** covers genocide recognition, Pakistan's denial and
  apology, the war crimes trials, Jamaat's 1971 role, recognition of birangonas and
  freedom fighters, neglected killing fields and memorials, and the politics of 1971
  history.
- **Arts pieces left out:** films, novels, plays, poems, music and games about 1971 or
  1952, and reviews of them. Reviews of non-fiction history books stay.
- **Language Movement:** only the 1948-52 movement, its people and its history.
  International Mother Language Day pieces only when they are about 1952.
- "Slow Reads" includes In Focus, the older `/in-focus/` and `/views/in-focus/` paths,
  and `/ds/slow-reads-special/` (the site files these under its Slow Reads category).

### Daily reports
These 418 rows read like dispatches but are **not** real-time reports. They were
written decades later, as dated summaries of what happened on each day of 1971,
compiled from the period's newspapers and records:

- the 2014 online archive ("War Calendar: chronology of events taking place during
  1971"), one entry per date, posted in bulk in November-December 2014 (346 rows);
- "On this day in 1971", the front-page box of December 2019 (29);
- the "MARCH 6, 1971: ..." series of March 2018 and 2019 (34);
- Shamsuddoza Sajen's "Road to Freedom: This Day in Bangladesh Liberation War
  History" (2021) (9).

The date column shows when The Daily Star published each entry, not the 1971 date it
describes (that is in the title). Entries under 50 words were left out as stubs.
Longer single articles that happen to cover March 1971 day by day (e.g. "Counting the
days to independence") stay on the Liberation War tabs.

## Coverage

| Section | Candidates read | Candidates found |
|---|---|---|
| Slow Reads / In Focus | 1,536 | 1,545 |
| Other sections | 2,838 | 2,840 |

Slow Reads was read in full. Outside Slow Reads the site is far too large to read
every page, so sitemap URLs were fetched only when the URL contained a 1971 or
Language Movement term (the 8,500 URLs filtered out are in
`discovery/pruned_candidates.csv`). A relevant article with a non-descriptive URL
outside Slow Reads could therefore be missed; targeted web searches and themed
supplement listings were used to catch these.

## Discovery routes (rows can have several)

| Tab | Sitemaps | Listings | Search | Supplements |
|---|---|---|---|---|
| Slow Reads - Liberation War | 90 | 85 | 51 | 30 |
| Other - Liberation War | 715 | - | 89 | 140 |
| Slow Reads - Language Movement | 15 | 13 | 4 | - |
| Other - Language Movement | 60 | - | - | 1 |
| Pre-1971 | 9 | 4 | 6 | 1 |
| Present Day Discussions | 103 | 4 | 10 | 12 |

Tag pages were not used: robots.txt disallows `/tags/`.

## Crawl conduct and failures

- One request at a time, at least 5 seconds apart (2.5 s before the first 403),
  robots.txt respected, descriptive User-Agent.
- **HTTP 403 (once):** `/news/bangladesh/special-read/news/watch-pakistan-lying-about-1971-genocide-185098`
  (a video item). The crawl stopped as instructed; with your go-ahead it resumed more
  slowly and that page was never requested again. No other 403s or challenges occurred.
- **Two dropped connections at this environment's proxy** (not the site) stopped the
  crawl briefly; each time the proxy reported no faults and the same page then loaded
  normally.
- **Off-site redirects** to campaign microsites that cannot be reached from here:
  *Operation Searchlight: The night hell opened over Dhaka* (relevant; listed on
  Needs review with date and author blank) and five unrelated Slow Reads pages.
- **HTTP 404:** three listing URLs; their articles were reached by other routes.

## Things to check (Needs review tab)

1. **Possible republications under new titles**, both copies listed:
   - "The Proclamation of Independence was a beacon" (2025) / "The proclamation that
     gave Bangladesh its statehood" (2026)
   - "Anti-Bangladesh before & after '71" (2012) / "Anti-liberation all along" (2013)
   - "My three martyred teachers" (2022) / "A Tribute to My Martyr Teachers" (2023)
2. **Borderline-format pieces kept:** district liberation-day anniversary features
   that are mostly history, a BSS piece on Kissinger, an online report on a book about
   Nixon.
3. **Eight exact republications** (same title, author and text) are listed once; the
   other copy is on Needs review.
4. **Dates are the site's creation timestamps.** For older pieces republished later
   (e.g. reprints of 1971 articles), the date is the republication date.
