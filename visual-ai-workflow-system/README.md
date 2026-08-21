# Visual AI Workflow System

A Next.js workflow builder where every node is an AI decision step that returns exactly `YES` or `NO`. The editor is rendered with React Flow, execution is triggered through Inngest, and the UI polls run state to visualize the active node, active edge, logs, and history.

## Stack

- Next.js + React + TypeScript
- React Flow (`@xyflow/react`)
- Inngest
- OpenAI SDK
- Tailwind CSS
- Shadcn-style local UI primitives

## Setup

```powershell
npm install
Copy-Item .env.example .env
npm run dev
```

In another terminal:

```powershell
npm run inngest
```

Open:

- Frontend: http://localhost:3000
- Inngest dev server: usually http://localhost:8288

## Environment

```text
AI_STUB=1
INNGEST_DEV=1
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini
INNGEST_EVENT_KEY=
INNGEST_SIGNING_KEY=
```

`AI_STUB=1` uses a deterministic local YES/NO heuristic so the full workflow can be tested without spending tokens. Set `AI_STUB=0` and provide `OPENAI_API_KEY` to call OpenAI.

## Features

- React Flow canvas
- Add decision nodes
- Connect nodes with YES or NO edges
- Edit node labels and prompts
- Store workflow state in local storage
- JSON export/import
- Inngest-powered workflow execution
- One Inngest step per decision node
- AI YES/NO branching logic
- Execution order tracking
- Visual active node and animated active edge
- Execution logs panel
- Execution history
- Error handling for missing nodes and loops

## How Execution Works

1. Click **Run** in the editor.
2. The frontend posts the graph to `/api/workflows/run`.
3. The API stores a queued run and sends `workflow/run.requested` to Inngest.
4. The Inngest function executes each node with `step.run(...)`.
5. Each node prompt is sent to the AI decision helper.
6. The answer must be `YES` or `NO`.
7. The matching edge chooses the next node.
8. The frontend polls `/api/runs/:runId` and visualizes the path.

## Development Notes

The local run store is in memory, which is ideal for the Inngest dev server and demo workflow execution. For production, replace it with Redis, Postgres, or another persistent store.
