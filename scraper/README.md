# Week 5 A9 Polite Scraper

## Target Classification

- Site: Books to Scrape, `https://books.toscrape.com/`
- Parent sandbox: `https://toscrape.com/`, a site made for scraping practice.
- Scope: only the first 3 catalogue pages from Books to Scrape.
- Expected collection size: 60 book detail pages discovered from those catalogue pages.
- Collected data: title, product URL, raw price text, normalized GBP price, availability, rating, description, source catalogue page, and fetch timestamp.
- Robots check: `https://books.toscrape.com/robots.txt` returned HTTP 404 during inspection, so no robots directives were published there.

I will not reuse this code on another site without checking its rules and terms first.

## Install

From this `scraper` folder:

```powershell
..\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

## Run Command

```powershell
..\.venv\Scripts\python.exe -m src.main
```

To prove failure handling with one made-up book URL:

```powershell
..\.venv\Scripts\python.exe -m src.main --include-broken-url
```

The scraper runs from cached HTML after the first fetch, so repeated runs finish quickly and print `CACHE HIT`.

## Schema

`output/books.json` contains validated records with:

- `title`
- `product_url`
- `price_text`
- `price_gbp`
- `availability_text`
- `rating_text`
- `description`
- `source_page`
- `fetched_at`

Invalid records are written to `output/errors.json`.

## Politeness Rules

- Uses an honest `User-Agent`: `FlyRankInternship-A9/1.0 (+https://github.com/ahmad/task-api)`.
- Uses a 10 second request timeout.
- Checks HTTP status before caching.
- Waits at least 0.5 seconds between real network requests.
- Does not wait for cache hits.
- Retries timeout and 5xx failures once.
- Does not retry 403 or 404 pages.
- Scrapes only the first 3 catalogue pages and their 60 discovered book detail pages.
- Does not commit cache files; `cache/` is ignored.

## Browser Note

A browser is not needed to run or grade this assignment. The scraper fetches HTML directly with `requests`, parses it with BeautifulSoup, and stores JSON output in `output/`.

## Run Report Evidence

The saved `output/run-report.json` from the failure-handling proof run:

```json
{
  "started_at": "2026-08-21T20:04:49.861024+00:00",
  "finished_at": "2026-08-21T20:04:54.976943+00:00",
  "duration_seconds": 5.12,
  "catalogue_pages": 3,
  "discovered_urls": 60,
  "unique_urls": 60,
  "detail_pages_attempted": 61,
  "pages_fetched": 0,
  "cache_hits": 63,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 1,
  "failures": [
    {
      "url": "https://books.toscrape.com/catalogue/a9-deliberately-missing-book/index.html",
      "status_code": 404,
      "message": "Not Found"
    }
  ]
}
```

## Tests

```powershell
..\.venv\Scripts\python.exe -m pytest tests
```

The tests cover price normalization, relative-to-absolute URL parsing, missing descriptions, duplicate URL removal, and malformed records.

## Ethics Note

This code is intentionally limited to a public training sandbox. Before scraping any other site, check robots rules, terms, rate limits, login boundaries, copyright/privacy concerns, and whether an API or dataset is the better route.
