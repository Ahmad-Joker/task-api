export type Decision = "YES" | "NO";

export type WorkflowNodeData = {
  label: string;
  prompt: string;
  active?: boolean;
  result?: Decision;
  visited?: boolean;
  error?: string;
};

export type WorkflowEdgeData = {
  decision: Decision;
  active?: boolean;
};

export type WorkflowNode = {
  id: string;
  type?: string;
  position: { x: number; y: number };
  data: WorkflowNodeData;
};

export type WorkflowEdge = {
  id: string;
  source: string;
  target: string;
  type?: string;
  animated?: boolean;
  label?: string;
  data: WorkflowEdgeData;
};

export type WorkflowGraph = {
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
};

export type ExecutionLog = {
  nodeId: string;
  prompt: string;
  answer: Decision;
  nextNodeId: string | null;
  timestamp: string;
};

export type RunState = {
  runId: string;
  status: "queued" | "running" | "completed" | "failed";
  order: string[];
  logs: ExecutionLog[];
  activeNodeId?: string;
  activeEdgeIds: string[];
  error?: string;
  startedAt: string;
  finishedAt?: string;
};
