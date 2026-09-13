import architecture from "./architecture.json";

export const ZOOM_STOPS = [0.4, 0.75, 1, 1.5, 2];
export const HIT_MIN_PX = 44;
export const NODE_MIN_HEIGHT = HIT_MIN_PX / 0.4;
export const NODE_MIN_WIDTH = 248;
export const NODE_STEP_Y = 128;
export const LANE_STEP_X = 268;
export const FAMILY_GAP_X = 72;
export const FAMILY_GAP_Y = 48;
export const LANE_WRAP_ROWS = 8;
export const MAX_VISIBLE_NODES = 60;

export const FLOW_GESTURES = {
  panOnScroll: true,
  panOnScrollMode: "free",
  panOnScrollSpeed: 0.9,
  zoomOnPinch: true,
  zoomOnScroll: true,
  preventScrolling: true,
  minZoom: 0.4,
  maxZoom: 2,
  nodesFocusable: true,
  edgesFocusable: true,
  nodesConnectable: false,
  nodesDraggable: false,
  elementsSelectable: true,
  nodeClickDistance: 8,
  paneClickDistance: 6,
  panOnDrag: true,
  zoomOnDoubleClick: true,
  autoPanOnNodeFocus: true,
  deleteKeyCode: null,
  touchAction: "none",
};

export const EDGE_COLOR = {
  feeds: "#ffbd38",
  writes: "#ffe6cb",
  clusters: "#34d399",
  suggests: "#ffe6cb",
  decomposes: "#fbbf24",
  requires: "#fb7185",
  shows: "#5eead4",
  emits: "#c4b5fd",
  example: "#ffbd38",
  implemented_in: "#99f6e4",
  protects: "#fbbf24",
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

const KIND_LANE = {
  campaign: 0,
  invariant: 1,
  issue: 2,
  pr: 3,
  file: 4,
  subsystem: 0,
};

export function architectureGraph() {
  return {
    graph: architecture.graph,
    source: architecture.source,
    campaign: architecture.campaign,
    nodes: architecture.nodes.map((node) => ({ ...node })),
    relations: architecture.relations.map((rel) => ({ ...rel })),
  };
}

export const ARCHITECTURE_FOCUS_ID = "arch:sqlite-backlog";
export const NODE_CENTER = { x: 124, y: 55 };

export function hitSizeForZoom(_zoom) {
  return NODE_MIN_HEIGHT;
}

export function edgeLabelHitForZoom(zoom) {
  const z = Math.max(Number(zoom) || 1, FLOW_GESTURES.minZoom);
  return HIT_MIN_PX / z;
}

export function labelScaleForZoom(zoom) {
  const z = Math.max(Number(zoom) || 1, 0.4);
  return Math.max(1, 11 / (13 * z));
}

export function edgeLabelInvScale(zoom) {
  const z = Math.max(Number(zoom) || 1, FLOW_GESTURES.minZoom);
  return 1 / z;
}

export function shortNodeId(nodeId) {
  const raw = String(nodeId || "");
  const parts = raw.split(":");
  if (parts.length >= 3 && parts[0].includes("/")) {
    return parts.slice(1).join(":");
  }
  return raw;
}

export function repoFromNodeId(nodeId) {
  const raw = String(nodeId || "");
  const parts = raw.split(":");
  if (parts.length >= 3 && parts[0].includes("/")) return parts[0];
  return "";
}

export function nodeIdMatches(nodeId, query) {
  if (!nodeId || !query) return false;
  if (nodeId === query) return true;
  if (String(query).includes("/")) return false;
  return shortNodeId(nodeId) === query;
}

export function findNodeBySearch(nodes, query) {
  return (nodes || []).find((node) => nodeIdMatches(node.id, query));
}

export function isCompactViewport() {
  return typeof window !== "undefined" && window.matchMedia("(max-width: 980px)").matches;
}

export function frameGraph(api, mode, { compact = false } = {}) {
  if (!api) return;
  if (compact && mode === "architecture") {
    const node = api.getNode?.(ARCHITECTURE_FOCUS_ID);
    if (node?.position) {
      api.setCenter?.(node.position.x + NODE_CENTER.x, node.position.y + NODE_CENTER.y, {
        zoom: FLOW_GESTURES.minZoom,
        duration: 180,
      });
      return;
    }
  }
  api.fitView?.({ padding: 0.18, minZoom: FLOW_GESTURES.minZoom, maxZoom: FLOW_GESTURES.maxZoom, duration: 180 });
}

export function staggerLabelOffsets(relations) {
  const list = relations || [];
  const step = HIT_MIN_PX / FLOW_GESTURES.minZoom;
  const groups = new Map();
  list.forEach((rel, index) => {
    const key = `${rel.relation_type || "related"}::${rel.dst_id}`;
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(index);
  });
  const offsets = Array.from({ length: list.length }, () => 0);
  for (const indexes of groups.values()) {
    const mid = (indexes.length - 1) / 2;
    indexes.forEach((relIndex, rank) => {
      offsets[relIndex] = (rank - mid) * step;
    });
  }
  return offsets;
}

export function capGraphPayload(payload, limit = MAX_VISIBLE_NODES) {
  const nodes = payload?.nodes || [];
  const relations = payload?.relations || [];
  if (nodes.length <= limit) {
    return { ...payload, nodes, relations, truncated: 0, total: nodes.length };
  }
  const kept = nodes.slice(0, limit);
  const ids = new Set(kept.map((node) => node.id));
  return {
    ...payload,
    nodes: kept,
    relations: relations.filter((rel) => ids.has(rel.src_id) && ids.has(rel.dst_id)),
    truncated: nodes.length - limit,
    total: nodes.length,
  };
}

export function parseGraphSearch(search = "") {
  const raw = String(search || "");
  const params = new URLSearchParams(raw.startsWith("?") ? raw.slice(1) : raw);
  return {
    graph: params.get("graph") || undefined,
    node: params.get("node") || undefined,
  };
}

export function serializeGraphSearch({ graph, node } = {}) {
  const params = new URLSearchParams();
  if (graph) params.set("graph", graph);
  if (node) params.set("node", node);
  const query = params.toString();
  return query ? `?${query}` : "";
}

function laneFor(node) {
  if (node.kind === "issue" || node.kind === "pr") {
    return ROLE_LANE[node.role] ?? KIND_LANE[node.kind] ?? 2;
  }
  return KIND_LANE[node.kind] ?? 5;
}

export function layoutGraph(payload) {
  const rawNodes = payload?.nodes || [];
  if (!rawNodes.length) return [];

  const groups = new Map();
  for (const node of rawNodes) {
    const key = node.campaign_id || payload?.campaign?.id || "graph";
    if (!groups.has(key)) groups.set(key, []);
    groups.get(key).push(node);
  }

  const out = [];
  const autoFamilies = [];
  for (const members of groups.values()) {
    const hasPositions = members.every(
      (node) => Number.isFinite(node.position?.x) && Number.isFinite(node.position?.y),
    );
    if (hasPositions) {
      for (const node of members) {
        out.push(toFlowNode(node, node.position));
      }
    } else {
      autoFamilies.push(members);
    }
  }

  const columns = autoFamilies.length > 2 ? 2 : 1;
  let column = 0;
  let originX = 0;
  let originY = 0;
  let rowHeight = 0;
  for (const members of autoFamilies) {
    if (column >= columns) {
      column = 0;
      originX = 0;
      originY += rowHeight + FAMILY_GAP_Y;
      rowHeight = 0;
    }
    const family = layoutFamily(members, originX, originY);
    out.push(...family.nodes);
    originX += family.width + FAMILY_GAP_X;
    rowHeight = Math.max(rowHeight, family.height);
    column += 1;
  }
  return out;
}

function familyColumn(node) {
  if (node.kind === "pr") return 2;
  if (node.kind === "issue") return 1;
  return 0;
}

function layoutFamily(members, originX, originY) {
  const lanes = new Map();
  for (const member of members) {
    const column = familyColumn(member);
    if (!lanes.has(column)) lanes.set(column, []);
    lanes.get(column).push(member);
  }
  const nodes = [];
  let cursorX = originX;
  let tallest = NODE_MIN_HEIGHT;
  let widest = NODE_MIN_WIDTH;
  for (const [, laneNodes] of [...lanes.entries()].sort((a, b) => a[0] - b[0])) {
    laneNodes.sort((a, b) => laneFor(a) - laneFor(b) || String(a.id).localeCompare(String(b.id)));
    const subCols = Math.max(1, Math.ceil(laneNodes.length / LANE_WRAP_ROWS));
    laneNodes.forEach((node, index) => {
      const subCol = Math.floor(index / LANE_WRAP_ROWS);
      const row = index % LANE_WRAP_ROWS;
      const x = cursorX + subCol * LANE_STEP_X;
      const y = originY + row * NODE_STEP_Y;
      tallest = Math.max(tallest, (row + 1) * NODE_STEP_Y);
      widest = Math.max(widest, x - originX + NODE_MIN_WIDTH);
      nodes.push(toFlowNode(node, { x, y }));
    });
    cursorX += subCols * LANE_STEP_X;
  }
  return { nodes, width: Math.max(widest, cursorX - originX), height: tallest };
}

function toFlowNode(node, position) {
  const title = node.title || node.label || node.path || node.id;
  return {
    id: node.id,
    type: "hermes",
    position,
    data: {
      ...node,
      title,
      label: title,
      interactive: true,
    },
    style: {
      minWidth: NODE_MIN_WIDTH,
      minHeight: NODE_MIN_HEIGHT,
      width: NODE_MIN_WIDTH,
      height: NODE_MIN_HEIGHT,
    },
    draggable: false,
    selectable: true,
    connectable: false,
    focusable: false,
  };
}

export function toFlowEdges(relations) {
  const list = relations || [];
  const offsets = staggerLabelOffsets(list);
  return list.map((rel, index) => {
    const color = EDGE_COLOR[rel.relation_type] || "#ffe6cb";
    const dashed = ["possible_duplicate", "related", "similar_to", "suggests"].includes(rel.relation_type);
    return {
      id: rel.id ? String(rel.id) : `${rel.src_id}-${rel.relation_type}-${rel.dst_id}-${index}`,
      source: rel.src_id,
      target: rel.dst_id,
      label: String(rel.relation_type || "related").replaceAll("_", " "),
      selectable: true,
      focusable: true,
      interactionWidth: HIT_MIN_PX / FLOW_GESTURES.minZoom,
      type: "relation",
      markerEnd: { type: "arrowclosed", color },
      style: { stroke: color, strokeWidth: 2, strokeDasharray: dashed ? "6 4" : undefined },
      labelStyle: { fill: color, fontSize: 12, fontWeight: 600 },
      data: { ...rel, labelOffset: offsets[index] },
    };
  });
}

function ticketRepo(data) {
  return data?.repo || repoFromNodeId(data?.id);
}

export function formatNodeKicker(data) {
  if (!data) return "node";
  if (data.kind === "issue" || data.kind === "pr") {
    const ticket = `${data.kind} #${data.number}`;
    const repo = ticketRepo(data);
    return repo ? `${ticket} · ${repo}` : ticket;
  }
  if (data.kind === "file") return "file";
  if (data.kind === "invariant") return "invariant";
  if (data.kind === "campaign") return "campaign";
  return (data.role || data.kind || "node").replaceAll("_", " ");
}

export function formatNodeHeading(data) {
  if (!data) return "Selection";
  const repo = ticketRepo(data);
  if (data.kind === "issue") return repo ? `Issue #${data.number} · ${repo}` : `Issue #${data.number}`;
  if (data.kind === "pr") return repo ? `PR #${data.number} · ${repo}` : `PR #${data.number}`;
  if (data.kind === "campaign") return `Campaign · ${data.title || data.id}`;
  if (data.kind === "file") return `File · ${data.path || data.title || data.id}`;
  if (data.kind === "invariant") return `Invariant · ${data.title || data.id}`;
  if (data.kind === "subsystem") return data.title || data.id;
  if (data.relation_type) return String(data.relation_type).replaceAll("_", " ");
  return data.title || data.id;
}

export function attachTouchLock(element) {
  if (!element) return () => {};
  const stop = (event) => event.preventDefault();
  element.addEventListener("touchmove", stop, { passive: false });
  return () => element.removeEventListener("touchmove", stop);
}

export function describeSelection(selection) {
  if (!selection) return null;
  if (selection.type === "edge") {
    const rel = selection.edge?.data || selection.edge || {};
    return {
      heading: formatNodeHeading(rel),
      kind: "relation",
      kicker: "Typed relationship",
      summary: rel.evidence || "A typed edge in this slice.",
      meta: [
        rel.src_id && rel.dst_id ? `${rel.src_id} → ${rel.dst_id}` : null,
        rel.confidence != null ? `confidence ${Number(rel.confidence).toFixed(2)}` : null,
        rel.evidence_level ? String(rel.evidence_level).replaceAll("_", " ") : null,
      ].filter(Boolean),
      url: null,
    };
  }
  const data = selection.node?.data || selection.node || {};
  return {
    heading: formatNodeHeading(data),
    kind: data.kind || "node",
    kicker: formatNodeKicker(data),
    summary: data.summary || data.title || "",
    meta: [
      ticketRepo(data),
      data.state,
      data.author,
      data.role && String(data.role).replaceAll("_", " "),
      data.path,
    ].filter(Boolean),
    url: data.url || null,
    raw: data,
  };
}
