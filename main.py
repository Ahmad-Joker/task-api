from fastapi import FastAPI

app = FastAPI(title="Task API", version="1.0")


@app.get("/", tags=["System"])
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get("/health", tags=["System"])
def read_health():
    return {"status": "ok"}
