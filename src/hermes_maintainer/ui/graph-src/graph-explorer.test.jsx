import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { SAMPLE_CAMPAIGN } from "./fixtures.js";
import { FLOW_GESTURES, HIT_MIN_PX, ZOOM_STOPS } from "./graph-model.js";

vi.mock("./GraphCanvas.jsx", () => ({
  GraphCanvas: function MockGraphCanvas(props) {
    const ref = { current: null };
    useEffect(() => {
      props.onReady?.({
        fitView: () => {
          document.body.setAttribute("data-fit", "1");
        },
        zoomTo: (zoom) => {
          document.body.setAttribute("data-zoom", String(zoom));
          props.onZoomChange?.(zoom);
        },
        setViewport: ({ zoom }) => {
          document.body.setAttribute("data-zoom", String(zoom));
          props.onZoomChange?.(zoom);
        },
        getZoom: () => Number(document.body.getAttribute("data-zoom") || props.zoom || 1),
      });
    }, [props]);
    useEffect(() => {
      const el = ref.current;
      if (!el) return undefined;
      const stop = (event) => event.preventDefault();
      el.addEventListener("touchmove", stop, { passive: false });
      return () => el.removeEventListener("touchmove", stop);
    }, []);
    return (
      <div
        ref={(node) => {
          ref.current = node;
        }}
        data-testid="graph-canvas"
        data-pan-on-scroll={String(props.panOnScroll)}
        data-zoom-on-pinch={String(props.zoomOnPinch)}
        data-prevent-scrolling={String(props.preventScrolling)}
        data-min-zoom={String(props.minZoom)}
        data-max-zoom={String(props.maxZoom)}
        data-nodes-focusable={String(props.nodesFocusable)}
        data-edges-focusable={String(props.edgesFocusable)}
        data-touch-action={props.touchAction || "none"}
        style={{ touchAction: props.touchAction || "none" }}
      >
        {(props.nodes || []).map((node) => (
          <button
            key={node.id}
            type="button"
            className="hm-node"
            data-kind={node.data?.kind}
            style={{ minWidth: node.style?.minWidth, minHeight: node.style?.minHeight }}
            onClick={(event) => props.onNodeClick?.(event, node)}
          >
            {node.data?.title || node.data?.label || node.id}
          </button>
        ))}
        {(props.edges || []).map((edge) => (
          <button
            key={edge.id}
            type="button"
            className="hm-edge"
            onClick={(event) => props.onEdgeClick?.(event, edge)}
          >
            {edge.label}
          </button>
        ))}
      </div>
    );
  },
}));

const { GraphExplorer } = await import("./GraphExplorer.jsx");

function renderExplorer(payload, extra = {}) {
  return render(
    <div style={{ width: 1280, height: 800 }}>
      <GraphExplorer payload={payload} {...extra} />
    </div>,
  );
}

describe("GraphExplorer", () => {
  beforeEach(() => {
    document.body.removeAttribute("data-zoom");
    document.body.removeAttribute("data-fit");
  });

  it("renders a loading state before the graph exists", () => {
    renderExplorer({ status: "loading" });
    expect(screen.getByRole("status")).toHaveTextContent(/reading the backlog graph/i);
  });

  it("renders an error state without implying GitHub writes", () => {
    renderExplorer({ status: "error", error: "502 from /api/graph" });
    expect(screen.getByRole("alert")).toHaveTextContent(/502 from \/api\/graph/i);
    expect(screen.getByRole("alert")).toHaveTextContent(/did not change any GitHub state/i);
  });

  it("renders an empty campaign with a way onto the architecture map", () => {
    renderExplorer({ status: "ready", graph: "campaign", nodes: [], relations: [] });
    expect(screen.getByText(/no members yet/i)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /architecture/i })).toBeEnabled();
  });

  it("renders campaign nodes and relations, not a static poster", async () => {
    const user = userEvent.setup();
    const onSelect = vi.fn();
    renderExplorer(SAMPLE_CAMPAIGN, { onSelect });
    expect(screen.getByRole("button", { name: /cancelled ci treated as success/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /composite ci gate/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^fixes$/i })).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /cancelled ci treated as success/i }));
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/issue #98557/i);
    expect(onSelect).toHaveBeenCalled();
  });

  it("opens issue, PR, campaign, file, and invariant details from node clicks", async () => {
    const user = userEvent.setup();
    renderExplorer(SAMPLE_CAMPAIGN);
    await user.click(screen.getByRole("button", { name: /ci verdict integrity/i }));
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/campaign/i);
    await user.click(screen.getByRole("button", { name: /composite ci gate/i }));
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/pr #103195/i);
    await user.click(screen.getByRole("button", { name: /ci\.yaml/i }));
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/\.github\/workflows\/ci\.yaml/i);
    await user.click(screen.getByRole("button", { name: /cancelled ci is not success/i }));
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(
      /cannot be accepted as a successful verification/i,
    );
  });

  it("selects a relation when a clickable edge is activated", async () => {
    const user = userEvent.setup();
    renderExplorer(SAMPLE_CAMPAIGN);
    await user.click(screen.getByRole("button", { name: /^fixes$/i }));
    const detail = screen.getByRole("region", { name: /detail/i });
    expect(detail).toHaveTextContent(/fixes/i);
    expect(detail).toHaveTextContent(/source_confirmed|source confirmed/i);
  });

  it("clears the selection with Escape and Back", async () => {
    const user = userEvent.setup();
    renderExplorer(SAMPLE_CAMPAIGN);
    await user.click(screen.getByRole("button", { name: /composite ci gate/i }));
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/pr #103195/i);
    await user.keyboard("{Escape}");
    expect(screen.queryByRole("region", { name: /detail/i })).not.toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: /composite ci gate/i }));
    await user.click(screen.getByRole("button", { name: /back/i }));
    expect(screen.queryByRole("region", { name: /detail/i })).not.toBeInTheDocument();
  });

  it("focuses a node and activates it with Enter and Space", async () => {
    const user = userEvent.setup();
    renderExplorer(SAMPLE_CAMPAIGN);
    const node = screen.getByRole("button", { name: /cancelled ci treated as success/i });
    node.focus();
    expect(node).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/issue #98557/i);
    await user.keyboard("{Escape}");
    node.focus();
    await user.keyboard(" ");
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/issue #98557/i);
  });

  it("deep-links ?node= onto a selected node", async () => {
    renderExplorer(SAMPLE_CAMPAIGN, { search: "?graph=campaign&node=issue:98557" });
    await waitFor(() => {
      expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/issue #98557/i);
    });
  });

  it("renders architecture targets as buttons, not posters", async () => {
    const user = userEvent.setup();
    renderExplorer({ status: "ready", graph: "architecture" });
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    const sqlite = screen.getByRole("button", { name: /sqlite backlog graph/i });
    expect(sqlite.tagName).toBe("BUTTON");
    await user.click(sqlite);
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/sqlite/i);
  });

  it("passes native gesture props through the canvas adapter", () => {
    renderExplorer(SAMPLE_CAMPAIGN);
    const canvas = screen.getByTestId("graph-canvas");
    expect(canvas).toHaveAttribute("data-pan-on-scroll", String(FLOW_GESTURES.panOnScroll));
    expect(canvas).toHaveAttribute("data-zoom-on-pinch", String(FLOW_GESTURES.zoomOnPinch));
    expect(canvas).toHaveAttribute("data-prevent-scrolling", String(FLOW_GESTURES.preventScrolling));
    expect(canvas).toHaveAttribute("data-min-zoom", "0.4");
    expect(canvas).toHaveAttribute("data-max-zoom", "2");
    expect(canvas).toHaveAttribute("data-touch-action", "none");
    expect(canvas.style.touchAction).toBe("none");
  });

  it("keeps nodes selectable at every zoom stop and after fit-view", async () => {
    const user = userEvent.setup();
    renderExplorer(SAMPLE_CAMPAIGN);
    const canvas = screen.getByTestId("graph-canvas");
    expect(canvas).toHaveAttribute("data-min-zoom", "0.4");
    expect(canvas).toHaveAttribute("data-max-zoom", "2");

    for (const zoom of ZOOM_STOPS) {
      await user.click(screen.getByRole("button", { name: `Zoom ${zoom}`, exact: true }));
      expect(document.body.getAttribute("data-zoom")).toBe(String(zoom));
      const node = screen.getByRole("button", { name: /cancelled ci treated as success/i });
      expect(Number.parseFloat(node.style.minHeight)).toBeGreaterThanOrEqual(HIT_MIN_PX / 0.4);
      await user.click(node);
      expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/issue #98557/i);
      await user.keyboard("{Escape}");
    }

    await user.click(screen.getByRole("button", { name: /fit view/i }));
    expect(document.body.getAttribute("data-fit")).toBe("1");
    await user.click(screen.getByRole("button", { name: /composite ci gate/i }));
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/pr #103195/i);
  });

  it("does not hand touch moves to page scroll", () => {
    renderExplorer(SAMPLE_CAMPAIGN);
    const canvas = screen.getByTestId("graph-canvas");
    const touch = new Event("touchmove", { bubbles: true, cancelable: true });
    canvas.dispatchEvent(touch);
    expect(touch.defaultPrevented).toBe(true);
  });
});
