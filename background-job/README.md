# Background Job API

A small Express API for Week 6: the endpoint accepts slow report work quickly, Inngest runs the work in the background, and clients poll for status.

## Run

```powershell
npm install
npm run dev
```

The API listens on `http://localhost:3000`.

## Stage 0 Proof

```powershell
curl -i http://localhost:3000/health
```

Expected response: `200 OK` with `{"status":"ok"}`.
