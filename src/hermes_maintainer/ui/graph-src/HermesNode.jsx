import { Handle, Position, useStore } from "@xyflow/react";
import { formatNodeKicker, labelScaleForZoom } from "./graph-model.js";

export function HermesNode({ id, data, selected }) {
  const zoom = useStore((state) => state.transform[2]);
  const scale = labelScaleForZoom(zoom);
  const title = data.title || data.label || id;
  const compact = zoom < 0.75;
  const kind = data.kind || "subsystem";

  return (
    <div className={`hm-node-shell kind-${kind} role-${data.role || "member"}${selected ? " is-selected" : ""}`}>
      <Handle type="target" position={Position.Top} isConnectable={false} />
      <button
        type="button"
        className="hm-node nopan nodrag"
        aria-label={title}
        aria-pressed={selected ? "true" : "false"}
        style={{
          minWidth: 248,
          minHeight: 110,
          fontSize: `${13 * scale}px`,
        }}
      >
        <span className="hm-kicker">
          <span>{formatNodeKicker(data)}</span>
          {data.kind === "issue" || data.kind === "pr" ? (
            <span>{(data.role || "member").replaceAll("_", " ")}</span>
          ) : null}
        </span>
        <span className="hm-title">{title}</span>
        {!compact && (data.summary || data.state || data.author) ? (
          <span className="hm-meta">
            {data.kind === "issue" || data.kind === "pr"
              ? `${data.state || "open"}${data.author ? ` · ${data.author}` : ""}`
              : data.summary}
          </span>
        ) : null}
      </button>
      <Handle type="source" position={Position.Bottom} isConnectable={false} />
    </div>
  );
}
