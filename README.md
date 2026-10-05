# Daily Star: 1971 Liberation War article index

Builds `liberation_war_articles.xlsx`, a list of thedailystar.net articles on the
1971 Liberation War, with Slow Reads / In Focus as the priority section.

## Crawler etiquette
`dstar/fetch.py` respects robots.txt and sends one request at a time, at least
2.5 s apart. It uses a descriptive User-Agent and retries with backoff. It
**stops** on HTTP 403, a captcha or a Cloudflare challenge, and never tries to
bypass them. Every response is cached and logged in `cache/fetch_log.jsonl`, so
an interrupted run resumes without repeating requests.

## Run order
```
pip install -r requirements.txt
python -m dstar.discover listings          # (a) Slow Reads + In Focus pagination
python -m dstar.extract                    # fetch + extract metadata/text
python -m dstar.discover tags              # (b) tag pages found on fetched articles
python -m dstar.discover sitemaps          # (c) sitemap index + news sitemaps
python -m dstar.discover search hits.csv   # (d) import search hits (url,keyword)
python -m dstar.extract
python -m dstar.classify pending 10        # read articles, then label them:
python -m dstar.classify set <node_id> Core feature "reason" [--unsure "note"]
python -m dstar.discover snowball          # (e) links inside relevant articles
python -m dstar.extract                    # ...repeat extract/classify/snowball
python -m dstar.build_xlsx
python -m dstar.recall                     # exits non-zero if a known article is missing
```

## Outputs
* `candidates.csv`: url, source_of_discovery, first_seen (de-duplicated by the article's numeric id)
* `cache/articles.jsonl`, `cache/text/<id>.txt`: extracted metadata and full text
* `classification_log.csv`: label, content type and reason for **every** candidate, including Irrelevant ones. News reports (event/commemoration coverage, tribunal hearings) are always Irrelevant: only articles centred on 1971 are kept
* `liberation_war_articles.xlsx`: sheets Articles, Needs review, Other sections, Summary
