import { describe, expect, it, vi } from "vitest";
import { NAMESPACED_CAMPAIGN, SAMPLE_CAMPAIGN, stackedFixesCampaign } from "./fixtures.js";
import {
  ARCHITECTURE_FOCUS_ID,
  FLOW_GESTURES,
  HIT_MIN_PX,
  NODE_CENTER,
  NODE_MIN_HEIGHT,
  NODE_MIN_WIDTH,
  ZOOM_STOPS,
  architectureGraph,
  edgeLabelHitForZoom,
  edgeLabelInvScale,
  findNodeBySearch,
  formatNodeHeading,
  formatNodeKicker,
  frameGraph,
  hitSizeForZoom,
  labelScaleForZoom,
  layoutGraph,
  nodeIdMatches,
  parseGraphSearch,
  repoFromNodeId,
  serializeGraphSearch,
  shortNodeId,
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
    const sampleEdge = toFlowEdges(SAMPLE_CAMPAIGN.relations)[0];
    for (const zoom of ZOOM_STOPS) {
      const visualHit = hitSizeForZoom(zoom) * zoom;
      const visualFont = 13 * labelScaleForZoom(zoom) * zoom;
      const edgeHit = sampleEdge.interactionWidth * zoom;
      const edgeFont = 11 * edgeLabelInvScale(zoom) * zoom;
      const edgeLabelHit = edgeLabelHitForZoom(zoom) * zoom;
      expect(visualHit).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
      expect(visualFont).toBeGreaterThanOrEqual(11);
      expect(edgeHit).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
      expect(edgeFont).toBeGreaterThanOrEqual(11 - 0.05);
      expect(edgeLabelHit).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
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
    expect(
      serializeGraphSearch({ graph: "campaign", node: "acme/widgets:issue:98557" }),
    ).toBe("?graph=campaign&node=acme%2Fwidgets%3Aissue%3A98557");
  });

  it("matches short issue:N queries onto namespaced owner/name:issue:N ids", () => {
    expect(shortNodeId("acme/widgets:issue:98557")).toBe("issue:98557");
    expect(shortNodeId("issue:98557")).toBe("issue:98557");
    expect(repoFromNodeId("acme/widgets:issue:98557")).toBe("acme/widgets");
    expect(nodeIdMatches("acme/widgets:issue:98557", "issue:98557")).toBe(true);
    expect(nodeIdMatches("acme/widgets:issue:98557", "acme/widgets:issue:98557")).toBe(true);
    expect(nodeIdMatches("acme/widgets:issue:98557", "other/lib:issue:98557")).toBe(false);
    expect(nodeIdMatches("acme/widgets:issue:10", "issue:1")).toBe(false);
    const found = findNodeBySearch(layoutGraph(NAMESPACED_CAMPAIGN), "issue:98557");
    expect(found?.id).toBe("acme/widgets:issue:98557");
  });

  it("puts the repo in ticket kickers and headings so --repo ids are not issue:N-only", () => {
    const issue = NAMESPACED_CAMPAIGN.nodes.find((node) => node.kind === "issue");
    expect(formatNodeKicker(issue)).toMatch(/acme\/widgets/i);
    expect(formatNodeKicker(issue)).toMatch(/issue #98557/i);
    expect(formatNodeHeading(issue)).toMatch(/issue #98557/i);
    expect(formatNodeHeading(issue)).toMatch(/acme\/widgets/i);
    expect(formatNodeHeading({ kind: "pr", number: 7, repo: "hyprwm/Hyprland", id: "hyprwm/Hyprland:pr:7" })).toMatch(
      /hyprwm\/Hyprland/i,
    );
  });

  it("keeps stacked fixes labels on distinct hit boxes at every zoom stop", () => {
    const edges = toFlowEdges(stackedFixesCampaign(6).relations);
    expect(edges).toHaveLength(6);
    const offsets = edges.map((edge) => Number(edge.data?.labelOffset) || 0);
    expect(new Set(offsets).size).toBe(edges.length);
    for (const zoom of ZOOM_STOPS) {
      const cssHit = edgeLabelHitForZoom(zoom);
      expect(cssHit * zoom).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
      const visualGaps = offsets
        .slice()
        .sort((a, b) => a - b)
        .map((offset, index, list) => (index === 0 ? Infinity : (offset - list[index - 1]) * zoom));
      visualGaps.slice(1).forEach((gap) => {
        expect(gap).toBeGreaterThanOrEqual(HIT_MIN_PX - 0.05);
      });
    }
  });

  it("frames compact architecture onto the sqlite core instead of an empty corner", () => {
    const setCenter = vi.fn();
    const fitView = vi.fn();
    const api = {
      getNode: (id) => (id === ARCHITECTURE_FOCUS_ID ? { position: { x: 280, y: 510 } } : undefined),
      setCenter,
      fitView,
    };
    frameGraph(api, "architecture", { compact: true });
    expect(setCenter).toHaveBeenCalled();
    const [x, y, opts] = setCenter.mock.calls[0];
    expect(x).toBe(280 + NODE_CENTER.x);
    expect(y).toBe(510 + NODE_CENTER.y);
    expect(opts.zoom).toBe(0.4);
    expect(fitView).not.toHaveBeenCalled();
  });
});
