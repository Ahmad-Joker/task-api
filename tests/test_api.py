from fastapi.testclient import TestClient
import pytest

from main import app, reset_tasks


client = TestClient(app)


@pytest.fixture(autouse=True)
def reset_task_list():
    reset_tasks()


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
