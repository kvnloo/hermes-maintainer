import json
from pathlib import Path

root = Path('/mnt/data/hermes_triage_audit')
H = '205645ee424163c7b6cfc032c331c3557797497b'
O = '95daf90670b7c039c436c85537da5fbfe2205b41'
G = '9c1b0a610534d6f8120964cf2672c07807d8fc90'
S = '50666ae0b9a51e260b52b7efbab2e4e020346e94'

def blob(repo, sha, path):
    return f'https://github.com/{repo}/blob/{sha}/{path}'

workflows = ['case-collision-check.yml', 'ci-review-comment.yml', 'ci.yaml', 'contributor-check.yml', 'deploy-site.yml', 'docker-lint.yml', 'docker.yml', 'docs-site-checks.yml', 'e2e-desktop.yml', 'history-check.yml', 'infographic-check.yml', 'install-e2e-macos-run.yml', 'install-e2e-run.yml', 'install-e2e-windows-run.yml', 'install-e2e.yml', 'installer-tests.yml', 'js-autofix.yml', 'js-tests.yml', 'label-rerun.yml', 'lint.yml', 'lockfile-diff.yml', 'nix.yml', 'osv-scanner.yml', 'plugin-catalog-ci.yml', 'profile-artifact-check.yml', 'publish-e2e-evidence.yml', 'review-labels.yml', 'rust-tests.yml', 'skills-index-freshness.yml', 'skills-index.yml', 'supply-chain-audit.yml', 'tests-os.yml', 'tests.yml', 'uv-lockfile-check.yml', 'windows-venv-e2e.yml']
assert len(workflows) == 35
sources = {
 'H_POLICY': blob('NousResearch/hermes-agent', H, 'AGENTS.md'),
 'H_CI': blob('NousResearch/hermes-agent', H, '.github/workflows/ci.yaml'),
 'H_COMMENT': blob('NousResearch/hermes-agent', H, '.github/workflows/ci-review-comment.yml'),
 'H_LABEL': blob('NousResearch/hermes-agent', H, '.github/workflows/review-labels.yml'),
 'H_RERUN': blob('NousResearch/hermes-agent', H, '.github/workflows/label-rerun.yml'),
 'H_WORKFLOW_TREE': 'https://api.github.com/repos/NousResearch/hermes-agent/git/trees/c2474998de03e4e12c8f1a6acff37531f8b4255a',
 'O_DUPLICATES': blob('anomalyco/opencode', O, '.github/workflows/duplicate-issues.yml'),
 'O_TRIAGE': blob('anomalyco/opencode', O, '.opencode/agent/triage.md'),
 'O_ISSUE_FIRST': blob('anomalyco/opencode', O, 'CONTRIBUTING.md'),
 'O_CLOSE_PRS_WORKFLOW': blob('anomalyco/opencode', O, '.github/workflows/close-prs.yml'),
 'O_CLOSE_PRS': blob('anomalyco/opencode', O, 'script/github/close-prs.ts'),
 'O_CLOSE_ISSUES': blob('anomalyco/opencode', O, 'script/github/close-issues.ts'),
 'O_COMPLIANCE': blob('anomalyco/opencode', O, '.github/workflows/compliance-close.yml'),
 'G_ORCHESTRATOR': blob('google-gemini/gemini-cli', G, 'tools/caretaker-agent/cloudrun/triage-worker/.gemini/triage_orchestrator.md'),
 'G_WORKER': blob('google-gemini/gemini-cli', G, 'tools/caretaker-agent/cloudrun/triage-worker/main.py'),
 'G_JUDGE': blob('google-gemini/gemini-cli', G, 'tools/caretaker-agent/evals/triage/judge.md'),
 'S_POLICY': blob('aaif-goose/goose', S, 'CONTRIBUTING.md'),
 'GH_AW': 'https://github.github.com/gh-aw/introduction/architecture/',
 'GH_AW_README': 'https://github.com/github/gh-aw/blob/main/README.md',
 'GH_ISSUES_API': 'https://docs.github.com/en/rest/issues/issues',
 'GH_MERGE_QUEUE': 'https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue',
 'GIT_PATCH_ID': 'https://git-scm.com/docs/git-patch-id',
 'SQLITE_FTS5': 'https://www.sqlite.org/fts5.html',
 'CP_SAT': 'https://developers.google.com/optimization/cp/cp_solver',
 'PR98563': 'https://github.com/NousResearch/hermes-agent/pull/98563',
 'PR98684': 'https://github.com/NousResearch/hermes-agent/pull/98684',
 'PR103195': 'https://github.com/NousResearch/hermes-agent/pull/103195',
 'PR108055': 'https://github.com/NousResearch/hermes-agent/pull/108055',
 'PR108055_SOURCE': blob('crazyief/hermes-agent', 'c907c76a4fae8aaef29158ba8fb9041ccaade233', '.github/workflows/ci.yaml'),
 'PR109093': 'https://github.com/NousResearch/hermes-agent/pull/109093',
 'PR91293': 'https://github.com/NousResearch/hermes-agent/pull/91293',
 'PR106742': 'https://github.com/NousResearch/hermes-agent/pull/106742',
}
(root / 'sources.json').write_text(json.dumps(sources, indent=2) + '\n')
coverage = {
 'audit_date_local': '2026-09-12',
 'timezone': 'America/Chicago',
 'pins': {'hermes_main': H, 'opencode_dev': O, 'gemini_cli_search_snapshot': G, 'goose_search_snapshot': S},
 'complete_inventory': {'hermes_workflow_filenames': workflows, 'count': len(workflows)},
 'content_review': 'Selected repository policies, automation source, and competing PR patches. Not all inventoried files were read in full.',
 'backlog_scope': 'Targeted issue/PR families and earlier aggregate search counts. Not a complete paginated census or full comment/commit graph.',
 'local_execution': '16 isolated source-predicate, reduced-YAML, and synthetic-pagination probes; no full repository suite.',
 'constraints': 'No local clone or full source archive obtained; container network access was unavailable.',
 'mutations': [],
 'not_established': ['complete backlog coverage', 'effective branch-protection configuration', 'deployment configuration of Hermes sweeper', 'comparative bot effectiveness', 'globally optimal commit subset', 'merge readiness of any candidate'],
 'prior_statistical_correction': 'Counts of still-open items created since a date are surviving cohorts, not total inflow; no net-arrival/closure rate was established.',
}
(root / 'scan_coverage.json').write_text(json.dumps(coverage, indent=2) + '\n')
seed = {
 'schema_version': 1,
 'status': 'hand-curated audit seeds, not exhaustive automated clustering',
 'publication_mode': 'read_only',
 'baseline_sha': H,
 'families': [
  {
   'id': 'ci-verdict-integrity', 'canonical_issue': 98557,
   'invariant': 'A required cancelled or unknown CI result cannot be accepted as a successful verification.',
   'evidence_level': 'source_inspected_plus_isolated_probe',
   'candidate_prs': [
    {'number': 98563, 'head_sha': '68ca8e5b9ea2ec6be9fb4eecafef67ff2cd5896f', 'role': 'minimal_predicate_donor', 'observed_mergeable': False, 'notes': 'Allowlist success/skipped. Does not carry the complete composite lifecycle changes.'},
    {'number': 98684, 'head_sha': None, 'role': 'overlapping_predicate', 'notes': 'Inspected patch also changes model pricing. Full PR must not be treated as a CI-only atom.'},
    {'number': 103195, 'head_sha': None, 'role': 'composite_campaign_candidate', 'observed_mergeable': False, 'notes': 'Gate, reusable-workflow concurrency, status reporting and tests. Whole candidate not executed.'},
    {'number': 108055, 'head_sha': 'c907c76a4fae8aaef29158ba8fb9041ccaade233', 'role': 'overlapping_predicate', 'observed_mergeable': False, 'notes': 'Unindented assignment escapes YAML block scalar at inspected head; reduced-fragment parser probe fails.'},
   ],
   'proposal': 'Reconcile the existing composite campaign, separating distinct improvements from duplicate gate predicates. No new competing PR.',
   'closure_ready': False,
   'required_validation': ['current-main reproduction', 'trusted YAML/action validation', 'gate and comment verdict parity', 'exact integration-tree tests', 'maintainer CI-sensitive review'],
  },
  {
   'id': 'mcp-oauth-issuer-relay', 'canonical_issue': None,
   'related_issues': [105895, 92758],
   'candidate_prs': [109093, 105610, 108420, 108455, 106634, 92765],
   'evidence_level': 'author_explicit_overlap_claim',
   'head_observed': {'109093': '5f37887af4408d6d5b74abe4170cbd640d1d7d1e'},
   'proposal': 'Compare coverage per callback route and preserve SDK issuer validation. Do not infer all six proposals are complete duplicates.',
   'closure_ready': False,
  },
  {
   'id': 'profile-child-environment-provenance', 'canonical_issue': 82936,
   'candidate_prs': [94878, 91293, 83007],
   'evidence_level': 'author_description_of_recorded_survivor_decision',
   'head_observed': {'91293': '5f65be3f8b09f9d20237bc6c1bb392bf432a8ba2'},
   'recorded_survivor': 94878,
   'proposal': 'Reconcile refreshed donor work into the selected composite and validate that exact tree. Donor test results do not certify the composite.',
   'closure_ready': False,
  },
  {
   'id': 'session-runtime-authority', 'canonical_issue': None,
   'candidate_prs': [106742, 109338, 109403, 109404, 109405, 109412],
   'evidence_level': 'previous_turn_pr_description_and_metadata',
   'proposal': 'Model incorporated commits separately from remaining contributor deltas. Preserve explicit standalone serve/remote gaps.',
   'closure_ready': False,
  },
 ]
}
(root / 'campaign_seeds.json').write_text(json.dumps(seed, indent=2) + '\n')
print('Coverage and campaign seeds written.')
