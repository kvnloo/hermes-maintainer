import { BaseEdge, EdgeLabelRenderer, getBezierPath } from "@xyflow/react";

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
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            pointerEvents: "all",
            minWidth: 44,
            minHeight: 44,
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
        >
          {label}
        </button>
      </EdgeLabelRenderer>
    </>
  );
}
