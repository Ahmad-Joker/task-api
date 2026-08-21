"""Entry point for the Week 5 Books to Scrape assignment."""

from pathlib import Path

import requests


BASE_URL = "https://books.toscrape.com/"
FIRST_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/ahmad/task-api)"
TIMEOUT_SECONDS = 10
CACHE_DIR = Path("cache")


def fetch_with_cache(url: str, cache_path: Path) -> str:
    """Fetch a URL once, then reuse the saved HTML on later runs."""
    if cache_path.exists():
        print(f"CACHE HIT {cache_path}")
        return cache_path.read_text(encoding="utf-8")

    print(f"FETCH {url}")
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
    )
    response.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(response.text, encoding="utf-8")
    return response.text


def main() -> None:
    html = fetch_with_cache(FIRST_CATALOGUE_URL, CACHE_DIR / "catalogue-page-1.html")
    print(f"catalogue_page_1_bytes={len(html.encode('utf-8'))}")


if __name__ == "__main__":
    main()
