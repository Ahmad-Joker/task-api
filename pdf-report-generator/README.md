# PDF Report Generator

Small FastAPI + SQLite report pipeline:

```text
query -> render HTML -> print PDF -> store file -> serve by link
```

Dataset: little shop orders.

## Stage Status

- Stage 0: setup ready.
- Stage 1: seeded `report.db` with 200 little-shop orders.
- Stage 2: aggregation queries return totals, top products, orders per day, and all orders.
- Stage 3: HTML renders to PDF with clean table page breaks.
- Stage 4: API generates, stores, and serves reports by link.

## Run

```powershell
..\.venv\Scripts\python.exe scripts\seed.py
..\.venv\Scripts\python.exe scripts\print_report_data.py
..\.venv\Scripts\python.exe scripts\render_test_pdf.py
..\.venv\Scripts\uvicorn app:app --reload --port 8001
```

Generate a report:

```powershell
curl -i -X POST http://localhost:8001/reports
```
