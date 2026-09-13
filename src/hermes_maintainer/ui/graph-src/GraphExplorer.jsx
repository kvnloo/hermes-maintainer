import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GraphCanvas } from "./GraphCanvas.jsx";
import {
  FLOW_GESTURES,
  ZOOM_STOPS,
  architectureGraph,
  describeSelection,
  layoutGraph,
  parseGraphSearch,
  serializeGraphSearch,
  toFlowEdges,
} from "./graph-model.js";

const ARCHITECTURE = architectureGraph();
const NODE_CENTER = { x: 124, y: 55 };

function frameGraph(api, mode) {
  if (!api) return;
  const compact = typeof window !== "undefined" && window.matchMedia("(max-width: 980px)").matches;
  if (compact && mode === "architecture") {
    const node = api.getNode?.("arch:sqlite-backlog");
    if (node) {
      api.setCenter(node.position.x + NODE_CENTER.x, node.position.y + NODE_CENTER.y, {
        zoom: 0.4,
        duration: 180,
      });
      return;
    }
  }
  api.fitView?.({ padding: 0.18, minZoom: 0.4, maxZoom: 2, duration: 180 });
}

function GraphToolbar({ mode, zoom, sourceLabel, onArchitecture, onCampaigns, onZoom, onFit }) {
  return (
    <div className="hm-toolbar" role="toolbar" aria-label="Graph controls">
      <div className="hm-mode">
        <button
          type="button"
          className={mode === "architecture" ? "tab active" : "tab"}
          aria-pressed={mode === "architecture"}
          onClick={onArchitecture}
        >
          Architecture
        </button>
        <button
          type="button"
          className={mode === "campaign" ? "tab active" : "tab"}
          aria-pressed={mode === "campaign"}
          onClick={onCampaigns}
        >
          Campaigns
        </button>
      </div>
      <div className="hm-zooms">
        {ZOOM_STOPS.map((stop) => (
          <button
            key={stop}
            type="button"
            className={Math.abs(zoom - stop) < 0.02 ? "tab active" : "tab"}
            aria-label={`Zoom ${stop}`}
            onClick={() => onZoom(stop)}
          >
            {stop}×
          </button>
        ))}
        <button type="button" className="tab" onClick={onFit}>
          Fit view
        </button>
      </div>
      <div className="hm-source">{sourceLabel}</div>
    </div>
  );
}

function GraphLegend({ mode, legend }) {
  return (
    <div className="hm-legend-bar" aria-label="Graph legend">
      <span className="hm-legend-title">
        {mode === "architecture"
          ? "Every box is a control — subsystems, files, invariants."
          : "Issues, PRs, files, and the invariant this campaign is trying to keep true."}
      </span>
      <ul>
        {legend.kinds.map((kind) => (
          <li key={kind}>
            <span className={`swatch kind-${kind}`} />
            {kind}
          </li>
        ))}
      </ul>
      {legend.relations.length ? (
        <span className="hm-legend-rels">{legend.relations.join(" · ")}</span>
      ) : null}
    </div>
  );
}

function GraphDetail({ detail, onBack }) {
  return (
    <aside className="hm-detail" role="region" aria-label="Detail">
      <div className="hm-detail-head">
        <button type="button" onClick={onBack}>
          Back
        </button>
        <span className="hm-kicker">{detail.kicker}</span>
      </div>
      <h2>{detail.heading}</h2>
      <p>{detail.summary}</p>
      {detail.meta?.length ? <p className="meta">{detail.meta.join(" · ")}</p> : null}
      {detail.url ? (
        <p>
          <a href={detail.url} target="_blank" rel="noreferrer">
            Open on GitHub
          </a>
        </p>
      ) : null}
    </aside>
  );
}

function legendItems(nodes, edges) {
  const kinds = [];
  const seenKind = new Set();
  for (const node of nodes) {
    const kind = node.data?.kind;
    if (kind && !seenKind.has(kind)) {
      seenKind.add(kind);
      kinds.push(kind);
    }
  }
  const relations = [];
  const seenRel = new Set();
  for (const edge of edges) {
    const label = edge.label;
    if (label && !seenRel.has(label)) {
      seenRel.add(label);
      relations.push(label);
    }
  }
  return { kinds, relations: relations.slice(0, 8) };
}

export function GraphExplorer({ payload, onSelect, search, onNavigate }) {
  const parsed = parseGraphSearch(search ?? (typeof window !== "undefined" ? window.location.search : ""));
  const [mode, setMode] = useState(parsed.graph || payload?.graph || "architecture");
  const [selected, setSelected] = useState(null);
  const [zoom, setZoom] = useState(1);
  const flowRef = useRef(null);

  useEffect(() => {
    if (payload?.graph) setMode(payload.graph);
  }, [payload?.graph]);

  const status = payload?.status || (payload?.error ? "error" : "ready");
  const source = mode === "architecture" ? ARCHITECTURE : payload;
  const nodes = useMemo(() => {
    const laid = layoutGraph(source);
    return laid.map((node) => ({
      ...node,
      selected: selected?.type === "node" && selected.id === node.id,
    }));
  }, [source, selected]);
  const edges = useMemo(() => {
    const laid = toFlowEdges(source?.relations);
    return laid.map((edge) => ({
      ...edge,
      selected: selected?.type === "edge" && selected.id === edge.id,
    }));
  }, [source, selected]);

  const applySelection = useCallback(
    (next) => {
      setSelected(next);
      const data = next?.type === "edge" ? next.edge?.data : next?.node?.data;
      onSelect?.(data || null, { graph: mode, payload, selection: next });
      const query = serializeGraphSearch({ graph: mode, node: next?.type === "node" ? next.id : undefined });
      onNavigate?.(query);
      if (typeof window !== "undefined" && window.history?.replaceState) {
        const url = `${window.location.pathname}${query}${window.location.hash}`;
        window.history.replaceState(null, "", url);
      }
    },
    [mode, onNavigate, onSelect, payload],
  );

  const clearSelection = useCallback(() => applySelection(null), [applySelection]);

  const appliedLink = useRef(null);
  useEffect(() => {
    if (!parsed.node || appliedLink.current === parsed.node) return;
    const node = layoutGraph(source).find((item) => item.id === parsed.node);
    if (node) {
      appliedLink.current = parsed.node;
      setSelected({ type: "node", id: node.id, node });
    }
  }, [parsed.node, source]);

  useEffect(() => {
    const onKey = (event) => {
      if (event.key === "Escape") {
        event.preventDefault();
        clearSelection();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [clearSelection]);

  const onNodeClick = useCallback(
    (_event, node) => applySelection({ type: "node", id: node.id, node }),
    [applySelection],
  );
  const onEdgeClick = useCallback(
    (_event, edge) => applySelection({ type: "edge", id: edge.id, edge }),
    [applySelection],
  );
  const onPaneClick = useCallback((event) => {
    if (event?.target?.closest?.(".hm-node, .hm-edge-label, button")) return;
    clearSelection();
  }, [clearSelection]);

  const zoomTo = useCallback((value) => {
    setZoom(value);
    const api = flowRef.current;
    if (!api) return;
    if (selected?.type === "node") {
      const node = api.getNode?.(selected.id);
      if (node) {
        api.setCenter(node.position.x + NODE_CENTER.x, node.position.y + NODE_CENTER.y, { zoom: value, duration: 140 });
        return;
      }
    }
    api.zoomTo?.(value, { duration: 140 });
  }, [selected]);

  const fit = useCallback(() => {
    const api = flowRef.current;
    if (!api) return;
    const compact = typeof window !== "undefined" && window.matchMedia("(max-width: 980px)").matches;
    if (compact && mode === "architecture") setZoom(0.4);
    frameGraph(api, mode);
  }, [mode]);

  const detail = describeSelection(selected);
  const legend = legendItems(nodes, edges);
  const campaignEmpty = mode === "campaign" && status === "ready" && !(payload?.nodes || []).length;
  const graphKey = `${mode}:${nodes.map((node) => node.id).join("|")}`;

  useEffect(() => {
    if (status !== "ready" || campaignEmpty) return undefined;
    const timer = window.setTimeout(() => {
      if (window.matchMedia("(max-width: 980px)").matches && mode === "architecture") {
        setZoom(0.4);
      }
      frameGraph(flowRef.current, mode);
    }, 120);
    return () => window.clearTimeout(timer);
  }, [graphKey, status, campaignEmpty, mode]);

  if (status === "loading") {
    return (
      <div className="graph-shell">
        <div className="graph-empty" role="status">
          Reading the backlog graph from local SQLite…
        </div>
      </div>
    );
  }

  if (status === "error") {
    return (
      <div className="graph-shell">
        <div className="graph-empty" role="alert">
          {payload?.error || "The graph endpoint failed."} The dashboard did not change any GitHub
          state. Retry, or load the seed canvas.
        </div>
      </div>
    );
  }

  return (
    <div className="graph-shell" style={{ ["--graph-zoom"]: String(zoom) }}>
      <GraphToolbar
        mode={mode}
        zoom={zoom}
        sourceLabel={
          mode === "architecture"
            ? "Maintainer map · local SQLite, read-only GitHub"
            : (payload?.campaign?.title || (payload?.families?.length ? `${payload.families.length} seed families` : "Campaign slice"))
        }
        onArchitecture={() => {
          setMode("architecture");
          setSelected(null);
        }}
        onCampaigns={() => {
          setMode("campaign");
          setSelected(null);
        }}
        onZoom={zoomTo}
        onFit={fit}
      />
      <GraphLegend mode={mode} legend={legend} />

      {campaignEmpty ? (
        <div className="graph-empty">
          This campaign slice has no members yet. Scan NousResearch/hermes-agent, or open the seed
          canvas to inspect the CI-verdict and OAuth families.
        </div>
      ) : (
        <div className="hm-stage">
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            zoom={zoom}
            onZoomChange={setZoom}
            onReady={(api) => {
              const ready = api.getNode ? { ...api, getNode: api.getNode.bind(api) } : api;
              flowRef.current = ready;
              frameGraph(ready, mode);
            }}
            onNodeClick={onNodeClick}
            onEdgeClick={onEdgeClick}
            onPaneClick={onPaneClick}
            panOnScroll={FLOW_GESTURES.panOnScroll}
            zoomOnPinch={FLOW_GESTURES.zoomOnPinch}
            preventScrolling={FLOW_GESTURES.preventScrolling}
            minZoom={FLOW_GESTURES.minZoom}
            maxZoom={FLOW_GESTURES.maxZoom}
            nodesFocusable={FLOW_GESTURES.nodesFocusable}
            edgesFocusable={FLOW_GESTURES.edgesFocusable}
            touchAction={FLOW_GESTURES.touchAction}
          />
          {detail ? <GraphDetail detail={detail} onBack={clearSelection} /> : null}
        </div>
      )}
    </div>
  );
}
