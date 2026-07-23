from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="Task API", version="1.0")

STARTING_TASKS = [
    {"id": 1, "title": "Learn FastAPI basics", "done": False},
    {"id": 2, "title": "Write API tests", "done": False},
    {"id": 3, "title": "Review Swagger docs", "done": True},
]

tasks = [task.copy() for task in STARTING_TASKS]


def reset_tasks():
    tasks.clear()
    tasks.extend(task.copy() for task in STARTING_TASKS)


def find_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            return task
    return None


def task_not_found(task_id: int):
    return JSONResponse(
        status_code=404,
        content={"error": f"Task {task_id} not found"},
    )


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


@app.get("/tasks", tags=["Tasks"])
def read_tasks():
    return tasks


@app.get("/tasks/{task_id}", tags=["Tasks"])
def read_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return task_not_found(task_id)
    return task
