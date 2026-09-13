import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
} from "@xyflow/react";
import { useEffect, useMemo, useRef, useState } from "react";
import { HermesNode, hermesNodeHandlers } from "./HermesNode.jsx";
import { RelationEdge, relationEdgeHandlers } from "./RelationEdge.jsx";
import { attachTouchLock, FLOW_GESTURES } from "./graph-model.js";

const nodeTypes = { hermes: HermesNode };
const edgeTypes = { relation: RelationEdge };

const defaultEdgeOptions = { type: "default", animated: false };

function nodeColor(node) {
  const kind = node.data?.kind;
  if (kind === "issue") return "#ffe6cb";
  if (kind === "pr" || node.data?.role === "survivor") return "#34d399";
  if (kind === "invariant") return "#fbbf24";
  if (kind === "file") return "#5eead4";
  if (kind === "campaign") return "#ffbd38";
  return "#c4b5fd";
}

function CanvasInner({
  nodes,
  edges,
  onNodeClick,
  onEdgeClick,
  onPaneClick,
  onReady,
  onZoomChange,
  panOnScroll = FLOW_GESTURES.panOnScroll,
  zoomOnPinch = FLOW_GESTURES.zoomOnPinch,
  preventScrolling = FLOW_GESTURES.preventScrolling,
  minZoom = FLOW_GESTURES.minZoom,
  maxZoom = FLOW_GESTURES.maxZoom,
  nodesFocusable = FLOW_GESTURES.nodesFocusable,
  edgesFocusable = FLOW_GESTURES.edgesFocusable,
  touchAction = FLOW_GESTURES.touchAction,
}) {
  const rootRef = useRef(null);
  const [rfNodes, setNodes, onNodesChange] = useNodesState(nodes);
  const [rfEdges, setEdges, onEdgesChange] = useEdgesState(edges);
  const [showMiniMap, setShowMiniMap] = useState(() => (
    typeof window !== "undefined" && window.matchMedia("(min-width: 981px)").matches
  ));

  useEffect(() => {
    setNodes(nodes || []);
    setEdges(edges || []);
  }, [nodes, edges, setEdges, setNodes]);

  useEffect(() => attachTouchLock(rootRef.current), []);

  useEffect(() => {
    const mq = window.matchMedia("(min-width: 981px)");
    const onChange = () => setShowMiniMap(mq.matches);
    onChange();
    mq.addEventListener("change", onChange);
    return () => mq.removeEventListener("change", onChange);
  }, []);

  useEffect(() => {
    hermesNodeHandlers.onClick = onNodeClick || null;
    relationEdgeHandlers.onClick = onEdgeClick || null;
    return () => {
      if (hermesNodeHandlers.onClick === onNodeClick) hermesNodeHandlers.onClick = null;
      if (relationEdgeHandlers.onClick === onEdgeClick) relationEdgeHandlers.onClick = null;
    };
  }, [onEdgeClick, onNodeClick]);

  const fitViewOptions = useMemo(() => ({ padding: 0.18, minZoom, maxZoom }), [minZoom, maxZoom]);

  return (
    <div
      ref={rootRef}
      className="hm-flow"
      data-zoom-on-pinch={String(zoomOnPinch)}
      data-pan-on-scroll={String(panOnScroll)}
      data-touch-action={touchAction}
      style={{ width: "100%", height: "100%", touchAction }}
    >
      <ReactFlow
        nodes={rfNodes}
        edges={rfEdges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        onPaneClick={onPaneClick}
        onInit={onReady}
        onMove={(_, viewport) => onZoomChange?.(viewport.zoom)}
        onMoveEnd={(_, viewport) => onZoomChange?.(viewport.zoom)}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        fitView
        fitViewOptions={fitViewOptions}
        colorMode="dark"
        nodesConnectable={FLOW_GESTURES.nodesConnectable}
        nodesDraggable={FLOW_GESTURES.nodesDraggable}
        elementsSelectable={FLOW_GESTURES.elementsSelectable}
        nodesFocusable={nodesFocusable}
        edgesFocusable={edgesFocusable}
        edgesReconnectable={false}
        elevateNodesOnSelect
        elevateEdgesOnSelect
        defaultEdgeOptions={defaultEdgeOptions}
        minZoom={minZoom}
        maxZoom={maxZoom}
        panOnScroll={panOnScroll}
        panOnScrollMode={FLOW_GESTURES.panOnScrollMode}
        panOnScrollSpeed={FLOW_GESTURES.panOnScrollSpeed}
        zoomOnPinch={zoomOnPinch}
        zoomOnScroll={FLOW_GESTURES.zoomOnScroll}
        preventScrolling={preventScrolling}
        panOnDrag={FLOW_GESTURES.panOnDrag}
        zoomOnDoubleClick={FLOW_GESTURES.zoomOnDoubleClick}
        autoPanOnNodeFocus={FLOW_GESTURES.autoPanOnNodeFocus}
        nodeClickDistance={FLOW_GESTURES.nodeClickDistance}
        paneClickDistance={FLOW_GESTURES.paneClickDistance}
        deleteKeyCode={FLOW_GESTURES.deleteKeyCode}
        onlyRenderVisibleElements={false}
        attributionPosition="bottom-right"
        proOptions={{ hideAttribution: true }}
        className="hm-flow"
        style={{ width: "100%", height: "100%", touchAction }}
        noWheelClassName="nowheel"
      >
        <Background variant={BackgroundVariant.Dots} gap={22} size={1} color="rgba(255, 189, 56, 0.16)" />
        <Controls showInteractive={false} position="bottom-right" />
        {showMiniMap ? (
          <MiniMap nodeColor={nodeColor} maskColor="rgba(4, 28, 28, 0.78)" position="bottom-left" pannable zoomable />
        ) : null}
      </ReactFlow>
    </div>
  );
}

export function GraphCanvas(props) {
  return (
    <ReactFlowProvider>
      <CanvasInner {...props} />
    </ReactFlowProvider>
  );
}
