# Task API

A beginner-friendly FastAPI Task CRUD API built across three backend assignments.

Architecture progression:

```text
A1: Client -> FastAPI -> in-memory list
A2: Client -> FastAPI -> SQLite tasks.db
A3: Client -> FastAPI container -> PostgreSQL container
```

Assignment A3 upgrades the app to run as a Docker Compose stack with PostgreSQL persistence. The public API behavior stayed the same: routes, request bodies, response bodies, validation rules, and status codes remain compatible with A1 and A2.

## Features

- Root and health-check endpoints
- Full task CRUD API
- JSON error responses with an `error` key
- Swagger UI at `/docs`
- PostgreSQL-backed persistence
- Automatic table creation
- Seed data only when the table is empty
- Docker Compose one-command startup
- Pytest coverage for endpoints, validation, initialization, persistence, and SQL parameterization

## Technology Used

- Python 3.10+
- FastAPI
- Uvicorn
- PostgreSQL
- psycopg 3
- python-dotenv
- Docker
- Docker Compose
- Pytest
- FastAPI TestClient

## Project Structure

```text
task-api/
|-- main.py
|-- database.py
|-- requirements.txt
|-- Dockerfile
|-- compose.yaml
|-- .env.example
|-- .gitignore
|-- README.md
|-- tests/
|   |-- conftest.py
|   `-- test_api.py
`-- screenshots/
    |-- README.md
    |-- swagger-ui.png
    `-- database-browser.png
```

The real `.env` file and database files are ignored by Git.

## Clean Clone Setup

From a fresh clone, create your local environment file and start the stack.

Windows PowerShell:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

macOS and Linux:

```bash
cp .env.example .env
docker compose up --build
```

The API will be available at:

- API: http://localhost:8000
- Swagger: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Docker Commands

Start or rebuild the complete stack:

```bash
docker compose up --build
```

Start in the background:

```bash
docker compose up -d --build
```

Stop containers while keeping the PostgreSQL volume:

```bash
docker compose down
```

Destructive reset, including database volume deletion:

```bash
docker compose down -v
```

Use `docker compose down -v` only when you intentionally want to erase the PostgreSQL data.

## Docker Concepts

An image is the packaged blueprint for a service. The API image is built from the `Dockerfile`; the PostgreSQL image is pulled from Docker Hub.

A container is a running instance of an image. In this project, Docker Compose runs one API container and one PostgreSQL container.

## Dockerfile

The API `Dockerfile`:

1. Uses an official slim Python image.
2. Sets `/app` as the working directory.
3. Copies `requirements.txt` first for better build caching.
4. Installs dependencies.
5. Copies the application files.
6. Exposes port `8000`.
7. Runs Uvicorn on `0.0.0.0:8000`.

## Compose Services

`compose.yaml` defines two services:

| Service | Purpose |
| --- | --- |
| `api` | Builds and runs the FastAPI app |
| `db` | Runs PostgreSQL using the official `postgres:16` image |

The API uses this internal Docker hostname:

```text
db
```

Inside Docker Compose, `DATABASE_URL` points to:

```text
postgresql://postgres:dev@db:5432/tasks
```

The `db` service has a healthcheck using `pg_isready`, and the `api` service waits for the database to become healthy before starting.

## Environment Variables

`.env.example` is safe to commit and documents the local development values:

```text
DATABASE_URL=postgresql://postgres:dev@localhost:5432/tasks
POSTGRES_USER=postgres
POSTGRES_PASSWORD=dev
POSTGRES_DB=tasks
```

The real `.env` file is ignored by Git. Do not commit real secrets or production credentials.

For local development outside Docker, `DATABASE_URL` should use `localhost`:

```text
postgresql://postgres:dev@localhost:5432/tasks
```

Inside Docker Compose, the API uses `db` as the host:

```text
postgresql://postgres:dev@db:5432/tasks
```

## PostgreSQL Schema

The app creates this table automatically if it does not already exist:

```sql
CREATE TABLE IF NOT EXISTS tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    done BOOLEAN NOT NULL DEFAULT FALSE
);
```

PostgreSQL stores `done` as a real boolean. API responses return JSON booleans: `false` or `true`.

## Database Initialization

On startup, the app:

1. Reads `DATABASE_URL`.
2. Connects to PostgreSQL with a retry loop.
3. Creates the `tasks` table if missing.
4. Counts existing rows.
5. Seeds exactly three example tasks only when the table is empty.
6. Commits changes.
7. Closes connections safely.

Restarting the API or containers does not duplicate seed data.

Seed tasks:

```text
Learn FastAPI basics
Write API tests
Review Swagger docs
```

## Persistence

PostgreSQL data is stored in the named Docker volume:

```text
taskdata
```

That means task data survives:

- API container restarts
- database container restarts
- `docker compose down`

Data is erased only when the volume is deleted, such as with:

```bash
docker compose down -v
```

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

List tasks:

```bash
curl http://localhost:8000/tasks
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

## Validation

- `POST /tasks` requires a non-empty `title`.
- `PUT /tasks/{task_id}` requires `title`, `done`, or both.
- `title` must not be empty or whitespace-only.
- `done` must be a JSON boolean: `true` or `false`.
- Unknown task IDs return `404`.

Manual errors use this format:

```json
{
  "error": "Human-readable message"
}
```

## Parameterized Queries

All SQL queries that include values use psycopg placeholders:

```python
cursor.execute(
    "SELECT id, title, done FROM tasks WHERE id = %s",
    (task_id,)
)
```

The project does not use f-strings, string concatenation, or string formatting for SQL values.

## Testing

Start PostgreSQL first:

```bash
docker compose up -d db
```

Then run:

```bash
pytest
```

The tests use a separate PostgreSQL database named `tasks_test`. They recreate that test database during the test run so the normal development database is not modified destructively.

## Persistence Test Steps

1. Start the stack:

   ```bash
   docker compose up -d --build
   ```

2. Create a task:

   ```bash
   curl -X POST http://localhost:8000/tasks -H "Content-Type: application/json" -d "{\"title\":\"Persistent task\"}"
   ```

3. Stop the containers:

   ```bash
   docker compose down
   ```

4. Start the stack again:

   ```bash
   docker compose up -d
   ```

5. Confirm the task is still there:

   ```bash
   curl http://localhost:8000/tasks
   ```

## Inspecting PostgreSQL With psql

Open a shell inside the database container:

```bash
docker compose exec db psql -U postgres -d tasks
```

Useful commands:

```sql
\dt
SELECT * FROM tasks;
SELECT COUNT(*) FROM tasks;
SELECT * FROM tasks WHERE done = TRUE;
```

Exit `psql`:

```text
\q
```

## Screenshots

Existing screenshots:

- `screenshots/swagger-ui.png`
- `screenshots/database-browser.png`

Assignment A3 should include a PostgreSQL data screenshot at:

```text
screenshots/postgres-data.png
```

The screenshot can show `psql`, pgAdmin, or DBeaver displaying the `tasks` table rows. Instructions are in `screenshots/README.md`.

## Assignment Completion Checklist

- [x] Preserved A1 and A2 history
- [x] Replaced final runtime SQLite storage with PostgreSQL
- [x] Added psycopg 3
- [x] Added python-dotenv
- [x] Reads `DATABASE_URL` from environment
- [x] Kept credentials out of Python source
- [x] Added PostgreSQL connection retry loop
- [x] Creates `tasks` table automatically
- [x] Seeds exactly three tasks only when empty
- [x] Keeps endpoint behavior compatible with A1 and A2
- [x] Uses parameterized SQL placeholders
- [x] Added Dockerfile
- [x] Added Compose `api` and `db` services
- [x] Added PostgreSQL healthcheck
- [x] API depends on healthy database
- [x] Uses named volume `taskdata`
- [x] Stack starts with `docker compose up --build`
- [x] Tests pass
- [x] Swagger works at `/docs`
- [x] `.env` is ignored
- [x] `.env.example` is tracked
- [x] Screenshot instructions are documented
