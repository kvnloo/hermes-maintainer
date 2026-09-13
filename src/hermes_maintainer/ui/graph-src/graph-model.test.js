import { describe, expect, it } from "vitest";
import { SAMPLE_CAMPAIGN } from "./fixtures.js";
import {
  FLOW_GESTURES,
  HIT_MIN_PX,
  NODE_MIN_HEIGHT,
  NODE_MIN_WIDTH,
  ZOOM_STOPS,
  architectureGraph,
  edgeLabelInvScale,
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
      const edgeScreen = HIT_MIN_PX * edgeLabelInvScale(zoom) * zoom;
      expect(visualHit).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
      expect(visualFont).toBeGreaterThanOrEqual(11);
      expect(edgeScreen).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
    }
  });

  it("packs several campaign families into a grid that still fits at 0.4 zoom", () => {
    const nodes = [];
    for (const family of ["a", "b", "c", "d"]) {
      nodes.push({
        id: `campaign:${family}`,
        kind: "campaign",
        campaign_id: family,
        title: family,
      });
      nodes.push({
        id: `issue:${family}`,
        kind: "issue",
        campaign_id: family,
        title: `${family} issue`,
        role: "canonical_problem",
      });
      for (let index = 0; index < 4; index += 1) {
        nodes.push({
          id: `pr:${family}-${index}`,
          kind: "pr",
          campaign_id: family,
          title: `${family} pr ${index}`,
          role: "survivor",
        });
      }
    }
    const laid = layoutGraph({ nodes });
    const minX = Math.min(...laid.map((node) => node.position.x));
    const maxX = Math.max(...laid.map((node) => node.position.x));
    const minY = Math.min(...laid.map((node) => node.position.y));
    const maxY = Math.max(...laid.map((node) => node.position.y));
    const width = maxX - minX + NODE_MIN_WIDTH;
    const height = maxY - minY + NODE_MIN_HEIGHT;
    expect(width * 0.4).toBeLessThan(1280);
    expect(height * 0.4).toBeLessThan(720);
    expect(laid).toHaveLength(nodes.length);
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
