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
