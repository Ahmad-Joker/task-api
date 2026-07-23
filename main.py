import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

STARTING_TASKS = [
    {"id": 1, "title": "Learn FastAPI basics", "done": False},
    {"id": 2, "title": "Write API tests", "done": False},
    {"id": 3, "title": "Review Swagger docs", "done": True},
]

DB_PATH = Path(__file__).with_name("tasks.db")


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A beginner-friendly SQLite-backed Task CRUD API built with FastAPI.",
    lifespan=lifespan,
)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                done INTEGER NOT NULL DEFAULT 0
            )
            """
        )
        cursor.execute("SELECT COUNT(*) AS task_count FROM tasks")
        task_count = cursor.fetchone()["task_count"]

        if task_count == 0:
            for task in STARTING_TASKS:
                cursor.execute(
                    "INSERT INTO tasks (title, done) VALUES (?, ?)",
                    (task["title"], int(task["done"])),
                )

        connection.commit()


def row_to_task(row):
    return {
        "id": row["id"],
        "title": row["title"],
        "done": bool(row["done"]),
    }


def find_task(task_id: int):
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT id, title, done FROM tasks WHERE id = ?",
            (task_id,),
        )
        row = cursor.fetchone()

    if row is None:
        return None
    return row_to_task(row)


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


@app.get(
    "/",
    tags=["System"],
    summary="Show API information",
    description="Returns the API name, version, and main endpoint list.",
    response_description="Basic API information",
)
def read_root():
    return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


@app.get(
    "/health",
    tags=["System"],
    summary="Check API health",
    description="Returns a simple status response that confirms the API is running.",
    response_description="Health status",
)
def read_health():
    return {"status": "ok"}


@app.get(
    "/tasks",
    tags=["Tasks"],
    summary="List all tasks",
    description="Returns every task currently stored in the SQLite database.",
    response_description="Complete task list",
)
def read_tasks():
    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT id, title, done FROM tasks")
        rows = cursor.fetchall()

    return [row_to_task(row) for row in rows]


@app.get(
    "/tasks/{task_id}",
    tags=["Tasks"],
    summary="Get one task",
    description="Returns a single task by ID, or a JSON 404 error when it does not exist.",
    response_description="The matching task",
    responses={
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"error": "Task 999 not found"},
                }
            },
        }
    },
)
def read_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return task_not_found(task_id)
    return task


@app.post(
    "/tasks",
    status_code=201,
    tags=["Tasks"],
    summary="Create a task",
    description="Creates a new task from a title. The API generates the next integer ID and sets done to false.",
    response_description="The created task",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {"title": {"type": "string", "example": "Buy milk"}},
                        "required": ["title"],
                    },
                    "example": {"title": "Buy milk"},
                }
            },
        },
        "responses": {
            "201": {
                "description": "Task created",
                "content": {
                    "application/json": {
                        "example": {"id": 4, "title": "Buy milk", "done": False},
                    }
                },
            },
            "400": {
                "description": "Invalid task input",
                "content": {
                    "application/json": {
                        "example": {"error": "Title must not be empty"},
                    }
                },
            },
        },
    },
)
async def create_task(request: Request):
    body = await read_json_body(request)
    if body is None or "title" not in body:
        return bad_request("Title is required")

    title = validate_title(body.get("title"))
    if title is None:
        return bad_request("Title must not be empty")

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "INSERT INTO tasks (title, done) VALUES (?, ?)",
            (title, 0),
        )
        task_id = cursor.lastrowid
        connection.commit()

    return {"id": task_id, "title": title, "done": False}


@app.put(
    "/tasks/{task_id}",
    tags=["Tasks"],
    summary="Update a task",
    description="Updates a task title, done status, or both. Fields not included in the request are preserved.",
    response_description="The updated task",
    openapi_extra={
        "requestBody": {
            "required": True,
            "content": {
                "application/json": {
                    "schema": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "example": "Updated title"},
                            "done": {"type": "boolean", "example": True},
                        },
                    },
                    "example": {"title": "Updated title", "done": True},
                }
            },
        },
        "responses": {
            "200": {
                "description": "Task updated",
                "content": {
                    "application/json": {
                        "example": {"id": 1, "title": "Updated title", "done": True},
                    }
                },
            },
            "400": {
                "description": "Invalid update input",
                "content": {
                    "application/json": {
                        "example": {"error": "Done must be true or false"},
                    }
                },
            },
            "404": {
                "description": "Task not found",
                "content": {
                    "application/json": {
                        "example": {"error": "Task 999 not found"},
                    }
                },
            },
        },
    },
)
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

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute(
            "UPDATE tasks SET title = ?, done = ? WHERE id = ?",
            (task["title"], int(task["done"]), task_id),
        )
        connection.commit()

    return task


@app.delete(
    "/tasks/{task_id}",
    status_code=204,
    tags=["Tasks"],
    summary="Delete a task",
    description="Deletes a task by ID and returns an empty response body.",
    response_description="Task deleted",
    responses={
        404: {
            "description": "Task not found",
            "content": {
                "application/json": {
                    "example": {"error": "Task 999 not found"},
                }
            },
        }
    },
)
def delete_task(task_id: int):
    task = find_task(task_id)
    if task is None:
        return task_not_found(task_id)

    with get_connection() as connection:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        connection.commit()

    return Response(status_code=204)
