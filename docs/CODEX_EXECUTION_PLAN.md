# Parallel Codex / Cursor execution plan

The safest speedup is to parallelize by **orthogonal evidence seam**, not by asking several agents
to implement the whole product.

## Wave 1

Run these in parallel:

1. **Stack/commit mapper**
   - implement `tasks/01_stack_and_patch_identity.md`;
   - no UI changes.
2. **CI evidence ingester**
   - implement `tasks/02_ci_evidence.md`;
   - no optimizer changes.
3. **Similarity evaluator**
   - implement `tasks/03_similarity_eval.md`;
   - no GitHub writes.
4. **Dashboard graph explorer**
   - implement `tasks/04_dashboard_graph.md`;
   - consume existing API contracts only.

Merge only after each task includes tests and a clear scope receipt.

## Wave 2

1. acceptance-criteria model;
2. campaign coordinator;
3. commit-level fix atoms;
4. code-overlap/root-cause miner.

## Wave 3

1. isolated integration worktrees;
2. baseline/candidate test receipts;
3. CP-SAT requires/conflicts model;
4. shadow-mode relationship mapper agent.

## Prompt to hand to a cloud coding agent

Use `docs/AGENT_CONTRACT.md` as the global contract, then append exactly one file from `tasks/`.
Do not ask an agent to "improve hermes-maintainer generally". That invites scope collisions.
