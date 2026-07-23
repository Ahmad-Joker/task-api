import sqlite3

from fastapi.testclient import TestClient
import pytest

import main
from main import app, initialize_database


client = TestClient(app)


@pytest.fixture(autouse=True)
def use_temporary_database(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks.db"
    monkeypatch.setattr(main, "DB_PATH", test_db)
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


def test_database_file_is_created(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks.db"
    monkeypatch.setattr(main, "DB_PATH", test_db)

    initialize_database()

    assert test_db.exists()


def test_tasks_table_is_created(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks.db"
    monkeypatch.setattr(main, "DB_PATH", test_db)

    initialize_database()

    with sqlite3.connect(test_db) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type = ? AND name = ?",
            ("table", "tasks"),
        )
        assert cursor.fetchone() == ("tasks",)


def test_database_seeds_three_tasks_on_first_initialization(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks.db"
    monkeypatch.setattr(main, "DB_PATH", test_db)

    initialize_database()

    with sqlite3.connect(test_db) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT COUNT(*) FROM tasks")
        assert cursor.fetchone()[0] == 3


def test_database_reinitialization_does_not_duplicate_seeds(tmp_path, monkeypatch):
    test_db = tmp_path / "tasks.db"
    monkeypatch.setattr(main, "DB_PATH", test_db)

    initialize_database()
    initialize_database()

    with sqlite3.connect(test_db) as connection:
        cursor = connection.cursor()
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

    with sqlite3.connect(main.DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute(
            "SELECT title, done FROM tasks WHERE id = ?",
            (response.json()["id"],),
        )
        assert cursor.fetchone() == ("Buy milk", 0)


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

    with sqlite3.connect(main.DB_PATH) as first_connection:
        first_cursor = first_connection.cursor()
        first_cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
        assert first_cursor.fetchone()[0] == "Persistent task"

    with sqlite3.connect(main.DB_PATH) as second_connection:
        second_cursor = second_connection.cursor()
        second_cursor.execute("SELECT title FROM tasks WHERE id = ?", (task_id,))
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
