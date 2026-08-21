from fastapi import FastAPI


app = FastAPI(
    title="PDF Report Generator",
    version="1.0.0",
    description="Generate PDF reports from SQLite data and serve them by link.",
)


@app.get("/health")
def health():
    return {"status": "ok"}
