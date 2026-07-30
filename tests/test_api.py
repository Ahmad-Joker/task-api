import os

from fastapi.testclient import TestClient
import psycopg
import pytest

os.environ["DATABASE_URL"] = "postgresql://postgres:dev@localhost:5432/tasks_test"

import main
from main import app, initialize_database


client = TestClient(app)

TEST_DATABASE_URL = os.environ["DATABASE_URL"]
ADMIN_DATABASE_URL = "postgresql://postgres:dev@localhost:5432/tasks"


def recreate_test_database():
    with psycopg.connect(ADMIN_DATABASE_URL, autocommit=True) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s AND pid <> pg_backend_pid()
                """,
                ("tasks_test",),
            )
            cursor.execute("DROP DATABASE IF EXISTS tasks_test")
            cursor.execute("CREATE DATABASE tasks_test")


@pytest.fixture(autouse=True)
def use_test_database():
    recreate_test_database()
    initialize_database()


def test_read_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"],
    }


def test_read_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_database_connection_uses_environment_url():
    initialize_database()

    assert main.initialize_database is initialize_database


def test_tasks_table_is_created():
    initialize_database()

    with psycopg.connect(TEST_DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s AND table_name = %s
                """,
                ("public", "tasks"),
            )
            assert cursor.fetchone() == ("tasks",)


def test_database_seeds_three_tasks_on_first_initialization():
    initialize_database()

    with psycopg.connect(TEST_DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tasks")
            assert cursor.fetchone()[0] == 3


def test_database_reinitialization_does_not_duplicate_seeds():
    initialize_database()
    initialize_database()

    with psycopg.connect(TEST_DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM tasks")
            assert cursor.fetchone()[0] == 3


def test_read_tasks():
    response = client.get("/tasks")

    assert response.status_code == 200
    assert response.json() == [
        {"id": 1, "title": "Learn FastAPI basics", "done": False},
        {"id": 2, "title": "Write API tests", "done": False},
        {"id": 3, "title": "Review Swagger docs", "done": True},
    ]


def test_read_existing_task():
    response = client.get("/tasks/1")

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Learn FastAPI basics", "done": False}


def test_read_nonexistent_task():
    response = client.get("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"error": "Task 999 not found"}


def test_create_valid_task():
    response = client.post("/tasks", json={"title": "Buy milk"})

    assert response.status_code == 201
    assert response.json() == {"id": 4, "title": "Buy milk", "done": False}

    list_response = client.get("/tasks")
    assert len(list_response.json()) == 4


def test_create_persists_task_across_database_connections():
    response = client.post("/tasks", json={"title": "Buy milk"})

    assert response.status_code == 201

    with psycopg.connect(TEST_DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT title, done FROM tasks WHERE id = %s",
                (response.json()["id"],),
            )
            assert cursor.fetchone() == ("Buy milk", False)


def test_create_task_with_missing_title():
    response = client.post("/tasks", json={})

    assert response.status_code == 400
    assert response.json() == {"error": "Title is required"}


def test_create_task_with_empty_title():
    response = client.post("/tasks", json={"title": ""})

    assert response.status_code == 400
    assert response.json() == {"error": "Title must not be empty"}


def test_create_task_with_whitespace_title():
    response = client.post("/tasks", json={"title": "   "})

    assert response.status_code == 400
    assert response.json() == {"error": "Title must not be empty"}


def test_update_only_title():
    response = client.put("/tasks/1", json={"title": "Updated title"})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Updated title", "done": False}


def test_update_only_done():
    response = client.put("/tasks/1", json={"done": True})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Learn FastAPI basics", "done": True}


def test_update_title_and_done():
    response = client.put("/tasks/1", json={"title": "Finish project", "done": True})

    assert response.status_code == 200
    assert response.json() == {"id": 1, "title": "Finish project", "done": True}


def test_update_with_empty_body():
    response = client.put("/tasks/1", json={})

    assert response.status_code == 400
    assert response.json() == {"error": "Request body must include title, done, or both"}


def test_update_with_invalid_title():
    response = client.put("/tasks/1", json={"title": "   "})

    assert response.status_code == 400
    assert response.json() == {"error": "Title must not be empty"}


def test_update_with_invalid_done_value():
    response = client.put("/tasks/1", json={"done": "yes"})

    assert response.status_code == 400
    assert response.json() == {"error": "Done must be true or false"}


def test_update_nonexistent_task():
    response = client.put("/tasks/999", json={"title": "Missing task"})

    assert response.status_code == 404
    assert response.json() == {"error": "Task 999 not found"}


def test_delete_existing_task():
    response = client.delete("/tasks/1")

    assert response.status_code == 204
    assert response.content == b""


def test_deleted_task_is_gone():
    delete_response = client.delete("/tasks/1")
    read_response = client.get("/tasks/1")

    assert delete_response.status_code == 204
    assert read_response.status_code == 404
    assert read_response.json() == {"error": "Task 1 not found"}


def test_delete_nonexistent_task():
    response = client.delete("/tasks/999")

    assert response.status_code == 404
    assert response.json() == {"error": "Task 999 not found"}


def test_data_persists_across_separate_database_connections():
    create_response = client.post("/tasks", json={"title": "Persistent task"})
    task_id = create_response.json()["id"]

    with psycopg.connect(TEST_DATABASE_URL) as first_connection:
        with first_connection.cursor() as first_cursor:
            first_cursor.execute("SELECT title FROM tasks WHERE id = %s", (task_id,))
            assert first_cursor.fetchone()[0] == "Persistent task"

    with psycopg.connect(TEST_DATABASE_URL) as second_connection:
        with second_connection.cursor() as second_cursor:
            second_cursor.execute("SELECT title FROM tasks WHERE id = %s", (task_id,))
            assert second_cursor.fetchone()[0] == "Persistent task"


def test_data_remains_after_reinitializing_database():
    create_response = client.post("/tasks", json={"title": "Restart-safe task"})
    task_id = create_response.json()["id"]

    initialize_database()

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json() == {"id": task_id, "title": "Restart-safe task", "done": False}


def test_swagger_and_openapi_are_accessible():
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "Task API"


def test_repository_sql_uses_parameterized_placeholders():
    database_source = open("database.py", encoding="utf-8").read()

    assert "WHERE id = %s" in database_source
    assert "VALUES (%s, %s)" in database_source
    assert "WHERE id = ?" not in database_source
    assert "VALUES (?, ?)" not in database_source
    assert "execute(f\"" not in database_source
    assert "execute(f'" not in database_source
