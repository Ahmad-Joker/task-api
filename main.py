from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, Request
from fastapi.responses import JSONResponse, Response
from pydantic import ValidationError

from database import (
    create_task as create_task_in_database,
    delete_task as delete_task_from_database,
    get_all_tasks,
    get_task_by_id,
    initialize_database,
    update_task as update_task_in_database,
)
from auth import (
    AuthServiceError,
    InvalidCredentialsError,
    InvalidTokenError,
    get_current_user,
    login_user,
    logout_user,
    signup_user,
    validate_email,
    validate_password,
)
from src.llm.schema import TriageInput, TriageOutput, stub_triage_response


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="Task API",
    version="1.0",
    description="A beginner-friendly PostgreSQL-backed Task CRUD API built with FastAPI.",
    lifespan=lifespan,
)


@app.exception_handler(InvalidTokenError)
def invalid_token_exception_handler(request: Request, exc: InvalidTokenError):
    return unauthorized(str(exc))


def find_task(task_id: int):
    return get_task_by_id(task_id)


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


def validation_bad_request(exc: ValidationError):
    first_error = exc.errors()[0]
    field = ".".join(str(part) for part in first_error["loc"])
    return bad_request(f"{field}: {first_error['msg']}")


def unauthorized(message: str):
    return JSONResponse(status_code=401, content={"error": message})


def validate_auth_body(body):
    if body is None:
        return None, None, bad_request("Email and password are required")

    email = body.get("email")
    password = body.get("password")

    if email is None:
        return None, None, bad_request("Email is required")
    if password is None:
        return None, None, bad_request("Password is required")

    email = validate_email(email)
    if email is None:
        return None, None, bad_request("Valid email is required")

    password = validate_password(password)
    if password is None:
        return None, None, bad_request("Password must be at least 8 characters")

    return email, password, None


@app.post(
    "/auth/signup",
    status_code=201,
    tags=["Authentication"],
    summary="Sign up",
    description="Creates a Supabase Auth user with an email and password.",
)
async def signup(request: Request):
    body = await read_json_body(request)
    email, password, error = validate_auth_body(body)
    if error is not None:
        return error

    try:
        user = signup_user(email, password)
    except AuthServiceError:
        return bad_request("Could not sign up user")

    return {"user": user}


@app.post(
    "/auth/login",
    tags=["Authentication"],
    summary="Log in",
    description="Authenticates a Supabase Auth user and returns bearer tokens.",
)
async def login(request: Request):
    body = await read_json_body(request)
    email, password, error = validate_auth_body(body)
    if error is not None:
        return error

    try:
        return login_user(email, password)
    except InvalidCredentialsError:
        return unauthorized("Invalid login credentials")


@app.get(
    "/public/info",
    tags=["Public"],
    summary="Read public info",
    description="Returns public information without requiring authentication.",
)
def public_info():
    return {"message": "Welcome stranger! This info is public."}


@app.get(
    "/protected/profile",
    tags=["Protected"],
    summary="Read protected profile",
    description="Requires a valid Authorization: Bearer access token.",
)
def protected_profile(user=Depends(get_current_user)):
    return user


@app.get(
    "/protected/dashboard",
    tags=["Protected"],
    summary="Read protected dashboard",
    description="Uses the shared authentication dependency.",
)
def protected_dashboard(user=Depends(get_current_user)):
    return {
        "message": "Welcome to your dashboard",
        "user_id": user["id"],
    }


@app.post(
    "/auth/logout",
    status_code=204,
    tags=["Authentication"],
    summary="Log out",
    description="Requires a valid bearer token and signs out through Supabase.",
)
def logout(user=Depends(get_current_user)):
    logout_user()
    return Response(status_code=204)


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


@app.post(
    "/triage",
    tags=["LLM"],
    summary="Triage a support message",
    description="Classifies a messy support message into a validated routing decision.",
    response_model=TriageOutput,
)
async def triage_message(request: Request):
    body = await read_json_body(request)
    if body is None:
        return bad_request("text: Field required")

    try:
        triage_input = TriageInput.model_validate(body)
    except ValidationError as exc:
        return validation_bad_request(exc)

    _ = triage_input
    return stub_triage_response()


@app.get(
    "/tasks",
    tags=["Tasks"],
    summary="List all tasks",
    description="Returns every task currently stored in the PostgreSQL database.",
    response_description="Complete task list",
)
def read_tasks():
    return get_all_tasks()


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

    return create_task_in_database(title)


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

    return update_task_in_database(task_id, task["title"], task["done"])


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

    delete_task_from_database(task_id)
    return Response(status_code=204)
