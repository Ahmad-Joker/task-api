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

## Run

```powershell
..\.venv\Scripts\python.exe scripts\seed.py
..\.venv\Scripts\python.exe scripts\print_report_data.py
```
