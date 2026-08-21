from datetime import datetime
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse

from db import REPORTS_DIR, connect, initialize_database
from renderer import render_pdf
from report_data import get_report_data


app = FastAPI(
    title="PDF Report Generator",
    version="1.0.0",
    description="Generate PDF reports from SQLite data and serve them by link.",
)


@app.get("/health")
def health():
    return {"status": "ok"}


def report_to_response(row):
    return {
        "id": row["id"],
        "path": row["path"],
        "created_at": row["created_at"],
        "file": f"/reports/{row['id']}/file",
    }


def get_report_row(report_id: int):
    initialize_database()
    with connect() as connection:
        return connection.execute(
            "SELECT id, path, created_at FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()


@app.post("/reports", status_code=201)
def create_report():
    initialize_database()
    created_at = datetime.now().isoformat(timespec="seconds")

    with connect() as connection:
        cursor = connection.execute(
            "INSERT INTO reports (path, created_at) VALUES (?, ?)",
            ("", created_at),
        )
        report_id = cursor.lastrowid
        output_path = REPORTS_DIR / f"{report_id}.pdf"
        connection.execute(
            "UPDATE reports SET path = ? WHERE id = ?",
            (str(output_path), report_id),
        )
        connection.commit()

    render_pdf(get_report_data(), output_path)
    row = get_report_row(report_id)
    return JSONResponse(status_code=201, content=report_to_response(row))


@app.get("/reports/{report_id}")
def read_report(report_id: int):
    row = get_report_row(report_id)
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Report not found"})
    return report_to_response(row)


@app.get("/reports/{report_id}/file")
def download_report(report_id: int):
    row = get_report_row(report_id)
    if row is None:
        return JSONResponse(status_code=404, content={"error": "Report not found"})

    path = Path(row["path"])
    if not path.exists():
        return JSONResponse(status_code=404, content={"error": "Report file not found"})

    return FileResponse(
        path,
        media_type="application/pdf",
        filename=f"little-shop-report-{report_id}.pdf",
    )
