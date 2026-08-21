import type { RunState } from "@/lib/workflow-types";

const globalForRuns = globalThis as typeof globalThis & {
  workflowRuns?: Map<string, RunState>;
};

export const workflowRuns = globalForRuns.workflowRuns ?? new Map<string, RunState>();

if (!globalForRuns.workflowRuns) {
  globalForRuns.workflowRuns = workflowRuns;
}

export function saveRun(run: RunState) {
  workflowRuns.set(run.runId, run);
}

export function getRun(runId: string) {
  return workflowRuns.get(runId);
}
