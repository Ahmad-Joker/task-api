from pathlib import Path

from fastapi.testclient import TestClient

from app import app
from db import connect
from report_data import get_report_data
from scripts.seed import seed_orders


client = TestClient(app)


def test_seed_creates_exactly_200_orders_even_when_run_twice():
    seed_orders()
    seed_orders()

    with connect() as connection:
        count = connection.execute("SELECT COUNT(*) FROM orders").fetchone()[0]

    assert count == 200


def test_report_data_contains_required_sections():
    seed_orders()

    report = get_report_data()

    assert report["totals"]["total_orders"] == 200
    assert len(report["top_products"]) == 5
    assert len(report["orders_per_day"]) == 7
    assert len(report["orders"]) == 200


def test_report_endpoints_generate_metadata_and_pdf():
    seed_orders()

    response = client.post("/reports", json={"force": True})
    report_id = response.json()["id"]
    file_response = client.get(f"/reports/{report_id}/file")

    assert response.status_code == 201
    assert response.json()["file"] == f"/reports/{report_id}/file"
    assert file_response.status_code == 200
    assert file_response.headers["content-type"] == "application/pdf"
    assert file_response.content.startswith(b"%PDF")


def test_duplicate_report_requests_reuse_todays_report():
    seed_orders()

    first = client.post("/reports", json={"force": True})
    second = client.post("/reports")
    third = client.post("/reports")

    assert first.status_code == 201
    assert second.status_code == 200
    assert third.status_code == 200
    assert second.json()["id"] == third.json()["id"]


def test_unknown_report_returns_404():
    response = client.get("/reports/999999")

    assert response.status_code == 404
    assert response.json() == {"error": "Report not found"}
