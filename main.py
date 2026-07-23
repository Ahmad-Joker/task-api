from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

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


def bad_request(message: str):
    return JSONResponse(status_code=400, content={"error": message})


async def read_json_body(request: Request):
    try:
        body = await request.json()
    except Exception:
        return None
    if not isinstance(body, dict):
        return None
    return body


def validate_title(title):
    if not isinstance(title, str) or title.strip() == "":
        return None
    return title.strip()


def get_next_task_id():
    if not tasks:
        return 1
    return max(task["id"] for task in tasks) + 1


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


@app.post("/tasks", status_code=201, tags=["Tasks"])
async def create_task(request: Request):
    body = await read_json_body(request)
    if body is None or "title" not in body:
        return bad_request("Title is required")

    title = validate_title(body.get("title"))
    if title is None:
        return bad_request("Title must not be empty")

    task = {"id": get_next_task_id(), "title": title, "done": False}
    tasks.append(task)
    return task


@app.put("/tasks/{task_id}", tags=["Tasks"])
async def update_task(task_id: int, request: Request):
    task = find_task(task_id)
    if task is None:
        return task_not_found(task_id)

    body = await read_json_body(request)
    if body is None or body == {}:
        return bad_request("Request body must include title, done, or both")

    if "title" not in body and "done" not in body:
        return bad_request("Request body must include title, done, or both")

    if "title" in body:
        title = validate_title(body.get("title"))
        if title is None:
            return bad_request("Title must not be empty")
        task["title"] = title

    if "done" in body:
        done = body.get("done")
        if not isinstance(done, bool):
            return bad_request("Done must be true or false")
        task["done"] = done

    return task


@app.delete("/tasks/{task_id}", status_code=204, tags=["Tasks"])
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return task_not_found(task_id)

    tasks.remove(task)
    return Response(status_code=204)
