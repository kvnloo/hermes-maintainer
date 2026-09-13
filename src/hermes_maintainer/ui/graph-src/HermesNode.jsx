import { Handle, Position, useStore } from "@xyflow/react";
import { formatNodeKicker, labelScaleForZoom } from "./graph-model.js";

export const hermesNodeHandlers = { onClick: null };

export function HermesNode({ id, data, selected }) {
  const zoom = useStore((state) => state.transform[2]);
  const scale = labelScaleForZoom(zoom);
  const title = data.title || data.label || id;
  const compact = zoom < 0.75;
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
          minWidth: 248,
          minHeight: 110,
          height: 110,
          overflow: "hidden",
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
        {data.kind === "issue" || data.kind === "pr"
          ? (!compact && (data.state || data.author) ? (
            <span className="hm-meta">{`${data.state || "open"}${data.author ? ` · ${data.author}` : ""}`}</span>
          ) : null)
          : (!compact && data.summary ? <span className="hm-meta">{data.summary}</span> : null)}
      </button>
      <Handle type="source" position={Position.Bottom} isConnectable={false} />
    </div>
  );
}
