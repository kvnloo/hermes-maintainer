import { BaseEdge, EdgeLabelRenderer, getBezierPath, useStore } from "@xyflow/react";
import { HIT_MIN_PX, edgeLabelInvScale } from "./graph-model.js";

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
  const inv = edgeLabelInvScale(zoom);
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
            transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px) scale(${inv})`,
            pointerEvents: "all",
            minWidth: HIT_MIN_PX,
            minHeight: HIT_MIN_PX,
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
