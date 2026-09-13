import { Handle, Position, useStore } from "@xyflow/react";
import { formatNodeKicker, labelScaleForZoom, NODE_MIN_HEIGHT, NODE_MIN_WIDTH } from "./graph-model.js";

export const hermesNodeHandlers = { onClick: null };

function NodeKicker({ data }) {
  const ticket = data.kind === "issue" || data.kind === "pr";
  return (
    <span className="hm-kicker">
      <span>{formatNodeKicker(data)}</span>
      {ticket ? <span>{(data.role || "member").replaceAll("_", " ")}</span> : null}
    </span>
  );
}

function NodeMeta({ data, compact }) {
  if (compact) return null;
  const ticket = data.kind === "issue" || data.kind === "pr";
  const text = ticket
    ? (data.state || data.author ? `${data.state || "open"}${data.author ? ` · ${data.author}` : ""}` : null)
    : (data.summary || null);
  return text ? <span className="hm-meta">{text}</span> : null;
}

export function HermesNode({ id, data, selected }) {
  const zoom = useStore((state) => state.transform[2]);
  const scale = labelScaleForZoom(zoom);
  const title = data.title || data.label || id;
  const kind = data.kind || "subsystem";

  const activate = (event) => {
    event.stopPropagation();
    hermesNodeHandlers.onClick?.(event, { id, type: "hermes", data, selected });
  };

  return (
    <div className={`hm-node-shell kind-${kind} role-${data.role || "member"}${selected ? " is-selected" : ""}`}>
      <Handle type="target" position={Position.Top} isConnectable={false} />
      <button
        type="button"
        className="hm-node nopan nodrag"
        aria-label={title}
        aria-pressed={selected ? "true" : "false"}
        onClick={activate}
        onKeyDown={(event) => {
          if (event.key === "Enter" || event.key === " ") {
            event.preventDefault();
            activate(event);
          }
        }}
        style={{
          minWidth: NODE_MIN_WIDTH,
          minHeight: NODE_MIN_HEIGHT,
          height: NODE_MIN_HEIGHT,
          overflow: "hidden",
          fontSize: `${13 * scale}px`,
        }}
      >
        <NodeKicker data={data} />
        <span className="hm-title">{title}</span>
        <NodeMeta data={data} compact={zoom < 0.75} />
      </button>
      <Handle type="source" position={Position.Bottom} isConnectable={false} />
    </div>
  );
}
