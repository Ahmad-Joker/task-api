# Week 5 A9 Polite Scraper

## Target Classification

- Site: Books to Scrape, `https://books.toscrape.com/`
- Parent sandbox: `https://toscrape.com/`, a site made for scraping practice.
- Scope: only the first 3 catalogue pages from Books to Scrape.
- Expected collection size: 60 book detail pages discovered from those catalogue pages.
- Collected data: title, product URL, raw price text, normalized GBP price, availability, rating, description, source catalogue page, and fetch timestamp.
- Robots check: `https://books.toscrape.com/robots.txt` returned HTTP 404 during inspection, so no robots directives were published there.

I will not reuse this code on another site without checking its rules and terms first.

## Entry Point

The scraper entry file is `src/main.py`.
