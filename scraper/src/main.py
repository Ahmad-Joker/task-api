"""Entry point for the Week 5 Books to Scrape assignment."""

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import time
from urllib.parse import urljoin, urlsplit, urlunsplit

from bs4 import BeautifulSoup
from pydantic import BaseModel, Field, ValidationError, field_validator
import requests


BASE_URL = "https://books.toscrape.com/"
FIRST_CATALOGUE_URL = "https://books.toscrape.com/catalogue/page-1.html"
USER_AGENT = "FlyRankInternship-A9/1.0 (+https://github.com/ahmad/task-api)"
TIMEOUT_SECONDS = 10
REQUEST_DELAY_SECONDS = 0.6
CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")
LAST_REQUEST_AT: float | None = None
VALID_RATINGS = {"One", "Two", "Three", "Four", "Five"}


class BookRecord(BaseModel):
    title: str = Field(min_length=1)
    product_url: str = Field(min_length=1)
    price_text: str = Field(min_length=1)
    price_gbp: float = Field(ge=0)
    availability_text: str = Field(min_length=1)
    rating_text: str = Field(min_length=1)
    description: str | None
    source_page: str = Field(min_length=1)
    fetched_at: str = Field(min_length=1)

    @field_validator("product_url", "source_page")
    @classmethod
    def require_books_url(cls, value: str) -> str:
        if not value.startswith(BASE_URL):
            raise ValueError("URL must stay within Books to Scrape")
        return value

    @field_validator("rating_text")
    @classmethod
    def require_known_rating(cls, value: str) -> str:
        if value not in VALID_RATINGS:
            raise ValueError("rating_text must be One, Two, Three, Four, or Five")
        return value


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
        "product_url": canonicalize_url(product_url),
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
        "source_page": canonicalize_url(source_page),
        "fetched_at": fetched_at,
    }


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url)
    return urlunsplit(
        (
            parts.scheme.lower(),
            parts.netloc.lower(),
            parts.path,
            "",
            "",
        )
    )


def normalize_price(price_text: str) -> float:
    match = re.search(r"£\s*([0-9]+(?:\.[0-9]+)?)", price_text)
    if not match:
        raise ValueError(f"Could not parse GBP price from {price_text!r}")
    return round(float(match.group(1)), 2)


def validate_records(
    raw_records: list[dict[str, str | None]],
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    valid_records: list[dict[str, object]] = []
    errors: list[dict[str, object]] = []
    seen_urls: set[str] = set()

    for raw_record in raw_records:
        record = dict(raw_record)
        product_url = canonicalize_url(str(record.get("product_url", "")))
        if product_url in seen_urls:
            continue
        seen_urls.add(product_url)
        record["product_url"] = product_url

        try:
            record["price_gbp"] = normalize_price(str(record.get("price_text", "")))
            valid_records.append(BookRecord(**record).model_dump())
        except (ValidationError, ValueError) as exc:
            errors.append(
                {
                    "product_url": product_url,
                    "error": str(exc),
                    "raw_record": record,
                }
            )

    return valid_records, errors


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


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
    raw_records = extract_book_details(book_entries)
    valid_records, errors = validate_records(raw_records)
    write_json(OUTPUT_DIR / "books.json", valid_records)
    write_json(OUTPUT_DIR / "errors.json", errors)
    print(f"valid_records={len(valid_records)}, invalid_records={len(errors)}")


if __name__ == "__main__":
    main()
