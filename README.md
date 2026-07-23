# Task API

A beginner-friendly Task CRUD API for a Week 2 Backend Internship assignment. The API is built with FastAPI and stores tasks in a simple in-memory Python list.

## Features

- Root and health-check endpoints
- List all tasks
- Get one task by ID
- Create a new task
- Update a task title, done status, or both
- Delete a task
- Clear JSON error messages
- Interactive Swagger UI at `/docs`
- Automated tests with Pytest and FastAPI TestClient

## Technology Used

- Python 3.10+
- FastAPI
- Uvicorn
- Pytest
- FastAPI TestClient
- In-memory Python list storage

## Project Structure

```text
task-api/
|-- main.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- tests/
|   `-- test_api.py
`-- screenshots/
    `-- README.md
```

## Installation

Clone or download this project, then open a terminal in the `task-api` folder.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### macOS and Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## Run the API

Use this command from the project root:

```bash
uvicorn main:app --reload
```

## Local URLs

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Endpoints

| Method | Route | Purpose | Success Status |
| --- | --- | --- | --- |
| GET | `/` | Show API information | 200 |
| GET | `/health` | Check API health | 200 |
| GET | `/tasks` | List all tasks | 200 |
| GET | `/tasks/{task_id}` | Get one task | 200 |
| POST | `/tasks` | Create a task | 201 |
| PUT | `/tasks/{task_id}` | Update a task | 200 |
| DELETE | `/tasks/{task_id}` | Delete a task | 204 |

## Example Task

```json
{
  "id": 1,
  "title": "Buy milk",
  "done": false
}
```

## curl Examples

List all tasks:

```bash
curl http://localhost:8000/tasks
```

Retrieve one task:

```bash
curl http://localhost:8000/tasks/1
```

Create a task:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Buy milk\"}"
```

Update a task:

```bash
curl -X PUT http://localhost:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d "{\"title\":\"Buy oat milk\",\"done\":true}"
```

Delete a task:

```bash
curl -X DELETE http://localhost:8000/tasks/1
```

Example `curl -i` response:

```bash
curl -i http://localhost:8000/health
```

```text
HTTP/1.1 200 OK
content-type: application/json

{"status":"ok"}
```

## Status Codes

- `200 OK`: Successful read or update
- `201 Created`: Task was created
- `204 No Content`: Task was deleted and the response body is empty
- `400 Bad Request`: Request JSON is missing required data or contains invalid values
- `404 Not Found`: A task with the requested ID does not exist

## Validation

The API manually validates create and update requests so assignment-required errors return `400` instead of FastAPI's default `422`.

Validation rules:

- `POST /tasks` requires a `title`.
- `title` must not be empty or whitespace-only.
- `PUT /tasks/{task_id}` requires at least `title`, `done`, or both.
- `done` must be a JSON boolean: `true` or `false`.
- Unknown task IDs return a JSON `404` error.

Manual error responses use this format:

```json
{
  "error": "Human-readable message"
}
```

## Testing

Run the full test suite from the project root:

```bash
pytest
```

The tests reset the in-memory task list before each test so one test cannot affect another.

## In-Memory Storage

This API does not use a database or external storage. Tasks are stored in a Python list in memory. The task list resets to the three example tasks whenever the server restarts.

## Swagger Screenshot

The assignment asks for a Swagger UI screenshot saved at:

```text
screenshots/swagger-ui.png
```

This repository includes `screenshots/README.md` with step-by-step instructions for capturing and saving that screenshot.

## DB Browser for SQLite

Week 3 asks you to explore the generated SQLite database manually. DB Browser for SQLite is a beginner-friendly desktop app for opening `.db` files and running SQL.

To inspect the database:

1. Install DB Browser for SQLite from https://sqlitebrowser.org/.
2. Start this API once so `tasks.db` is created.
3. Open DB Browser for SQLite.
4. Click **Open Database** and choose `tasks.db` from the project root.
5. Open the **Browse Data** tab.
6. Select the `tasks` table.
7. Open the **Execute SQL** tab to run SQL queries.

Useful SQL queries:

```sql
SELECT * FROM tasks;
```

```sql
SELECT * FROM tasks WHERE done = 1;
```

```sql
SELECT COUNT(*) FROM tasks;
```

```sql
UPDATE tasks SET done = 1;
```

```sql
DELETE FROM tasks WHERE done = 1;
```

The first three queries are safe read-only queries. The `UPDATE` and `DELETE` examples change data, so use them only on a temporary or demo database unless you mean to change your project database.

Safe example:

```sql
SELECT COUNT(*) FROM tasks;
```

On a fresh database, this returns `3` because the app seeds exactly three example tasks when the table is empty.

## Database Screenshot

The Week 3 database screenshot should be saved at:

```text
screenshots/database-browser.png
```

This repository includes `screenshots/README.md` with exact steps for capturing it.

## Assignment Checklist

- [x] Python 3.10+ FastAPI project
- [x] Uvicorn run command
- [x] Pytest test suite
- [x] No database or external storage
- [x] In-memory task list
- [x] Exactly three preloaded example tasks
- [x] `GET /`
- [x] `GET /health`
- [x] `GET /tasks`
- [x] `GET /tasks/{task_id}`
- [x] `POST /tasks`
- [x] `PUT /tasks/{task_id}`
- [x] `DELETE /tasks/{task_id}`
- [x] Manual JSON errors with `error` key
- [x] Required status codes
- [x] Swagger UI at `/docs`
- [x] ReDoc at `/redoc`
- [x] Screenshot instructions
- [x] Beginner-friendly README
