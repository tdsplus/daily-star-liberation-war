# Daily Star 1971 Liberation War index: final report

Deliverable: `liberation_war_articles.xlsx`. Audit trail: `classification_log.csv`
(label, content type and reason for every article read, including Irrelevant ones),
`candidates.csv`, `discovery/pruned_candidates.csv`.

## Totals

| Sheet | Rows | Core | Borderline |
|---|---|---|---|
| Articles (Slow Reads / In Focus) | 157 | 100 | 57 |
| Other sections | 49 | 47 | 2 |
| Needs review | 15 | | |

- Every row has a publication date and an author taken from the page. Nothing was guessed.
- News reports were excluded by your rule: 9 relevant-topic reports, such as
  commemoration coverage and tribunal reports, are logged as Irrelevant with the
  reason "news report".
- 1 duplicate was left off the main sheets: Mascarenhas's "Genocide", published under two
  ids. The Slow Reads / In Focus copy was kept.
- Recall check: **7/7** known articles present.

## Coverage

| Section | Candidates read | Candidates found |
|---|---|---|
| Slow Reads / In Focus | 1,516 | 1,525 |
| Other sections | 55 | 2,549 |

**The "Other sections" sheet is incomplete.** After about 1,500 polite requests,
one at a time and about 2.5 s apart, the site returned HTTP 403 for
`/news/bangladesh/special-read/news/watch-pakistan-lying-about-1971-genocide-185098`.
The crawl stopped as instructed, and by your decision it was not resumed. About 2,490
other-section candidates (pages from sitemaps, supplements and search) were never read.
The existing 49 rows come mostly from targeted search, so treat that sheet as a sample,
not a census.

## Discovery routes

| Route | Articles sheet | Other sections |
|---|---|---|
| Sitemaps | 157 (9 found by no other route) | 32 |
| Slow Reads / In Focus listing pagination | 147 | — |
| Web search | 67 | 49 (16 found by no other route) |
| Themed supplements / packages | 10 | 10 |
| Tag pages | not used: `Disallow: /tags/` in robots.txt | |

## Pages that failed to load

- **HTTP 403** (crawl stopped here): the "[WATCH] Pakistan lying about 1971 genocide" page.
- **Off-site redirects**, to subdomains this environment cannot reach:
  - *Operation Searchlight: The night hell opened over Dhaka*. This is relevant (Core),
    so it is listed on "Needs review" with date and author blank.
  - Five unrelated Slow Reads pages that redirect to campaign microsites:
    climate and gender, the haor crisis, labour, workplace safety, and a censorship
    timeline.
- **HTTP 404:** three listing URLs (`/in-focus`, `/views/in-focus`,
  `/opinion/martyred-intellectuals-day`). Their articles were reached through other routes.

## Things I am unsure about

1. **Possible republications** under new titles. Both copies are listed and flagged
   on "Needs review":
   - "The Proclamation of Independence was a beacon" (2025) and
     "The proclamation that gave Bangladesh its statehood" (2026)
   - "Anti-Bangladesh before & after '71" (2012) and "Anti-liberation all along" (2013)
2. **Borderline judgements** flagged on "Needs review". For example, profiles of
   martyred intellectuals that dwell on their earlier lives, the Tharparkar memorial
   (western front), and Bengalis stranded in Pakistan after 1971.
3. **Dates are the site's own creation timestamps.** For older pieces republished in
   Slow Reads (e.g. Rehman Sobhan's June 1971 *Guardian* article), the date is the
   republication date, not the original.
4. **Sitemap filter for other sections.** Sitemap pages from other sections were
   queued for reading only if the URL contained a 1971 term. A relevant article with
   a non-descriptive URL could be missed there; this does not affect Slow Reads,
   which was read in full. The 8,500 URLs filtered out are in
   `discovery/pruned_candidates.csv`.
