import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { GraphCanvas } from "./GraphCanvas.jsx";
import {
  FLOW_GESTURES,
  NODE_CENTER,
  ZOOM_STOPS,
  architectureGraph,
  capGraphPayload,
  describeSelection,
  edgeLabelsVisible,
  findNodeBySearch,
  frameGraph,
  isCompactViewport,
  layoutGraph,
  parseGraphSearch,
  serializeGraphSearch,
  toFlowEdges,
} from "./graph-model.js";

const ARCHITECTURE = architectureGraph();

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
      <div className="hm-fit">
        <button type="button" className="tab" onClick={onFit}>
          Fit view
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
      </div>
      <div className="hm-source">{sourceLabel}</div>
    </div>
  );
}

function GraphLegend({ mode, legend, truncated, visible, total, onUseSeed }) {
  return (
    <div className="hm-legend-bar" aria-label="Graph legend">
      <span className={`hm-legend-title${truncated ? " is-truncated" : ""}`}>
        {truncated
          ? `Showing ${visible} of ${total} tickets. Rebuild campaigns or open the seed canvas.`
          : mode === "architecture"
            ? "Every box is a control — subsystems, files, invariants."
            : "Issues, PRs, files, and the invariant this campaign is trying to keep true."}
      </span>
      {truncated && onUseSeed ? (
        <button type="button" className="tab" onClick={onUseSeed}>
          Load seed families
        </button>
      ) : null}
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

export function GraphExplorer({ payload, onSelect, search, onNavigate, onUseSeed }) {
  const parsed = parseGraphSearch(
    search !== undefined
      ? search
      : (typeof window !== "undefined" ? window.location.search : ""),
  );
  const [mode, setMode] = useState(parsed.graph || payload?.graph || "architecture");
  const [selected, setSelected] = useState(null);
  const [zoom, setZoom] = useState(1);
  const flowRef = useRef(null);

  useEffect(() => {
    if (parsed.graph) {
      setMode(parsed.graph);
      return;
    }
    if (payload?.graph) setMode(payload.graph);
  }, [parsed.graph, payload?.graph]);

  const status = payload?.status || (payload?.error ? "error" : "ready");
  const rawSource = mode === "architecture" ? ARCHITECTURE : payload;
  const source = useMemo(
    () => (mode === "architecture" ? rawSource : capGraphPayload(rawSource)),
    [mode, rawSource],
  );
  const nodes = useMemo(() => {
    const laid = layoutGraph(source);
    return laid.map((node) => ({
      ...node,
      selected: selected?.type === "node" && selected.id === node.id,
    }));
  }, [source, selected]);
  const hideLabels = !edgeLabelsVisible(source?.nodes?.length || 0, zoom);
  const edges = useMemo(() => {
    const laid = toFlowEdges(source?.relations, { hideLabels });
    return laid.map((edge) => ({
      ...edge,
      selected: selected?.type === "edge" && selected.id === edge.id,
    }));
  }, [source, selected, hideLabels]);

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
      if (next?.type === "node" && isCompactViewport()) {
        const api = flowRef.current;
        const node = api?.getNode?.(next.id) || next.node;
        if (node?.position && api?.setCenter) {
          api.setCenter(node.position.x + NODE_CENTER.x, node.position.y + NODE_CENTER.y, {
            zoom,
            duration: 140,
          });
        }
      }
    },
    [mode, onNavigate, onSelect, payload, zoom],
  );

  const clearSelection = useCallback(() => applySelection(null), [applySelection]);

  const appliedLink = useRef(null);
  useEffect(() => {
    if (!parsed.node || appliedLink.current === parsed.node) return;
    const fromCurrent = findNodeBySearch(layoutGraph(source), parsed.node);
    if (fromCurrent) {
      appliedLink.current = parsed.node;
      setSelected({ type: "node", id: fromCurrent.id, node: fromCurrent });
      return;
    }
    if (mode !== "campaign") {
      const fromPayload = findNodeBySearch(layoutGraph(payload), parsed.node);
      if (fromPayload) {
        appliedLink.current = parsed.node;
        setMode("campaign");
        setSelected({ type: "node", id: fromPayload.id, node: fromPayload });
      }
    }
  }, [parsed.node, source, payload, mode]);

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
    const compact = isCompactViewport();
    if (compact && mode === "architecture") setZoom(FLOW_GESTURES.minZoom);
    frameGraph(api, mode, { compact });
  }, [mode]);

  const detail = describeSelection(selected);
  const legend = legendItems(nodes, edges);
  const campaignEmpty = mode === "campaign" && status === "ready" && !(payload?.nodes || []).length;
  const graphKey = `${mode}:${nodes.map((node) => node.id).join("|")}`;

  useEffect(() => {
    if (status !== "ready" || campaignEmpty) return undefined;
    const timer = window.setTimeout(() => {
      const compact = isCompactViewport();
      if (compact && mode === "architecture") setZoom(FLOW_GESTURES.minZoom);
      frameGraph(flowRef.current, mode, { compact });
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
            : source?.truncated
              ? `Showing ${source.nodes.length} of ${source.total}`
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
      <GraphLegend
        mode={mode}
        legend={legend}
        truncated={Boolean(source?.truncated)}
        visible={source?.nodes?.length}
        total={source?.total}
        onUseSeed={onUseSeed}
      />

      {campaignEmpty ? (
        <div className="graph-empty">
          This campaign slice has no members yet. Scan NousResearch/hermes-agent, or open the seed
          canvas to inspect the CI-verdict and OAuth families.
          {onUseSeed ? (
            <p>
              <button type="button" className="tab" onClick={onUseSeed}>
                Load seed families
              </button>
            </p>
          ) : null}
        </div>
      ) : (
        <div className="hm-stage">
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            zoom={zoom}
            onZoomChange={setZoom}
            onReady={(api) => {
              flowRef.current = api;
              frameGraph(api, mode, { compact: isCompactViewport() });
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
