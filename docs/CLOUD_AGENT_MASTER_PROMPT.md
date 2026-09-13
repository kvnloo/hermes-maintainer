# Master prompt for Codex / Cursor cloud agents

You are working on `hermes-maintainer`, a local-first repository maintenance intelligence system
for `NousResearch/hermes-agent`.

Read in this order:

1. `README.md`
2. `docs/MASTER_PLAN.md`
3. `docs/ARCHITECTURE.md`
4. `docs/SECURITY.md`
5. `docs/AGENT_CONTRACT.md`
6. your assigned file in `tasks/`
7. `seed/audit/HERMES_TRIAGE_AUDIT.md` only for historical context and campaign seeds

The product goal is to make integration of existing useful work cheaper and more reliable than
opening another overlapping PR. The durable model is a typed backlog graph over issues, PRs,
commits, evidence, campaigns, and fix atoms.

Do not broaden your task. Do not add GitHub write actions. Do not replace deterministic evidence
with model confidence. Do not collapse `similar`, `duplicate`, `same root cause`, `partial`, and
`superseded` into one relation.

Before coding:

- inspect existing code for a reusable primitive;
- identify the exact contract your task owns;
- add a focused failing test when practical;
- avoid introducing a new service or dependency unless the task requires it.

At completion, return:

```text
Scope completed:
Files changed:
Tests/commands:
Results:
Behavioral evidence:
Unresolved risks:
Overlapping work discovered:
Recommended next packet:
```
