"use client";

import "@xyflow/react/dist/style.css";

import {
  addEdge,
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MarkerType,
  MiniMap,
  Position,
  ReactFlow,
  type Connection,
  type Edge,
  type EdgeChange,
  type Node,
  type NodeChange,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import {
  Activity,
  Braces,
  Download,
  FileJson,
  GitBranchPlus,
  History,
  Loader2,
  Play,
  Plus,
  Save,
  Trash2,
  Upload,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import type {
  RunState,
  WorkflowEdgeData,
  WorkflowGraph,
  WorkflowNodeData,
} from "@/lib/workflow-types";
import { cn } from "@/lib/utils";

type FlowNode = Node<WorkflowNodeData, "decision">;
type FlowEdge = Edge<WorkflowEdgeData>;

const storageKey = "ai-workflow-system.graph.v1";

const initialNodes: FlowNode[] = [
  {
    id: "node-support-check",
    type: "decision",
    position: { x: 80, y: 120 },
    data: {
      label: "Support Gate",
      prompt: "Is this message a support request?",
    },
  },
  {
    id: "node-support",
    type: "decision",
    position: { x: 480, y: 40 },
    data: {
      label: "Support Route",
      prompt: "Is the support issue urgent enough for engineering escalation?",
    },
  },
  {
    id: "node-sales",
    type: "decision",
    position: { x: 480, y: 260 },
    data: {
      label: "Sales Route",
      prompt: "Is this message from a buyer asking about pricing or plans?",
    },
  },
];

const initialEdges: FlowEdge[] = [
  {
    id: "edge-support-yes",
    source: "node-support-check",
    target: "node-support",
    label: "YES",
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed },
    data: { decision: "YES" },
  },
  {
    id: "edge-support-no",
    source: "node-support-check",
    target: "node-sales",
    label: "NO",
    type: "smoothstep",
    markerEnd: { type: MarkerType.ArrowClosed },
    data: { decision: "NO" },
  },
];

function DecisionNode({ data }: { data: WorkflowNodeData }) {
  return (
    <div
      className={cn(
        "w-64 rounded-lg border bg-zinc-950/95 p-3 shadow-2xl shadow-black/40 transition",
        data.active && "border-emerald-300 ring-2 ring-emerald-300/30",
        data.visited && !data.active && "border-sky-400/70",
        !data.active && !data.visited && "border-zinc-700",
      )}
    >
      <Handle
        type="target"
        position={Position.Left}
        className="!h-3 !w-3 !border-zinc-950 !bg-zinc-400"
      />
      <div className="mb-2 flex items-center justify-between gap-2">
        <div className="text-xs font-semibold uppercase tracking-[0.22em] text-emerald-200">
          {data.label}
        </div>
        {data.result && (
          <span
            className={cn(
              "rounded px-2 py-0.5 text-xs font-bold",
              data.result === "YES"
                ? "bg-emerald-300 text-zinc-950"
                : "bg-rose-400 text-zinc-950",
            )}
          >
            {data.result}
          </span>
        )}
      </div>
      <p className="line-clamp-4 text-sm leading-5 text-zinc-300">{data.prompt}</p>
      {data.error && <p className="mt-2 text-xs text-red-300">{data.error}</p>}
      <Handle
        type="source"
        position={Position.Right}
        className="!h-3 !w-3 !border-zinc-950 !bg-emerald-300"
      />
    </div>
  );
}

const nodeTypes = { decision: DecisionNode };

function graphFromFlow(nodes: FlowNode[], edges: FlowEdge[]): WorkflowGraph {
  return {
    nodes: nodes.map((node) => ({
      id: node.id,
      type: node.type,
      position: node.position,
      data: {
        label: node.data.label,
        prompt: node.data.prompt,
      },
    })),
    edges: edges.map((edge) => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: edge.type,
      label: String(edge.label || edge.data?.decision || "YES"),
      animated: edge.animated,
      data: { decision: edge.data?.decision || "YES" },
    })),
  };
}

function flowFromGraph(graph: WorkflowGraph) {
  return {
    nodes: graph.nodes.map((node) => ({
      ...node,
      type: "decision" as const,
    })),
    edges: graph.edges.map((edge) => ({
      ...edge,
      type: "smoothstep",
      markerEnd: { type: MarkerType.ArrowClosed },
      label: edge.data.decision,
    })),
  };
}

export default function Home() {
  const [nodes, setNodes, onNodesChange] = useNodesState<FlowNode>(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState<FlowEdge>(initialEdges);
  const [selectedNodeId, setSelectedNodeId] = useState(initialNodes[0].id);
  const [edgeMode, setEdgeMode] = useState<"YES" | "NO">("YES");
  const [input, setInput] = useState(
    "I cannot log in and the export button is broken before our demo.",
  );
  const [run, setRun] = useState<RunState | null>(null);
  const [history, setHistory] = useState<RunState[]>([]);
  const [importText, setImportText] = useState("");
  const [error, setError] = useState("");
  const pollRef = useRef<number | null>(null);

  const selectedNode = useMemo(
    () => nodes.find((node) => node.id === selectedNodeId) || nodes[0],
    [nodes, selectedNodeId],
  );

  const decoratedNodes = useMemo(() => {
    if (!run) return nodes;
    return nodes.map((node) => {
      const log = run.logs.find((item) => item.nodeId === node.id);
      return {
        ...node,
        data: {
          ...node.data,
          active: run.activeNodeId === node.id,
          visited: run.order.includes(node.id),
          result: log?.answer,
        },
      };
    });
  }, [nodes, run]);

  const decoratedEdges = useMemo(() => {
    const activeEdgeIds = new Set(run?.activeEdgeIds || []);
    return edges.map((edge) => ({
      ...edge,
      animated: activeEdgeIds.has(edge.id),
      style: {
        stroke: activeEdgeIds.has(edge.id)
          ? edge.data?.decision === "YES"
            ? "#6ee7b7"
            : "#fb7185"
          : "#52525b",
        strokeWidth: activeEdgeIds.has(edge.id) ? 3 : 1.5,
      },
      label: edge.data?.decision || "YES",
      markerEnd: { type: MarkerType.ArrowClosed },
    }));
  }, [edges, run]);

  useEffect(() => {
    const saved = window.localStorage.getItem(storageKey);
    if (!saved) return;
    try {
      const graph = JSON.parse(saved) as WorkflowGraph;
      const restored = flowFromGraph(graph);
      window.queueMicrotask(() => {
        setNodes(restored.nodes);
        setEdges(restored.edges);
        setSelectedNodeId(restored.nodes[0]?.id || "");
      });
    } catch {
      window.localStorage.removeItem(storageKey);
    }
  }, [setEdges, setNodes]);

  useEffect(() => {
    return () => {
      if (pollRef.current) window.clearInterval(pollRef.current);
    };
  }, []);

  const handleNodesChange = useCallback(
    (changes: NodeChange<FlowNode>[]) => onNodesChange(changes),
    [onNodesChange],
  );

  const handleEdgesChange = useCallback(
    (changes: EdgeChange<FlowEdge>[]) => onEdgesChange(changes),
    [onEdgesChange],
  );

  const onConnect = useCallback(
    (connection: Connection) => {
      const id = `edge-${connection.source}-${connection.target}-${edgeMode}-${Date.now()}`;
      setEdges((current) =>
        addEdge(
          {
            ...connection,
            id,
            type: "smoothstep",
            label: edgeMode,
            markerEnd: { type: MarkerType.ArrowClosed },
            data: { decision: edgeMode },
          },
          current,
        ),
      );
    },
    [edgeMode, setEdges],
  );

  function addDecisionNode() {
    const id = `node-${Date.now()}`;
    setNodes((current) => [
      ...current,
      {
        id,
        type: "decision",
        position: { x: 120 + current.length * 40, y: 120 + current.length * 30 },
        data: {
          label: `Decision ${current.length + 1}`,
          prompt: "Does this condition pass?",
        },
      },
    ]);
    setSelectedNodeId(id);
  }

  function updateSelectedNode(update: Partial<WorkflowNodeData>) {
    setNodes((current) =>
      current.map((node) =>
        node.id === selectedNodeId
          ? { ...node, data: { ...node.data, ...update } }
          : node,
      ),
    );
  }

  function deleteSelectedNode() {
    if (!selectedNodeId) return;
    setNodes((current) => current.filter((node) => node.id !== selectedNodeId));
    setEdges((current) =>
      current.filter(
        (edge) => edge.source !== selectedNodeId && edge.target !== selectedNodeId,
      ),
    );
    setSelectedNodeId(nodes.find((node) => node.id !== selectedNodeId)?.id || "");
  }

  function saveWorkflow() {
    window.localStorage.setItem(storageKey, JSON.stringify(graphFromFlow(nodes, edges)));
  }

  function loadWorkflow() {
    const saved = window.localStorage.getItem(storageKey);
    if (!saved) return;
    const restored = flowFromGraph(JSON.parse(saved));
    setNodes(restored.nodes);
    setEdges(restored.edges);
    setSelectedNodeId(restored.nodes[0]?.id || "");
  }

  function exportWorkflow() {
    setImportText(JSON.stringify(graphFromFlow(nodes, edges), null, 2));
  }

  function importWorkflow() {
    try {
      const graph = JSON.parse(importText) as WorkflowGraph;
      const restored = flowFromGraph(graph);
      setNodes(restored.nodes);
      setEdges(restored.edges);
      setSelectedNodeId(restored.nodes[0]?.id || "");
      setError("");
    } catch {
      setError("Import failed: JSON is not a workflow graph.");
    }
  }

  async function runWorkflow() {
    setError("");
    const response = await fetch("/api/workflows/run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        graph: graphFromFlow(nodes, edges),
        input,
        startNodeId: nodes[0]?.id,
      }),
    });
    const payload = await response.json();
    if (!response.ok) {
      setError(payload.error || "Could not start workflow.");
      return;
    }

    const runId = payload.runId as string;
    const poll = async () => {
      const runResponse = await fetch(`/api/runs/${runId}`);
      if (!runResponse.ok) return;
      const nextRun = (await runResponse.json()) as RunState;
      setRun(nextRun);
      if (nextRun.status === "completed" || nextRun.status === "failed") {
        if (pollRef.current) window.clearInterval(pollRef.current);
        pollRef.current = null;
        setHistory((current) => [nextRun, ...current].slice(0, 6));
      }
    };
    await poll();
    pollRef.current = window.setInterval(poll, 700);
  }

  const isRunning = run?.status === "queued" || run?.status === "running";

  return (
    <main className="min-h-screen bg-[#090b0b] text-zinc-100">
      <div className="grid min-h-screen grid-cols-[minmax(0,1fr)_380px]">
        <section className="relative">
          <header className="absolute left-5 right-5 top-5 z-10 flex items-center justify-between rounded-lg border border-zinc-800 bg-zinc-950/90 px-4 py-3 backdrop-blur">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-emerald-200">
                Inngest decision graph
              </p>
              <h1 className="text-xl font-semibold tracking-tight">
                Visual AI Workflow System
              </h1>
            </div>
            <div className="flex items-center gap-2">
              <Button variant="secondary" size="sm" onClick={addDecisionNode}>
                <Plus className="h-4 w-4" />
                Node
              </Button>
              <Button
                variant={edgeMode === "YES" ? "default" : "secondary"}
                size="sm"
                onClick={() => setEdgeMode("YES")}
              >
                YES edge
              </Button>
              <Button
                variant={edgeMode === "NO" ? "default" : "secondary"}
                size="sm"
                onClick={() => setEdgeMode("NO")}
              >
                NO edge
              </Button>
              <Button onClick={runWorkflow} disabled={isRunning || nodes.length === 0}>
                {isRunning ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                Run
              </Button>
            </div>
          </header>

          <ReactFlow
            nodes={decoratedNodes}
            edges={decoratedEdges}
            nodeTypes={nodeTypes}
            onNodesChange={handleNodesChange}
            onEdgesChange={handleEdgesChange}
            onConnect={onConnect}
            onNodeClick={(_, node) => setSelectedNodeId(node.id)}
            fitView
            className="bg-[#090b0b]"
          >
            <Background color="#1f2937" gap={28} variant={BackgroundVariant.Dots} />
            <Controls className="!border-zinc-800 !bg-zinc-950 !text-zinc-100" />
            <MiniMap
              className="!border !border-zinc-800 !bg-zinc-950"
              nodeColor="#6ee7b7"
              maskColor="rgba(9,11,11,0.75)"
            />
          </ReactFlow>
        </section>

        <aside className="flex h-screen flex-col border-l border-zinc-800 bg-zinc-950">
          <div className="border-b border-zinc-800 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-200">
              <GitBranchPlus className="h-4 w-4 text-emerald-300" />
              Node editor
            </div>
            {selectedNode ? (
              <div className="space-y-3">
                <Input
                  value={selectedNode.data.label}
                  onChange={(event) => updateSelectedNode({ label: event.target.value })}
                />
                <Textarea
                  value={selectedNode.data.prompt}
                  onChange={(event) => updateSelectedNode({ prompt: event.target.value })}
                />
                <Button variant="danger" size="sm" onClick={deleteSelectedNode}>
                  <Trash2 className="h-4 w-4" />
                  Delete node
                </Button>
              </div>
            ) : (
              <p className="text-sm text-zinc-500">Select a node to edit its prompt.</p>
            )}
          </div>

          <div className="border-b border-zinc-800 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-200">
              <Activity className="h-4 w-4 text-emerald-300" />
              Execution input
            </div>
            <Textarea value={input} onChange={(event) => setInput(event.target.value)} />
            {error && <p className="mt-2 text-sm text-red-300">{error}</p>}
          </div>

          <div className="grid grid-cols-4 gap-2 border-b border-zinc-800 p-4">
            <Button variant="secondary" size="sm" onClick={saveWorkflow} title="Save locally">
              <Save className="h-4 w-4" />
            </Button>
            <Button variant="secondary" size="sm" onClick={loadWorkflow} title="Load local">
              <Upload className="h-4 w-4" />
            </Button>
            <Button variant="secondary" size="sm" onClick={exportWorkflow} title="Export JSON">
              <Download className="h-4 w-4" />
            </Button>
            <Button variant="secondary" size="sm" onClick={importWorkflow} title="Import JSON">
              <FileJson className="h-4 w-4" />
            </Button>
          </div>

          <div className="border-b border-zinc-800 p-4">
            <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-200">
              <Braces className="h-4 w-4 text-emerald-300" />
              JSON import/export
            </div>
            <Textarea
              className="min-h-32 font-mono text-xs"
              value={importText}
              onChange={(event) => setImportText(event.target.value)}
              placeholder="Exported workflow JSON appears here."
            />
          </div>

          <div className="min-h-0 flex-1 overflow-y-auto p-4">
            <div className="mb-3 flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-zinc-200">
                <Activity className="h-4 w-4 text-emerald-300" />
                Execution logs
              </div>
              <span className="text-xs uppercase tracking-[0.2em] text-zinc-500">
                {run?.status || "idle"}
              </span>
            </div>
            <div className="space-y-2">
              {(run?.logs || []).map((log, index) => (
                <div
                  key={`${log.nodeId}-${index}`}
                  className="rounded-md border border-zinc-800 bg-zinc-900/70 p-3"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-xs text-zinc-500">{log.nodeId}</span>
                    <span
                      className={cn(
                        "rounded px-2 py-0.5 text-xs font-bold",
                        log.answer === "YES"
                          ? "bg-emerald-300 text-zinc-950"
                          : "bg-rose-400 text-zinc-950",
                      )}
                    >
                      {log.answer}
                    </span>
                  </div>
                  <p className="mt-2 text-sm text-zinc-300">{log.prompt}</p>
                  <p className="mt-2 text-xs text-zinc-500">
                    Next: {log.nextNodeId || "end"}
                  </p>
                </div>
              ))}
              {run?.error && <p className="text-sm text-red-300">{run.error}</p>}
              {!run?.logs.length && (
                <p className="rounded-md border border-dashed border-zinc-800 p-4 text-sm text-zinc-500">
                  Run the graph to see each AI decision step.
                </p>
              )}
            </div>

            <div className="mt-6">
              <div className="mb-3 flex items-center gap-2 text-sm font-semibold text-zinc-200">
                <History className="h-4 w-4 text-emerald-300" />
                Execution history
              </div>
              <div className="space-y-2">
                {history.map((item) => (
                  <button
                    key={item.runId}
                    className="w-full rounded-md border border-zinc-800 bg-zinc-900/50 p-3 text-left text-sm hover:border-emerald-300"
                    onClick={() => setRun(item)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-mono text-xs text-zinc-400">
                        {item.runId.slice(0, 8)}
                      </span>
                      <span>{item.status}</span>
                    </div>
                    <p className="mt-1 text-xs text-zinc-500">
                      {item.order.length} node{item.order.length === 1 ? "" : "s"} visited
                    </p>
                  </button>
                ))}
              </div>
            </div>
          </div>
        </aside>
      </div>
    </main>
  );
}
