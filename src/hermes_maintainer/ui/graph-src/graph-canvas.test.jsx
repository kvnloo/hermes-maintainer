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
});
