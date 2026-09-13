export const SAMPLE_CAMPAIGN = {
  status: "ready",
  graph: "campaign",
  source: "seed",
  campaign: {
    id: "seed:ci-verdict-integrity",
    title: "CI verdict integrity",
    summary: "A cancelled or unknown required check must not count as green.",
  },
  nodes: [
    {
      id: "campaign:ci-verdict-integrity",
      kind: "campaign",
      title: "CI verdict integrity",
      summary: "Reconcile the composite campaign. Do not open another competing PR.",
      role: "campaign",
    },
    {
      id: "issue:98557",
      kind: "issue",
      number: 98557,
      title: "Cancelled CI treated as success",
      role: "canonical_problem",
      state: "open",
      author: "tek",
      url: "https://github.com/NousResearch/hermes-agent/issues/98557",
    },
    {
      id: "pr:103195",
      kind: "pr",
      number: 103195,
      title: "Composite CI gate",
      role: "survivor",
      state: "open",
      author: "tek",
      url: "https://github.com/NousResearch/hermes-agent/pull/103195",
    },
    {
      id: "file:.github/workflows/ci.yaml",
      kind: "file",
      title: "ci.yaml",
      path: ".github/workflows/ci.yaml",
      summary: "Required check workflow whose cancelled/unknown verdict must not pass the gate.",
    },
    {
      id: "invariant:ci-verdict",
      kind: "invariant",
      title: "Cancelled CI is not success",
      summary:
        "A required cancelled or unknown CI result cannot be accepted as a successful verification.",
    },
  ],
  relations: [
    {
      id: "r-fixes",
      src_id: "pr:103195",
      dst_id: "issue:98557",
      relation_type: "fixes",
      confidence: 0.8,
      evidence_level: "source_confirmed",
      evidence: "Composite gate plus tests; still needs an integration tree.",
    },
    {
      id: "r-protects",
      src_id: "invariant:ci-verdict",
      dst_id: "file:.github/workflows/ci.yaml",
      relation_type: "protects",
      confidence: 1,
      evidence_level: "source_confirmed",
      evidence: "The invariant is the acceptance criterion for the workflow gate.",
    },
  ],
};

export const NAMESPACED_CAMPAIGN = {
  status: "ready",
  graph: "campaign",
  source: "live",
  campaign: {
    id: "acme/widgets:campaign:ci-verdict-integrity",
    title: "CI verdict integrity",
    summary: "A cancelled or unknown required check must not count as green.",
  },
  nodes: [
    {
      id: "campaign:ci-verdict-integrity",
      kind: "campaign",
      title: "CI verdict integrity",
      summary: "Reconcile the composite campaign. Do not open another competing PR.",
      role: "campaign",
    },
    {
      id: "acme/widgets:issue:98557",
      kind: "issue",
      repo: "acme/widgets",
      number: 98557,
      title: "Cancelled CI treated as success",
      role: "canonical_problem",
      state: "open",
      author: "tek",
      url: "https://github.com/acme/widgets/issues/98557",
    },
    {
      id: "acme/widgets:pr:103195",
      kind: "pr",
      repo: "acme/widgets",
      number: 103195,
      title: "Composite CI gate",
      role: "survivor",
      state: "open",
      author: "tek",
      url: "https://github.com/acme/widgets/pull/103195",
    },
    {
      id: "file:.github/workflows/ci.yaml",
      kind: "file",
      title: "ci.yaml",
      path: ".github/workflows/ci.yaml",
      summary: "Required check workflow whose cancelled/unknown verdict must not pass the gate.",
    },
    {
      id: "invariant:ci-verdict",
      kind: "invariant",
      title: "Cancelled CI is not success",
      summary:
        "A required cancelled or unknown CI result cannot be accepted as a successful verification.",
    },
  ],
  relations: [
    {
      id: "r-fixes",
      src_id: "acme/widgets:pr:103195",
      dst_id: "acme/widgets:issue:98557",
      relation_type: "fixes",
      confidence: 0.8,
      evidence_level: "source_confirmed",
      evidence: "Composite gate plus tests; still needs an integration tree.",
    },
    {
      id: "r-protects",
      src_id: "invariant:ci-verdict",
      dst_id: "file:.github/workflows/ci.yaml",
      relation_type: "protects",
      confidence: 1,
      evidence_level: "source_confirmed",
      evidence: "The invariant is the acceptance criterion for the workflow gate.",
    },
  ],
};

export function stackedFixesCampaign(count = 6) {
  const nodes = [
    {
      id: "issue:1",
      kind: "issue",
      number: 1,
      title: "Root lock race",
      role: "canonical_problem",
      campaign_id: "c1",
    },
  ];
  const relations = [];
  for (let index = 0; index < count; index += 1) {
    const number = 10 + index;
    nodes.push({
      id: `pr:${number}`,
      kind: "pr",
      number,
      title: `Competing fix ${index}`,
      role: "active_implementation",
      campaign_id: "c1",
    });
    relations.push({
      id: `r-fixes-${index}`,
      src_id: `pr:${number}`,
      dst_id: "issue:1",
      relation_type: "fixes",
      confidence: 0.7,
      evidence_level: "reported",
      evidence: "Competing candidate",
    });
  }
  return { status: "ready", graph: "campaign", nodes, relations, source: "seed" };
}
