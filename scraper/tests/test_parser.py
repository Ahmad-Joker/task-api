from src.main import (
    BASE_URL,
    canonicalize_url,
    normalize_price,
    parse_book_detail,
    parse_catalogue_page,
    validate_records,
)


def test_normalize_price_text_to_gbp_number():
    assert normalize_price("£51.77") == 51.77


def test_relative_catalogue_links_become_absolute_urls():
    html = """
    <article class="product_pod">
      <h3><a href="a-light-in-the-attic_1000/index.html">A Light</a></h3>
    </article>
    <li class="next"><a href="page-2.html">next</a></li>
    """

    book_urls, next_url = parse_catalogue_page(
        html,
        "https://books.toscrape.com/catalogue/page-1.html",
    )

    assert book_urls == [
        "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    ]
    assert next_url == "https://books.toscrape.com/catalogue/page-2.html"


def test_missing_description_returns_none():
    html = """
    <div class="product_main">
      <h1>Title</h1>
      <p class="price_color">£10.50</p>
      <p class="instock availability">In stock</p>
      <p class="star-rating Four"></p>
    </div>
    """

    record = parse_book_detail(
        html,
        f"{BASE_URL}catalogue/example_1/index.html",
        f"{BASE_URL}catalogue/page-1.html",
        "2026-08-21T00:00:00+00:00",
    )

    assert record["description"] is None


def test_duplicate_product_urls_are_removed_during_validation():
    raw_record = {
        "title": "A Book",
        "product_url": f"{BASE_URL}catalogue/example_1/index.html?utm=ignored",
        "price_text": "£12.34",
        "availability_text": "In stock",
        "rating_text": "Three",
        "description": None,
        "source_page": f"{BASE_URL}catalogue/page-1.html",
        "fetched_at": "2026-08-21T00:00:00+00:00",
    }

    valid_records, errors = validate_records([raw_record, dict(raw_record)])

    assert len(valid_records) == 1
    assert errors == []
    assert valid_records[0]["product_url"] == canonicalize_url(raw_record["product_url"])


def test_malformed_record_goes_to_errors():
    malformed = {
        "title": "",
        "product_url": f"{BASE_URL}catalogue/broken_1/index.html",
        "price_text": "free",
        "availability_text": "",
        "rating_text": "Six",
        "description": None,
        "source_page": f"{BASE_URL}catalogue/page-1.html",
        "fetched_at": "2026-08-21T00:00:00+00:00",
    }

    valid_records, errors = validate_records([malformed])

    assert valid_records == []
    assert len(errors) == 1
