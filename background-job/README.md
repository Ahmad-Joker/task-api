# Background Job API

A small Express API for Week 6: the endpoint accepts slow report work quickly, Inngest runs the work in the background, and clients poll for status.

## Run

```powershell
npm install
npm run dev
```

The API listens on `http://localhost:3000`.

In a second terminal, start the Inngest Dev Server:

```powershell
npx inngest-cli@latest dev -u http://localhost:3000/api/inngest
```

Open the dashboard at `http://localhost:8288` and invoke `say-hello`.

## Stage 0 Proof

```powershell
curl -i http://localhost:3000/health
```

Expected response: `200 OK` with `{"status":"ok"}`.

## Stage 1 Proof

The Inngest dashboard should show `say-hello` running the `wait-five-seconds` step and finishing with `Hello from the background!`.

## Stage 2 Proof

Create a report:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:3000/reports" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"topic":"cats"}'
```

Expected immediate response:

```json
{
  "id": "generated-id",
  "status": "pending"
}
```

Poll immediately, then again after about 10 seconds:

```powershell
Invoke-RestMethod http://localhost:3000/reports/generated-id
```

The first response is `pending`; the later response is `done` with a generated `result`.

## Stage 3 Proof

Bad input is rejected at the door:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:3000/reports" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{}'
```

Expected response: `400 Bad Request` with `{"error":"topic is required"}`.

To watch retries, create a report with the special topic:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:3000/reports" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"topic":"fail"}'
```

Open the `make-report` run in the Inngest dashboard. It fails inside `build-report`, retries two more times, then ends `Failed` after 3 total attempts.

Stage 3 sentence: missing topic is a bad request and should not be retried; `topic: "fail"` is accepted work that fails later, so the background worker retries it automatically.

## Stage 4 Proof

The `heartbeat` function runs from the cron expression `* * * * *`, which means every minute. In the dashboard, it should show one `log-report-summary` step per run and return a line like:

```text
heartbeat: pending=0 done=1 failed=1
```

Stage 4 sentences:

`0 8 * * *` runs every day at 08:00.

`0 22 * * 0` runs every Sunday at 22:00.
