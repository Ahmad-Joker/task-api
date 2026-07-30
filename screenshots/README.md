# Screenshot Instructions

This folder is reserved for assignment screenshots.

## Swagger UI Screenshot

The Week 2 Swagger UI screenshot should be saved as:

```text
screenshots/swagger-ui.png
```

To create or update it:

1. Start the API from the project root:

   ```bash
   uvicorn main:app --reload
   ```

2. Open Swagger UI in your browser:

   ```text
   http://localhost:8000/docs
   ```

3. Capture the page with your operating system screenshot tool.

4. Save the image in this folder as:

   ```text
   screenshots/swagger-ui.png
   ```

## Database Browser Screenshot

The Week 3 database screenshot should be saved as:

```text
screenshots/database-browser.png
```

To create it:

1. Start the API from the project root so `tasks.db` is created:

   ```bash
   uvicorn main:app --reload
   ```

2. Open DB Browser for SQLite.

3. Choose **Open Database**.

4. Select the generated database file:

   ```text
   tasks.db
   ```

5. Select the **Browse Data** tab.

6. In the table dropdown, select:

   ```text
   tasks
   ```

7. Capture the DB Browser window with your operating system screenshot tool.

8. Save the image in this folder as:

   ```text
   screenshots/database-browser.png
   ```

The database screenshot image is not committed until you create it manually.

## PostgreSQL Data Screenshot

Assignment A3 asks for a PostgreSQL data screenshot saved as:

```text
screenshots/postgres-data.png
```

You can capture this from `psql`, pgAdmin, or DBeaver.

### Option 1: psql

1. Start the stack:

   ```bash
   docker compose up -d --build
   ```

2. Open `psql` inside the PostgreSQL container:

   ```bash
   docker compose exec db psql -U postgres -d tasks
   ```

3. Run:

   ```sql
   \dt
   SELECT * FROM tasks;
   ```

4. Take a screenshot showing the `tasks` table and task rows.

5. Save it as:

   ```text
   screenshots/postgres-data.png
   ```

### Option 2: pgAdmin or DBeaver

1. Connect to PostgreSQL using:

   ```text
   Host: localhost
   Port: 5432
   Database: tasks
   User: postgres
   Password: dev
   ```

2. Open the `tasks` table.

3. Capture the visible rows.

4. Save the image as:

   ```text
   screenshots/postgres-data.png
   ```

Do not claim the PostgreSQL screenshot exists until `screenshots/postgres-data.png` has actually been created.

## Swagger Auth Screenshot

Assignment A4 asks for a Swagger authentication screenshot saved as:

```text
screenshots/swagger-auth.png
```

To create it:

1. Add real Supabase values to `.env`.

2. Start the API:

   ```bash
   docker compose up --build
   ```

3. Open Swagger:

   ```text
   http://localhost:8000/docs
   ```

4. Use `POST /auth/signup` to create a practice user.

5. Use `POST /auth/login` with the same email and password.

6. Copy the `access_token` from the login response.

7. Click **Authorize** near the top of Swagger.

8. Paste the access token into the HTTPBearer field.

9. Call `GET /protected/profile`.

10. Capture Swagger showing the protected route lock icon and a successful `200` response.

11. Save the image as:

    ```text
    screenshots/swagger-auth.png
    ```

Do not include full real access tokens or refresh tokens in screenshots if they are visible.
