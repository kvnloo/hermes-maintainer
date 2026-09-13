import { BaseEdge, EdgeLabelRenderer, getBezierPath, useStore } from "@xyflow/react";
import { edgeLabelHitForZoom, edgeLabelInvScale } from "./graph-model.js";

export const relationEdgeHandlers = { onClick: null };

export function RelationEdge({
  id,
  source,
  target,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  label,
  style,
  markerEnd,
  selected,
  data,
}) {
  const zoom = useStore((state) => state.transform[2]);
  const fontSize = 11 * edgeLabelInvScale(zoom);
  const hit = edgeLabelHitForZoom(zoom);
  const offset = Number(data?.labelOffset) || 0;
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    targetX,
    targetY,
    sourcePosition,
    targetPosition,
  });
  return (
    <>
      <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={style} />
      <EdgeLabelRenderer>
        <button
          type="button"
          className={`hm-edge-label nopan nodrag${selected ? " is-selected" : ""}`}
          style={{
            position: "absolute",
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY + offset}px)`,
            pointerEvents: "all",
            fontSize: `${fontSize}px`,
            minHeight: hit,
            minWidth: hit,
          }}
          aria-label={String(label || "relation")}
          onClick={(event) => {
            event.stopPropagation();
            relationEdgeHandlers.onClick?.(event, {
              id,
              source,
              target,
              label,
              data,
              selectable: true,
            });
          }}
          onKeyDown={(event) => {
            if (event.key === "Enter" || event.key === " ") {
              event.preventDefault();
              event.currentTarget.click();
            }
          }}
        >
          {label}
        </button>
      </EdgeLabelRenderer>
    </>
  );
}
