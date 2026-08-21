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
