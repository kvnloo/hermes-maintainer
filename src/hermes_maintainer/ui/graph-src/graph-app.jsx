import React, { useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Background,
  BackgroundVariant,
  Controls,
  Handle,
  MiniMap,
  MarkerType,
  Position,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";

const ROLE_LANE = {
  canonical_problem: 0,
  member: 0,
  provenance: 1,
  survivor: 2,
  active_implementation: 2,
  donor: 3,
  stacked_child: 3,
  superseded: 4,
};

const EDGE_COLOR = {
  fixes: "#34d399",
  supersedes: "#ffbd38",
  duplicate_of: "#ffe6cb",
  possible_duplicate: "#ffe6cb",
  same_root_cause: "#5eead4",
  stacked_on: "#ffe6cb",
  incorporates_commit: "#fbbf24",
  complements: "#99f6e4",
  related: "#ffe6cb",
};

let current = { nodes: [], relations: [], campaign: null, source: "live" };
const listeners = new Set();

export function setGraph(payload) {
  current = payload || { nodes: [], relations: [], campaign: null };
  listeners.forEach((fn) => fn(current));
}

export function mount(container, options = {}) {
  const root = createRoot(container);
  root.render(<GraphApp onSelect={options.onSelect} />);
  return { setGraph, unmount: () => root.unmount() };
}

function useGraphPayload() {
  const [payload, setPayload] = useState(current);
  useEffect(() => {
    listeners.add(setPayload);
    setPayload(current);
    return () => listeners.delete(setPayload);
  }, []);
  return payload;
}

function TicketNode({ data, selected }) {
  return (
    <div className={`ticket-node kind-${data.kind} role-${data.role || "member"}${selected ? " is-selected" : ""}`}>
      <Handle type="target" position={Position.Left} />
      <div className="ticket-kicker">
        <span>{data.kind} #{data.number}</span>
        <span>{(data.role || "member").replaceAll("_", " ")}</span>
      </div>
      <div className="ticket-title">{data.title}</div>
      <div className="ticket-meta">
        {data.state || "open"}
        {data.author ? ` · ${data.author}` : ""}
      </div>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

const nodeTypes = { ticket: TicketNode };

function layoutNodes(rawNodes) {
  const groups = new Map();
  for (const node of rawNodes) {
    const key = node.campaign_id || "graph";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(node);
  }
  const out = [];
  let groupY = 0;
  for (const members of groups.values()) {
    const lanes = new Map();
    for (const member of members) {
      const lane = ROLE_LANE[member.role] ?? (member.kind === "issue" ? 0 : 2);
      if (!lanes.has(lane)) lanes.set(lane, []);
      lanes.get(lane).push(member);
    }
    let tallest = 0;
    for (const [lane, laneNodes] of [...lanes.entries()].sort((a, b) => a[0] - b[0])) {
      laneNodes.forEach((node, index) => {
        const y = groupY + index * 108;
        tallest = Math.max(tallest, (index + 1) * 108);
        out.push({
          id: node.id,
          type: "ticket",
          position: { x: lane * 300, y },
          data: node,
        });
      });
    }
    groupY += Math.max(tallest, 120) + 48;
  }
  return out;
}

function toEdges(relations) {
  return (relations || []).map((rel, index) => {
    const color = EDGE_COLOR[rel.relation_type] || "#ffe6cb";
    const dashed = ["possible_duplicate", "related", "similar_to"].includes(rel.relation_type);
    return {
      id: rel.id ? String(rel.id) : `${rel.src_id}-${rel.relation_type}-${rel.dst_id}-${index}`,
      source: rel.src_id,
      target: rel.dst_id,
      label: rel.relation_type.replaceAll("_", " "),
      markerEnd: { type: MarkerType.ArrowClosed, color },
      style: { stroke: color, strokeWidth: 1.5, strokeDasharray: dashed ? "6 4" : undefined },
      labelStyle: { fill: color, fontSize: 11 },
      data: rel,
    };
  });
}

function GraphApp({ onSelect }) {
  const payload = useGraphPayload();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  useEffect(() => {
    setNodes(layoutNodes(payload.nodes || []));
    setEdges(toEdges(payload.relations || []));
  }, [payload, setEdges, setNodes]);

  const onNodeClick = useCallback(
    (_event, node) => {
      if (onSelect) onSelect(node.data, payload);
    },
    [onSelect, payload],
  );

  const onPaneClick = useCallback(() => {
    if (onSelect) onSelect(null, payload);
  }, [onSelect, payload]);

  const nodeColor = useCallback((node) => {
    if (node.data?.kind === "issue") return "#ffe6cb";
    if (node.data?.role === "survivor") return "#34d399";
    return "#5eead4";
  }, []);

  const empty = !payload.nodes || payload.nodes.length === 0;

  const defaultEdgeOptions = useMemo(
    () => ({ type: "default", animated: false }),
    [],
  );

  if (empty) {
    return (
      <div className="graph-empty">
        No campaign graph yet. Run <code>hermes-maintainer scan</code> and
        <code>analyze</code>, or load the seed canvas.
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      onNodeClick={onNodeClick}
      onPaneClick={onPaneClick}
      nodeTypes={nodeTypes}
      fitView
      colorMode="dark"
      nodesConnectable={false}
      elementsSelectable
      defaultEdgeOptions={defaultEdgeOptions}
      minZoom={0.2}
      maxZoom={1.6}
      attributionPosition="bottom-right"
    >
      <Background variant={BackgroundVariant.Dots} gap={18} size={1} color="rgba(255,230,203,0.18)" />
      <Controls showInteractive={false} />
      <MiniMap nodeColor={nodeColor} maskColor="rgba(4,28,28,0.72)" />
    </ReactFlow>
  );
}

if (typeof window !== "undefined") {
  window.HermesGraph = { mount, setGraph };
}
