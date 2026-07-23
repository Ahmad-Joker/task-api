# Task API

A beginner-friendly Task CRUD API for Backend Internship assignments. The API started as a Week 2 in-memory FastAPI project and was upgraded for Week 3 Assignment A2 to store tasks in a SQLite database named `tasks.db`.

The public API behavior stayed the same: the routes, request shapes, response shapes, validation rules, and status codes remain compatible with Assignment 1.

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
- SQLite persistence across server restarts
- Automatic database and table creation
- Seed data only when the database is empty

## Technology Used

- Python 3.10+
- FastAPI
- Uvicorn
- Pytest
- FastAPI TestClient
- Python's built-in `sqlite3` module
- SQLite database file storage

## Project Structure

```text
task-api/
|-- main.py
|-- requirements.txt
|-- README.md
|-- .gitignore
|-- tasks.db              # generated automatically and ignored by Git
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

When the API starts, it automatically creates `tasks.db` in the project root if the file does not already exist.

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

The tests use temporary SQLite database files so one test cannot affect another and the real development `tasks.db` is not changed permanently.

## Week 3 Database Upgrade

Assignment 1 used a simple Python list:

```text
Client -> API -> in-memory list
```

Assignment 2 uses SQLite:

```text
Client -> API -> SQLite tasks.db
```

SQLite was selected because it is perfect for a beginner backend assignment:

- It stores the database in one file.
- It does not require a separate database server.
- It needs zero setup beyond Python.
- Data survives server restarts.

## Database Schema

The app creates this table automatically:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0
);
```

SQLite stores `done` as `0` or `1`. API responses convert those values into real JSON booleans: `false` or `true`.

## Automatic Database Initialization

On startup, the app:

1. Opens or creates `tasks.db`.
2. Creates the `tasks` table if it does not exist.
3. Counts existing rows.
4. Seeds exactly three example tasks only when the table is empty.
5. Commits changes.
6. Closes the database connection safely.

Restarting the server does not duplicate the three seed tasks.

## Persistence

Tasks are now stored in `tasks.db`, so created, updated, and deleted data remains after the server restarts.

To demonstrate persistence:

1. Start the API.
2. Create a task with `POST /tasks`.
3. Stop the server with `Ctrl + C`.
4. Start the API again.
5. Run `GET /tasks`.

The task you created should still be present.

## Database File

The database file is located in the project root:

```text
tasks.db
```

This file is generated automatically and ignored by Git. A clean clone can run the app without manually creating the database.

## Parameterized Queries

All SQL queries that include values use parameterized placeholders. This keeps user input separate from SQL text.

Example:

```python
cursor.execute("SELECT id, title, done FROM tasks WHERE id = ?", (task_id,))
```

The project does not build SQL with f-strings, string concatenation, or formatting for user-supplied values.

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

## Assignment 1 Checklist

- [x] Python 3.10+ FastAPI project
- [x] Uvicorn run command
- [x] Pytest test suite
- [x] Original Week 2 implementation used no database or external storage
- [x] Original Week 2 implementation used an in-memory task list
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

## Assignment 2 Checklist

- [x] Replaced in-memory storage with SQLite
- [x] Uses Python's built-in `sqlite3` module
- [x] Creates `tasks.db` automatically
- [x] Creates the `tasks` table automatically
- [x] Seeds exactly three tasks only when empty
- [x] Does not duplicate seeds on restart
- [x] Keeps endpoint behavior compatible with Assignment 1
- [x] Converts SQLite `0` and `1` values to JSON booleans
- [x] Uses parameterized SQL queries
- [x] Tests use temporary databases
- [x] `tasks.db` is ignored by Git
- [x] Swagger remains available at `/docs`
- [x] DB Browser instructions are documented
- [x] Database screenshot instructions are documented
