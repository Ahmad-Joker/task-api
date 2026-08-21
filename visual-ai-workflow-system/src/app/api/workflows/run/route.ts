import { NextResponse } from "next/server";

import { inngest } from "@/inngest/client";
import { saveRun } from "@/lib/run-store";
import type { RunState, WorkflowGraph } from "@/lib/workflow-types";

type RunRequest = {
  graph: WorkflowGraph;
  input: string;
  startNodeId?: string;
};

export async function POST(request: Request) {
  const body = (await request.json()) as RunRequest;

  if (!body.graph?.nodes?.length) {
    return NextResponse.json({ error: "Graph must include at least one node" }, { status: 400 });
  }

  const startNodeId = body.startNodeId || body.graph.nodes[0].id;
  const runId = crypto.randomUUID();
  const queuedRun: RunState = {
    runId,
    status: "queued",
    order: [],
    logs: [],
    activeEdgeIds: [],
    startedAt: new Date().toISOString(),
  };
  saveRun(queuedRun);

  await inngest.send({
    name: "workflow/run.requested",
    data: {
      runId,
      graph: body.graph,
      input: body.input || "",
      startNodeId,
    },
  });

  return NextResponse.json({ runId });
}
