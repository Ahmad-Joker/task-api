import { askYesNo } from "@/lib/ai";
import { saveRun } from "@/lib/run-store";
import type {
  ExecutionLog,
  RunState,
  WorkflowEdge,
  WorkflowGraph,
  WorkflowNode,
} from "@/lib/workflow-types";
import { inngest } from "@/inngest/client";

type WorkflowRunEvent = {
  name: "workflow/run.requested";
  data: {
    runId: string;
    graph: WorkflowGraph;
    input: string;
    startNodeId: string;
  };
};

function findDecisionEdge(edges: WorkflowEdge[], nodeId: string, answer: "YES" | "NO") {
  return edges.find(
    (edge) => edge.source === nodeId && edge.data?.decision === answer,
  );
}

function updateRun(run: RunState) {
  saveRun({ ...run, logs: [...run.logs], order: [...run.order], activeEdgeIds: [...run.activeEdgeIds] });
}

export const runWorkflow = inngest.createFunction(
  {
    id: "run-visual-ai-workflow",
    triggers: [{ event: "workflow/run.requested" }],
  },
  async ({ event, step }) => {
    const typedEvent = event as unknown as WorkflowRunEvent;
    const { runId, graph, input, startNodeId } = typedEvent.data;
    const run: RunState = {
      runId,
      status: "running",
      order: [],
      logs: [],
      activeNodeId: startNodeId,
      activeEdgeIds: [],
      startedAt: new Date().toISOString(),
    };
    updateRun(run);

    try {
      let currentNodeId: string | null = startNodeId;
      const visited = new Set<string>();

      while (currentNodeId) {
        if (visited.has(currentNodeId)) {
          throw new Error(`Workflow loop detected at node ${currentNodeId}`);
        }
        visited.add(currentNodeId);

        const node = graph.nodes.find((item: WorkflowNode) => item.id === currentNodeId);
        if (!node) {
          throw new Error(`Node ${currentNodeId} was not found`);
        }

        run.activeNodeId = node.id;
        updateRun(run);

        const answer = await step.run(`ai-decision-${node.id}`, async () =>
          askYesNo(node.data.prompt, input),
        );

        const edge = findDecisionEdge(graph.edges, node.id, answer);
        const log: ExecutionLog = {
          nodeId: node.id,
          prompt: node.data.prompt,
          answer,
          nextNodeId: edge?.target ?? null,
          timestamp: new Date().toISOString(),
        };

        run.order.push(node.id);
        run.logs.push(log);
        if (edge) {
          run.activeEdgeIds.push(edge.id);
        }
        updateRun(run);

        currentNodeId = edge?.target ?? null;
      }

      run.status = "completed";
      run.activeNodeId = undefined;
      run.finishedAt = new Date().toISOString();
      updateRun(run);
      return run;
    } catch (error) {
      run.status = "failed";
      run.error = error instanceof Error ? error.message : "Unknown workflow error";
      run.finishedAt = new Date().toISOString();
      updateRun(run);
      throw error;
    }
  },
);

export const functions = [runWorkflow];
