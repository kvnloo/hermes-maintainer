import { describe, expect, it } from "vitest";
import { SAMPLE_CAMPAIGN } from "./fixtures.js";
import {
  FLOW_GESTURES,
  HIT_MIN_PX,
  ZOOM_STOPS,
  architectureGraph,
  hitSizeForZoom,
  labelScaleForZoom,
  layoutGraph,
  parseGraphSearch,
  serializeGraphSearch,
  toFlowEdges,
} from "./graph-model.js";

describe("graph model", () => {
  it("exposes the inspection zoom stops including fit-view", () => {
    expect(ZOOM_STOPS).toEqual([0.4, 0.75, 1, 1.5, 2]);
  });

  it("keeps pinch/pan native and blocks page scroll on the canvas", () => {
    expect(FLOW_GESTURES.zoomOnPinch).toBe(true);
    expect(FLOW_GESTURES.panOnScroll).toBe(true);
    expect(FLOW_GESTURES.preventScrolling).toBe(true);
    expect(FLOW_GESTURES.minZoom).toBe(0.4);
    expect(FLOW_GESTURES.maxZoom).toBe(2);
    expect(FLOW_GESTURES.nodesFocusable).toBe(true);
    expect(FLOW_GESTURES.edgesFocusable).toBe(true);
    expect(FLOW_GESTURES.touchAction).toBe("none");
  });

  it("layouts campaign nodes and typed edges", () => {
    const nodes = layoutGraph(SAMPLE_CAMPAIGN);
    const edges = toFlowEdges(SAMPLE_CAMPAIGN.relations);
    expect(nodes.map((node) => node.id)).toEqual(
      expect.arrayContaining([
        "issue:98557",
        "pr:103195",
        "campaign:ci-verdict-integrity",
        "file:.github/workflows/ci.yaml",
        "invariant:ci-verdict",
      ]),
    );
    expect(nodes.every((node) => Number.isFinite(node.position.x) && Number.isFinite(node.position.y))).toBe(true);
    expect(nodes.every((node) => (node.style?.minHeight ?? 0) >= HIT_MIN_PX / 0.4)).toBe(true);
    expect(edges).toHaveLength(2);
    expect(edges[0]).toMatchObject({ source: "pr:103195", target: "issue:98557", label: "fixes" });
    expect(edges.every((edge) => edge.selectable && edge.interactionWidth >= 24)).toBe(true);
  });

  it("returns no flow nodes for an empty campaign slice", () => {
    expect(layoutGraph({ nodes: [], relations: [] })).toEqual([]);
    expect(toFlowEdges([])).toEqual([]);
  });

  it("builds an interactive architecture graph with subsystems, files, and invariants", () => {
    const graph = architectureGraph();
    const ids = graph.nodes.map((node) => node.id);
    expect(ids).toEqual(
      expect.arrayContaining([
        "arch:github-api",
        "arch:sqlite-backlog",
        "arch:campaigns",
        "arch:local-ui",
        "file:graph/store.py",
        "invariant:evidence-before-closure",
      ]),
    );
    expect(graph.nodes.every((node) => ["subsystem", "file", "invariant", "campaign"].includes(node.kind))).toBe(true);
    expect(graph.relations.length).toBeGreaterThan(8);
    const laid = layoutGraph(graph);
    expect(laid.every((node) => node.type === "hermes")).toBe(true);
  });

  it("keeps labels and hit targets usable at every inspection zoom", () => {
    for (const zoom of ZOOM_STOPS) {
      const visualHit = hitSizeForZoom(zoom) * zoom;
      const visualFont = 13 * labelScaleForZoom(zoom) * zoom;
      expect(visualHit).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
      expect(visualFont).toBeGreaterThanOrEqual(11);
    }
  });

  it("round-trips graph deep links", () => {
    expect(parseGraphSearch("?graph=architecture&node=arch:sqlite-backlog")).toEqual({
      graph: "architecture",
      node: "arch:sqlite-backlog",
    });
    expect(serializeGraphSearch({ graph: "campaign", node: "issue:98557" })).toBe(
      "?graph=campaign&node=issue%3A98557",
    );
  });
});
