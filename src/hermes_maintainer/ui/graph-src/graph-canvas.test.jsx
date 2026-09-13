import { act, cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SAMPLE_CAMPAIGN } from "./fixtures.js";
import { GraphCanvas } from "./GraphCanvas.jsx";
import { architectureGraph, layoutGraph, toFlowEdges, ZOOM_STOPS } from "./graph-model.js";

function renderFlow(graph = SAMPLE_CAMPAIGN, extra = {}) {
  const nodes = layoutGraph(graph.graph === "architecture" ? architectureGraph() : graph);
  const edges = toFlowEdges((graph.graph === "architecture" ? architectureGraph() : graph).relations);
  let api;
  const onReady = (instance) => {
    api = instance;
    extra.onReady?.(instance);
  };
  const view = render(
    <div className="hm-flow-host" style={{ width: 1280, height: 800 }}>
      <GraphCanvas nodes={nodes} edges={edges} onReady={onReady} {...extra} />
    </div>,
  );
  return { ...view, getApi: () => api };
}

describe("GraphCanvas (real xyflow)", () => {
  afterEach(() => {
    cleanup();
  });
  it("mounts the real flow with nodes and edges", async () => {
    renderFlow();
    expect(document.querySelector(".react-flow")).toBeTruthy();
    await waitFor(() => {
      expect(screen.getByText(/cancelled ci treated as success/i)).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /^fixes$/i })).toBeInTheDocument();
  });

  it("selects an architecture node through a real control, not a poster", async () => {
    const onNodeClick = vi.fn();
    renderFlow({ graph: "architecture", relations: architectureGraph().relations, nodes: architectureGraph().nodes }, { onNodeClick });
    const button = await screen.findByRole("button", { name: /sqlite backlog graph/i });
    expect(button.tagName).toBe("BUTTON");
    fireEvent.click(button);
    expect(onNodeClick).toHaveBeenCalled();
  });

  it("keeps hit targets working after zoom stops and fit-view", async () => {
    const onNodeClick = vi.fn();
    const { getApi } = renderFlow(SAMPLE_CAMPAIGN, { onNodeClick });
    await screen.findByRole("button", { name: /cancelled ci treated as success/i });
    await waitFor(() => expect(getApi()).toBeTruthy());

    for (const zoom of ZOOM_STOPS) {
      await act(async () => {
        await getApi().setViewport({ x: 80, y: 40, zoom });
      });
      const button = screen.getByRole("button", { name: /cancelled ci treated as success/i });
      expect(button).toBeVisible();
      onNodeClick.mockClear();
      fireEvent.click(button);
      expect(onNodeClick).toHaveBeenCalled();
    }

    await act(async () => {
      getApi().fitView({ padding: 0.2 });
    });
    onNodeClick.mockClear();
    fireEvent.click(screen.getByRole("button", { name: /composite ci gate/i }));
    expect(onNodeClick).toHaveBeenCalled();
  });

  it("locks the pane against page scrolling and exposes pinch/pan", () => {
    renderFlow();
    const flow = document.querySelector(".hm-flow") || document.querySelector(".react-flow");
    expect(flow).toBeTruthy();
    expect(flow.style.touchAction === "none" || flow.getAttribute("data-touch-action") === "none").toBe(true);
    expect(flow.getAttribute("data-zoom-on-pinch")).toBe("true");
  });

  it("activates a focused node with keyboard from the real wrapper", async () => {
    const onNodeClick = vi.fn();
    const user = userEvent.setup();
    renderFlow(SAMPLE_CAMPAIGN, { onNodeClick });
    const button = await screen.findByRole("button", { name: /cancelled ci treated as success/i });
    button.focus();
    expect(button).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(onNodeClick).toHaveBeenCalled();
  });

  it("activates a focused edge with Enter and Space", async () => {
    const onEdgeClick = vi.fn();
    const user = userEvent.setup();
    renderFlow(SAMPLE_CAMPAIGN, { onEdgeClick });
    const edge = await screen.findByRole("button", { name: /^fixes$/i });
    edge.focus();
    expect(edge).toHaveFocus();
    await user.keyboard("{Enter}");
    expect(onEdgeClick).toHaveBeenCalled();
    onEdgeClick.mockClear();
    edge.focus();
    await user.keyboard(" ");
    expect(onEdgeClick).toHaveBeenCalled();
  });

  it("hides MiniMap at 2× on desktop so it cannot cover nodes", async () => {
    window.matchMedia = (query) => ({
      matches: String(query).includes("min-width"),
      media: query,
      onchange: null,
      addListener() {},
      removeListener() {},
      addEventListener() {},
      removeEventListener() {},
      dispatchEvent() {
        return false;
      },
    });
    const atOne = renderFlow(SAMPLE_CAMPAIGN, { zoom: 1 });
    await screen.findByRole("button", { name: /cancelled ci treated as success/i });
    expect(document.querySelector(".hm-flow")?.getAttribute("data-minimap")).toBe("on");
    atOne.unmount();
    renderFlow(SAMPLE_CAMPAIGN, { zoom: 2 });
    await screen.findByRole("button", { name: /cancelled ci treated as success/i });
    expect(document.querySelector(".hm-flow")?.getAttribute("data-minimap")).toBe("off");
    expect(document.querySelector(".react-flow__minimap")).toBeNull();
  });

  it("hides MiniMap on a dense campaign grid so it cannot cover tickets", async () => {
    window.matchMedia = (query) => ({
      matches: String(query).includes("min-width"),
      media: query,
      onchange: null,
      addListener() {},
      removeListener() {},
      addEventListener() {},
      removeEventListener() {},
      dispatchEvent() {
        return false;
      },
    });
    const nodes = Array.from({ length: 40 }, (_, index) => ({
      id: `issue:${index + 1}`,
      kind: "issue",
      number: index + 1,
      title: `ticket ${index + 1}`,
    }));
    renderFlow({ status: "ready", graph: "campaign", nodes, relations: [] }, { zoom: 1 });
    await screen.findByRole("button", { name: "ticket 1", exact: true });
    expect(document.querySelector(".hm-flow")?.getAttribute("data-minimap")).toBe("off");
  });

  it("hides xyflow Controls on a compact viewport so they cannot cover nodes", async () => {
    window.matchMedia = (query) => ({
      matches: false,
      media: query,
      onchange: null,
      addListener() {},
      removeListener() {},
      addEventListener() {},
      removeEventListener() {},
      dispatchEvent() {
        return false;
      },
    });
    renderFlow(SAMPLE_CAMPAIGN, { zoom: 1 });
    await screen.findByRole("button", { name: /cancelled ci treated as success/i });
    expect(document.querySelector(".react-flow__controls")).toBeNull();
    expect(document.querySelector(".hm-flow")?.getAttribute("data-controls")).toBe("off");
  });

  it("does not render relation labels on a dense campaign grid", async () => {
    const nodes = Array.from({ length: 40 }, (_, index) => ({
      id: `issue:${index + 1}`,
      kind: "issue",
      number: index + 1,
      title: `ticket ${index + 1}`,
    }));
    const relations = Array.from({ length: 12 }, (_, index) => ({
      id: `r-${index}`,
      src_id: `issue:${index + 2}`,
      dst_id: `issue:${index + 1}`,
      relation_type: "fixes",
    }));
    const hideLabels = nodes.length > 24;
    const { GraphCanvas: Canvas } = await import("./GraphCanvas.jsx");
    const { toFlowEdges: edgesOf, layoutGraph: layout } = await import("./graph-model.js");
    render(
      <div className="hm-flow-host" style={{ width: 1280, height: 800 }}>
        <Canvas nodes={layout({ nodes, relations })} edges={edgesOf(relations, { hideLabels })} />
      </div>,
    );
    await screen.findByRole("button", { name: "ticket 1", exact: true });
    expect(screen.queryByRole("button", { name: /^fixes$/i })).not.toBeInTheDocument();
  });
});
