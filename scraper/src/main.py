"""Entry point for the Week 5 Books to Scrape assignment."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests


BASE_URL = "https://books.toscrape.com/"
FIRST_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/ahmad/task-api)"
TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.6
CACHE_DIR = Path("cache")
LAST_REQUEST_AT: float | None = None


def fetch_with_cache(url: str, cache_path: Path) -> str:
    """Fetch a URL once, then reuse the saved HTML on later runs."""
    global LAST_REQUEST_AT

    if cache_path.exists():
        print(f"CACHE HIT {cache_path}")
        return cache_path.read_text(encoding="utf-8")

    if LAST_REQUEST_AT is not None:
        wait_for = REQUEST_DELAY_SECONDS - (time.monotonic() - LAST_REQUEST_AT)
        if wait_for > 0:
            time.sleep(wait_for)

    print(f"FETCH {url}")
    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT_SECONDS,
    )
    LAST_REQUEST_AT = time.monotonic()
    response.raise_for_status()
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(response.text, encoding="utf-8")
    return response.text


def parse_catalogue_page(html: str, page_url: str) -> tuple[list[str], str | None]:
    soup = BeautifulSoup(html, "html.parser")
    book_urls = [
        urljoin(page_url, link["href"])
        for link in soup.select("article.product_pod h3 a[href]")
    ]
    next_link = soup.select_one("li.next a[href]")
    next_url = urljoin(page_url, next_link["href"]) if next_link else None
    return book_urls, next_url


def discover_books(max_pages: int = 3) -> list[dict[str, str]]:
    discovered: list[dict[str, str]] = []
    seen_urls: set[str] = set()
    current_url: str | None = FIRST_CATALOGUE_URL

    for page_number in range(1, max_pages + 1):
        if current_url is None:
            break

        html = fetch_with_cache(
            current_url,
            CACHE_DIR / f"catalogue-page-{page_number}.html",
        )
        book_urls, next_url = parse_catalogue_page(html, current_url)
        for book_url in book_urls:
            if book_url not in seen_urls:
                seen_urls.add(book_url)
                discovered.append(
                    {
                        "product_url": book_url,
                        "source_page": current_url,
                    }
                )
        current_url = next_url

    print(
        f"catalogue_pages={max_pages}, discovered={len(discovered)}, "
        f"unique_urls={len(seen_urls)}"
    )
    return discovered


def cache_name_for_product(product_url: str) -> str:
    slug = product_url.rstrip("/").split("/")[-2]
    safe_slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", slug).strip("-")
    digest = hashlib.sha1(product_url.encode("utf-8")).hexdigest()[:10]
    return f"{safe_slug[:80]}-{digest}.html"


def parse_rating_text(rating_classes: list[str]) -> str:
    for class_name in rating_classes:
        if class_name != "star-rating":
            return class_name
    return ""


def parse_book_detail(
    html: str,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> dict[str, str | None]:
    soup = BeautifulSoup(html, "html.parser")
    title_node = soup.select_one("div.product_main h1")
    price_node = soup.select_one("div.product_main p.price_color")
    availability_node = soup.select_one("div.product_main p.instock.availability")
    rating_node = soup.select_one("div.product_main p.star-rating")
    description_heading = soup.select_one("#product_description")
    description_node = (
        description_heading.find_next_sibling("p") if description_heading else None
    )

    return {
        "title": title_node.get_text(strip=True) if title_node else "",
        "product_url": product_url,
        "price_text": price_node.get_text(strip=True) if price_node else "",
        "availability_text": (
            availability_node.get_text(" ", strip=True) if availability_node else ""
        ),
        "rating_text": parse_rating_text(rating_node.get("class", []))
        if rating_node
        else "",
        "description": description_node.get_text(" ", strip=True)
        if description_node
        else None,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }


def extract_book_details(book_entries: list[dict[str, str]]) -> list[dict[str, str | None]]:
    records: list[dict[str, str | None]] = []
    fetched_at = datetime.now(timezone.utc).isoformat()

    for entry in book_entries:
        product_url = entry["product_url"]
        html = fetch_with_cache(
            product_url,
            CACHE_DIR / "books" / cache_name_for_product(product_url),
        )
        records.append(
            parse_book_detail(
                html=html,
                product_url=product_url,
                source_page=entry["source_page"],
                fetched_at=fetched_at,
            )
        )

    if records:
        print(json.dumps(records[0], indent=2, ensure_ascii=False))
    print(f"detail_pages={len(records)}")
    return records


def main() -> None:
    book_entries = discover_books(max_pages=3)
    extract_book_details(book_entries)


if __name__ == "__main__":
    main()
