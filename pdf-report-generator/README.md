# PDF Report Generator

Small FastAPI + SQLite report pipeline:

```text
query -> render HTML -> print PDF -> store file -> serve by link
```

Dataset: little shop orders.

## Stage Status

- Stage 0: setup ready.
- Stage 1: seeded `report.db` with 200 little-shop orders.

## Run

```powershell
..\.venv\Scripts\python.exe scripts\seed.py
```
