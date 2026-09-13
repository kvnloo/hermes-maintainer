import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useEffect } from "react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { NAMESPACED_CAMPAIGN, SAMPLE_CAMPAIGN } from "./fixtures.js";
import { FLOW_GESTURES, HIT_MIN_PX, ZOOM_STOPS } from "./graph-model.js";

function stubViewport(width) {
  window.matchMedia = (query) => {
    const max = /max-width:\s*(\d+)/.exec(String(query));
    const min = /min-width:\s*(\d+)/.exec(String(query));
    let matches = false;
    if (max) matches = width <= Number(max[1]);
    if (min) matches = width >= Number(min[1]);
    return {
      matches,
      media: query,
      onchange: null,
      addListener() {},
      removeListener() {},
      addEventListener() {},
      removeEventListener() {},
      dispatchEvent() {
        return false;
      },
    };
  };
}

function createFlowApi(props) {
  return Object.create({
    fitView() {
      document.body.setAttribute("data-fit", "1");
    },
    zoomTo(zoom) {
      document.body.setAttribute("data-zoom", String(zoom));
      props.onZoomChange?.(zoom);
    },
    setViewport({ zoom }) {
      document.body.setAttribute("data-zoom", String(zoom));
      props.onZoomChange?.(zoom);
    },
    getZoom() {
      return Number(document.body.getAttribute("data-zoom") || props.zoom || 1);
    },
    getNode(id) {
      const node = (props.nodes || []).find((item) => item.id === id);
      if (node) return node;
      if (id === "arch:sqlite-backlog") return { id, position: { x: 280, y: 510 } };
      return undefined;
    },
    setCenter(x, y, opts = {}) {
      document.body.setAttribute("data-center", `${x},${y},${opts.zoom ?? ""}`);
      if (opts.zoom != null) {
        document.body.setAttribute("data-zoom", String(opts.zoom));
        props.onZoomChange?.(opts.zoom);
      }
    },
  });
}

vi.mock("./GraphCanvas.jsx", () => ({
  GraphCanvas: function MockGraphCanvas(props) {
    const ref = { current: null };
    useEffect(() => {
      props.onReady?.(createFlowApi(props));
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
        data-minimap={props.zoom >= 1.5 ? "off" : "on"}
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
            aria-label={String(edge.label || "relation")}
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
    <div style={{ width: extra.width || 1280, height: extra.height || 800 }}>
      <GraphExplorer payload={payload} {...extra} />
    </div>,
  );
}

describe("GraphExplorer", () => {
  const originalMatchMedia = window.matchMedia;

  beforeEach(() => {
    window.history.replaceState(null, "", "/");
    document.body.removeAttribute("data-zoom");
    document.body.removeAttribute("data-fit");
    document.body.removeAttribute("data-center");
    stubViewport(1280);
  });

  afterEach(() => {
    window.matchMedia = originalMatchMedia;
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

  it("focuses an edge and activates it with Enter and Space", async () => {
    const user = userEvent.setup();
    renderExplorer(SAMPLE_CAMPAIGN);
    const edge = screen.getByRole("button", { name: /^fixes$/i });
    edge.focus();
    expect(edge).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/fixes/i);
    await user.keyboard("{Escape}");
    edge.focus();
    await user.keyboard(" ");
    expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/fixes/i);
  });

  it("deep-links ?node= onto a selected node", async () => {
    renderExplorer(SAMPLE_CAMPAIGN, { search: "?graph=campaign&node=issue:98557" });
    await waitFor(() => {
      expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/issue #98557/i);
    });
  });

  it("deep-links ?node= without ?graph= onto the campaign issue", async () => {
    const payload = { ...SAMPLE_CAMPAIGN };
    delete payload.graph;
    renderExplorer(payload, { search: "?node=issue:98557" });
    await waitFor(() => {
      expect(screen.getByRole("region", { name: /detail/i })).toHaveTextContent(/issue #98557/i);
    });
  });

  it("honors ?graph=campaign when payload.graph is omitted", () => {
    const payload = { ...SAMPLE_CAMPAIGN };
    delete payload.graph;
    renderExplorer(payload, { search: "?graph=campaign" });
    expect(screen.getByRole("button", { name: /cancelled ci treated as success/i })).toBeInTheDocument();
  });

  it("deep-links a short ?node=issue:N onto a namespaced owner/name:issue:N id", async () => {
    renderExplorer(NAMESPACED_CAMPAIGN, { search: "?graph=campaign&node=issue:98557" });
    await waitFor(() => {
      const detail = screen.getByRole("region", { name: /detail/i });
      expect(detail).toHaveTextContent(/issue #98557/i);
      expect(detail).toHaveTextContent(/acme\/widgets/i);
    });
  });

  it("renders architecture targets as buttons, not posters", async () => {
    const user = userEvent.setup();
    renderExplorer({ status: "ready", graph: "architecture" }, { search: "?graph=architecture" });
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

  it("keeps Fit view off the wrapping zoom-chip row so 390 layouts can still hit it", () => {
    stubViewport(390);
    renderExplorer(SAMPLE_CAMPAIGN, { width: 390, height: 844 });
    const fit = screen.getByRole("button", { name: /fit view/i });
    expect(fit.closest(".hm-zooms")).toBeNull();
    expect(fit.closest(".hm-fit")).toBeTruthy();
  });

  it("frames architecture on a 390 viewport without waiting for a mystery pan", async () => {
    stubViewport(390);
    renderExplorer(
      { status: "ready", graph: "architecture" },
      { width: 390, height: 844, search: "?graph=architecture" },
    );
    await waitFor(() => {
      expect(String(document.body.getAttribute("data-center") || "")).toMatch(/0\.4/);
    });
    expect(screen.getByRole("button", { name: /sqlite backlog graph/i })).toBeInTheDocument();
  });

  it("does not hand touch moves to page scroll", () => {
    renderExplorer(SAMPLE_CAMPAIGN);
    const canvas = screen.getByTestId("graph-canvas");
    const touch = new Event("touchmove", { bubbles: true, cancelable: true });
    canvas.dispatchEvent(touch);
    expect(touch.defaultPrevented).toBe(true);
  });
});
