# Daily Star 1971 Liberation War index: final report

Deliverable: `liberation_war_articles.xlsx`. Audit trail: `classification_log.csv`
(label, content type and reason for every page read, including excluded ones),
`candidates.csv`, `discovery/` (pruned sitemap URLs, search hits, author listings,
coverage-push picks) and `discovery/decisions/` (every manual labelling batch).

## What is listed, and where

Only articles whose **central theme** is the subject of the tab are listed. News
reports (observances, speeches, court and tribunal reports, obituaries, release
announcements) are never listed, whatever the topic.

| Tab | Rows | What it holds |
|---|---|---|
| Liberation War Articles | 745 | Articles about 1971 itself: 112 from Slow Reads / In Focus and 633 from every other section (the Section column says which) |
| Daily Reports | 693 | Day-by-day 1971 chronicle entries (see below) |
| Slow Reads - Language Movement | 15 | Slow Reads pieces about the 1948-52 Language Movement |
| Other - Language Movement | 110 | The same, from every other section |
| Pre-1971 | 35 | The run-up before 1971: Six Points, the Agartala case, 1969, the 1970 election, the Bhola cyclone |
| Present Day Discussions | 194 | Present-day debates where 1971 is the subject |
| Needs review | 93 | Items flagged for a human look, and the duplicates left off (see below) |
| Summary | | Counts, years, date ranges, coverage |

**The two tabs you asked for.** The Liberation War material is now on two tabs, the
first two in the workbook:
- **Liberation War Articles** merges the former "Slow Reads - Liberation War" and
  "Other - Liberation War" tabs.
- **Daily Reports** holds the chronicle entries.

The Language Movement, Pre-1971 and Present Day Discussions tabs you asked for
earlier follow them. Their scope is unchanged, and none of their rows also appear on
the first two tabs.

- **Dates and authors.** Every listed row has a publication date and an author taken
  from the page. Nothing was guessed, so no cells needed highlighting.
- **Layout.** Each tab is sorted oldest first. Dates are real dates shown as
  DD-MMM-YYYY, and links are clickable.
- **Recall check: 7/7.** All seven known Slow Reads articles are listed.

### Rules applied (from your answers)
- **Central theme only.** 214 pieces where 1971 matters but is not the subject are
  labelled Borderline in the log and not listed. These include biographies,
  tributes, Victory Day editorials, post-war 1972 pieces and present-day politics
  citing 1971.
- **No news reports.** 1,487 news reports are excluded; they are listed in the log
  with their label.
- **Other exclusions.** Reader letters, scanned clippings, photo and video items, and
  stubs are excluded.
  - Three letters from the site's Letters to the Editor page had slipped onto the
    list, two of them labelled as editorials. They have been removed.
  - "Zia's declaration" stays: it is a letter followed by a longer reply from Syed
    Badrul Ahsan that is itself a piece of 1971 history.
- **March 1971 counts as 1971.** The 7 March speech and the March 1971
  non-cooperation movement are on the Liberation War tabs, not Pre-1971.
- **Present Day Discussions** is only for present-day pieces where 1971 is central.
  Topics include:
  - genocide recognition, and Pakistan's denial and apology
  - the war crimes trials, and Jamaat's 1971 role
  - recognition of birangonas and freedom fighters
  - neglected killing fields and memorials
  - textbooks and the politics of 1971 history
- **Arts pieces left out.** Films, novels, plays, poems, music and games about 1971
  or 1952, and reviews of them, are excluded. Reviews of non-fiction history books
  stay. Pieces about the role of music, concerts and photographs *in* 1971 stay.
- **Language Movement.** Only the 1948-52 movement, its people and its history are
  included. International Mother Language Day pieces count only when they are about
  1952.
- **What counts as Slow Reads.** "Slow Reads" includes:
  - In Focus
  - the older `/in-focus/` and `/views/in-focus/` paths
  - `/ds/slow-reads-special/` (the site files these under its Slow Reads category)

### Writers behind "The Daily Star" bylines
The site gives 504 listed rows only the byline "The Daily Star". The page itself often
names the writer, so each of these was read:

| Outcome | Rows | Author column |
|---|---|---|
| Writer found | 65 | The real name |
| Unsigned editorial | 34 | Left as "The Daily Star" |
| No writer named on the page | 405 | Left as "The Daily Star" |

- **Where the names came from.**
  - the standfirst under the headline ("...argues Kajalie Shehreen Islam")
  - a byline at the top of the text
  - a bio line at the end ("Mofidul Hoque is Trustee, Liberation War Museum")
  - in 6 cases, the writer's e-mail address
- **The Author note column** says where each name was found, or why there is none.
  Interviewers, translators and compilers are marked as such, e.g. "Naznin Tithi
  (interviewer)".
- **The 405 rows with no writer.** 376 are Daily Reports chronicle entries. The rest
  are mostly fact-sheet profiles, district reports and desk-written features.
- **E-mail addresses.**
  - The site hides addresses with Cloudflare's e-mail obfuscation, which every
    browser decodes when it shows the page.
  - They were decoded from the pages already downloaded, with no new requests, only
    to read the name.
  - No address is copied into the workbook.
- **A job title is not a name.** Some footers give only a role ("The writer is
  Executive Editor, The Daily Star"). The Author cell then stays "The Daily Star",
  and the note gives the likely writer.
- **Effect on duplicates.** With the real names, the duplicate check matched 7 more
  reprints to their originals. Most are 2014 reprints of pieces first published
  between 2008 and 2013.
- **Records.** Every decision is in `discovery/author_fixes.csv`, and the method is
  in `dstar/bylines.py`.
- **Your own file.** The same decisions were applied to your combined file
  (`A_Liberation_war_articles_combining_slow_reads_and_other_sections_in_one_tab.xlsx`).
  Only its Author cells changed, and an Author note column was added.

### Daily reports
These rows read like dispatches but are **not** real-time reports. They were written
decades later, as dated summaries of what happened on each day of 1971, compiled from
the period's newspapers and records.

| Series | Published | Rows |
|---|---|---|
| "War Calendar: chronology of events taking place during 1971" (online archive, one entry per date) | Nov-Dec 2014 | 356 |
| "On this day in 1971", March 1971 entries | Mar 2014 | 11 |
| Syed Badrul Ahsan, "Yahya flies into Bangalee militancy" | Mar 2013 | 1 |
| Declassified US documents on March 1971, day by day | Mar 2017 | 3 |
| Timeline "From 1970 elections to March 7" | Oct 2017 | 1 |
| "MARCH 2, 1971: ..." series | Mar 2018 | 28 |
| The same series, 2019 edition (entries not reprinted from 2018) | Mar 2019 | 10 |
| "On this day in 1971" front-page box (entries not reprinted from 2014) | Dec 2019 | 5 |
| Shamsuddoza Sajen, "Road to Freedom: This Day in Bangladesh Liberation War History" | Mar-Dec 2021 | 273 |
| Shamsuddoza Sajen, "Indomitable March" (entries not reprinted from 2021) | Mar 2024 | 5 |
| **Total** | | **693** |

- **Which date is shown.** The Date column is when The Daily Star published each
  entry, not the 1971 date it describes; that date is in the title or the first line.
- **What was left out:**
  - entries under 50 words, as stubs
  - 24 December 2019 entries, which reprint the 2014 entries
  - 22 "Indomitable March" entries, which reprint the 2021 entries
  - 3 March 2019 entries, which reprint the 2018 entries

  These are on Needs review, each with the copy that was kept.
- **What stays on Liberation War Articles.** Longer single articles that happen to
  cover March 1971 day by day (e.g. "Counting the days to independence") stay there,
  as does "Notes to My Successor: The Forgotten Women of the 1971 War".

## Coverage

| Section | Candidates read | Candidates found |
|---|---|---|
| Slow Reads / In Focus | 1,540 | 1,546 |
| Other sections | 4,034 | 4,037 |

**Slow Reads / In Focus** was read in full. The 6 unread pages redirect to campaign
microsites outside thedailystar.net (see below).

**Other sections.** The site is far too large to read every page, so candidates came
from these routes:
- sitemap URLs containing a 1971 or Language Movement term
- themed supplements (Victory Day, Independence Day, Martyred Intellectuals Day,
  Ekushey)
- web searches restricted to thedailystar.net
- writers' author pages
- links inside articles already read

**Final completeness push.** In this round, 1,203 more pages were read:

| Route | Pages read | What it found |
|---|---|---|
| Second pass over the sitemaps | 643 | The 2014 root-level archive, URLs the first filter had pruned, and slugless "-1971" URLs that a bug had skipped |
| Web searches | 332 | Older pieces with non-descriptive URLs |
| Author pages of 13 writers of 1971 series and features | 212 | Mainly the 2021 "Road to Freedom" and 2024 "Indomitable March" entries, whose URLs carry no 1971 term |
| Links inside articles already read | 16 | |

Compared with the previous version of the workbook, this added:

| Tab | Rows added |
|---|---|
| Liberation War Articles | +290 |
| Daily Reports | +275 |
| Language Movement | +49 |
| Pre-1971 | +24 |
| Present Day Discussions | +85 |

### What may still be missing
- **The old archive host is not reachable from here.** `archive.thedailystar.net`
  is blocked by this environment's network policy, so nothing on that host was
  read.
  - To include it, allow the host in the environment's settings: Edit → Network
    access → Custom → add `archive.thedailystar.net`. Then the crawl can be run
    there with the same rules.
- **Old pages with uninformative URLs.**
  - About 269,000 `news-detail-NNNN` pages (2007-2013) and about 133,000
    date-coded pages (2003-2006) give no clue to their subject in the URL.
  - They were reached only through searches and links, so some relevant ones from
    those years will be missing. The By-year table in the Summary shows thinner
    counts before 2013.
- **Tag pages were not used.** robots.txt disallows `/tags/`.
- **Deliberately not listed:**
  - Sajen's 1972 chronicle ("Bangabandhu's nation-building challenges", 2020-21;
    about 320 entries, not fetched), because it is post-war
  - Bangabandhu's homecoming of January 1972, which is Borderline

## Discovery routes (rows can have several)

| Tab | Author pages | Links in articles | Listings | Search | Sitemaps | Supplements |
|---|---|---|---|---|---|---|
| Liberation War Articles | 6 | 4 | 85 | 283 | 521 | 170 |
| Daily Reports | 187 | - | - | 16 | 496 | - |
| Slow Reads - Language Movement | - | - | 13 | 4 | 15 | - |
| Other - Language Movement | - | - | - | 41 | 68 | 1 |
| Pre-1971 | - | - | 4 | 21 | 18 | 1 |
| Present Day Discussions | 1 | 2 | 4 | 34 | 161 | 12 |

## Crawl conduct and failures

- **How the crawl ran.**
  - One request at a time, at least 5 seconds apart (2.5 s before the first 403).
  - robots.txt was respected, and every request used a descriptive User-Agent.
  - 6,263 requests were logged between 5 and 6 October 2026:

    | Outcome | Requests |
    |---|---|
    | OK | 6,206 |
    | Redirect to another site | 50 |
    | HTTP 404 | 6 |
    | HTTP 403 | 1 |
- **HTTP 403 (once).** The page was a video item:
  `/news/bangladesh/special-read/news/watch-pakistan-lying-about-1971-genocide-185098`.
  - The crawl stopped as instructed. With your go-ahead it resumed more slowly, and
    that page was never requested again.
  - No other 403s or challenges occurred.
- **Three dropped connections at this environment's proxy** (not the site) stopped
  the crawl briefly. Each time, the proxy reported no faults and the same page then
  loaded normally.
- **Redirects to campaign microsites that cannot be reached from here:**
  - *Operation Searchlight: The night hell opened over Dhaka*, which is relevant. It
    is listed on Needs review with date and author blank.
  - Five unrelated Slow Reads pages.
- **HTTP 404:**
  - Three listing URLs and one newspaper-date page; their articles were reached by
    other routes.
  - Two article URLs from search results (`news-detail-55573`,
    `wide-angle/memory-and-justice-3100`), whose content could not be checked.

## Things to check (Needs review tab)

1. **77 duplicates left off.** Each is shown with the URL of the copy that was kept.
   - 19 are exact republications: same title, author and text.
   - 58 are republications under a new title: same author, and most of the later
     piece's text repeats the earlier one. Most are the reprinted chronicle entries
     above. The rest are profiles and essays rerun on later anniversaries.
   - The Slow Reads copy is kept where there is one; otherwise the original is
     kept.
2. **15 rows with a relevance note**, all still listed:
   - collaborator profiles published alongside tribunal coverage
   - district liberation-day anniversary features that are mostly history
   - a wire piece on Kissinger, and an online report on a book about Nixon
   - an interview with Madhusudan Dey ("Modhu Da"), recorded in February 1971 about
     1952
   - three possible republication pairs whose texts differ too much to merge
     automatically. Both copies of each pair are listed:
     - "Anti-Bangladesh before & after '71" (2012) / "Anti-liberation all along"
       (2013)
     - "My three martyred teachers" (2022) / "A Tribute to My Martyr Teachers"
       (2023)
     - "The proclamation that gave Bangladesh its statehood" (2026), against its
       2025 version
3. **One relevant page could not be read** (the Operation Searchlight microsite
   above).
4. **Dates are the site's creation timestamps.** For older pieces republished later
   (e.g. reprints of 1971 articles), the date is the republication date.
