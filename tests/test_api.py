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


def test_swagger_and_openapi_are_accessible():
    docs_response = client.get("/docs")
    openapi_response = client.get("/openapi.json")

    assert docs_response.status_code == 200
    assert openapi_response.status_code == 200
    assert openapi_response.json()["info"]["title"] == "Task API"
