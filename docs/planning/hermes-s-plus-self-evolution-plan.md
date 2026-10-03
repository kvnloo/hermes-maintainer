# Hermes-Agent S+ Self-Evolution Plan

**Prepared for:** Kevin CoS  
**Date:** 2026-09-14  
**Scope:** First-principles plan to make hermes-agent S+ ready for distributed self-evolutionary development under verified-oss-loop

---

## Executive Summary

**Current state:** Three functional components exist in isolation:
- `kvnloo/hermes-maintainer` — local backlog graph + campaign coordination (M0 shipped, M1-M2 in progress)
- `kvnloo/verified-oss-loop` — contribution protocol kit (v0.1 spec + onboarding automation)
- `kvnloo/kerdoios` — heterogeneous compute router (MVP feature-complete, missing mutation tests)

**Target state (S+):** Community-driven distributed loop where AI agents + contributors can claim roadmap work, execute in isolation, produce revision-bound evidence, pass independent verification, and feed learning back to the roadmap — without self-merge, duplicate work, or unverifiable claims.

**Critical gap:** No live integration on `NousResearch/hermes-agent`. The factory exists (hermes-maintainer scaffold + verified-oss-loop contract), but the origin repository has not onboarded the protocol.

---

## Current State vs S+ Gaps

### ✅ What exists

| Component | Status | Location |
|---|---|---|
| Contribution contract | Shipped | `verified-oss-loop/SPEC.md` |
| Onboarding automation | Shipped | `verified-oss-loop/bin/oss-onboard` |
| Claim lease + expiry | Shipped | Receipt templates, stale automation |
| Evidence receipt | Shipped | `.github/PULL_REQUEST_TEMPLATE.md` (via onboard) |
| Rollout scheme (preview→nightly→dev→main) | Shipped | `.verified-oss-loop/rollout.yml`, 3 automerge workflows |
| Local backlog graph | Shipped | `hermes-maintainer` M0 (SQLite/FTS5, ingestion) |
| Campaign coordination | Partial | M4 design exists; no claim-lease API, no work-packet generator |
| Git mirror + patchID | Shipped | `hermes-maintainer/git/` (M1) |
| Compute allotment | Shipped | `kerdoios` MVP (portfolio planner, no execution) |
| Skills (autodevelop, tdd, verify, anti-slop, orient) | Shipped | `verified-oss-loop/skills/`, copied into repos via onboard |

### ❌ S+ Gaps

| Gap | Impact | Current workaround | Risk |
|---|---|---|---|
| **Harness integration** | Hermes-agent has no E2E evidence runner bound to exact SHAs | Manual local test, CI green != evidence | False positives escape |
| **Evidence engine** | M2 (check-run ingestion, RED/GREEN receipts) not shipped | Template receipt comments, not structured data | Evidence is advisory, not machine-readable |
| **Claim-lease API** | Campaign coordination exists but issues no bounded leases | Manual `gh issue comment`, `gh issue edit --add-label claimed` | Duplicate work / lease expiry not enforced |
| **Work-packet generator** | M4 design exists but no `hermes-maintainer campaign 123 --generate-task` | Humans write task JSON by hand | Blocks full-auto cycle |
| **Kerdoios routing in Hermes** | Kerdoios tools exist but not wired into Hermes agent execution | LiteLLM or naive provider | Cost/capacity advantage unused |
| **Independent verify bot** | Spec calls for separate verifier; none ships | CodeRabbit / Greptile manual enable | Implementer == reviewer |
| **Mutation coverage on kerdoios** | `mutmut` pinned but not run | Unit green, no sabotage tests | Surviving mutants hide missing assertions |
| **Hermes-agent onboarding** | `NousResearch/hermes-agent` has `AGENTS.md` but not `.verified-oss-loop/` kit | Manual contribution flow | Protocol not live on origin |

---

## How the Three Repos Fit Together

```text
┌────────────────────────────────────────────────────────────────┐
│ NousResearch/hermes-agent (origin)                            │
│   Agent runtime + plugins + skills + desktop/TUI              │
│   NOT YET ONBOARDED to verified-oss-loop                      │
└────────────────────────────────────────────────────────────────┘
                           ▲
                           │ (read-only scan)
                           │
┌────────────────────────────────────────────────────────────────┐
│ kvnloo/hermes-maintainer (ops repo)                           │
│   SQLite backlog graph                                         │
│   Campaign coordination (M0-M2 partial)                        │
│   Triage + similarity + optimizer                              │
│   Dashboard UI (xyflow canvas)                                 │
│   Skills: autodevelop, orient, tdd, verify, anti-slop          │
│   OWNS: kit under .verified-oss-loop/                          │
│   WRITES: PRs on kvnloo/hermes-maintainer docs/playbook only   │
└────────────────────────────────────────────────────────────────┘
                           ▲
                           │ (protocol kit)
                           │
┌────────────────────────────────────────────────────────────────┐
│ kvnloo/verified-oss-loop (protocol repo)                      │
│   SPEC.md — contribution contract                              │
│   oss-onboard — auto-setup (AGENTS.md, templates, CI)          │
│   Rollout scheme (rolling / staged / stable)                   │
│   Kit inventory (skills, receipt templates)                    │
│   Does NOT execute work; only defines the loop                 │
└────────────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────────────┐
│ kvnloo/kerdoios (standalone plugin)                           │
│   Heterogeneous compute router                                 │
│   Portfolio planner (N workers, perishable quota, privacy)     │
│   Installs into ~/.hermes/plugins/kerdoios/                    │
│   Hermes executes; Kerdoios only plans                         │
│   UPSTREAM: LiteLLM PRs first (quota pools #31823)             │
└────────────────────────────────────────────────────────────────┘
```

**Integration flow:**

1. `verified-oss-loop/bin/oss-onboard` copies kit → any repo (hermes-agent, hermes-maintainer, kerdoios)
2. `hermes-maintainer` ingests issues/PRs from hermes-agent (read-only), builds campaign graph, proposes work packets
3. Agent claims a task → executes in isolated branch/worktree → produces evidence receipt → independent verify → human merge
4. `kerdoios` tools route LLM calls when Hermes invokes them (`hermes kerdoios plan`)
5. Outcome (KEEP/DISCARD) feeds back into roadmap priority

**Critical insight:** hermes-maintainer is the **factory**. It orchestrates, triages, and proposes. It does NOT rewrite hermes-agent core unless claimed as a task. All writes stay on `kvnloo/*` forks until a human merges onto origin.

---

## Ranked Leaf Work Packages (Easy → Hard)

Each package is a claimable unit with acceptance criteria, evidence, and verify path.

### 1. **[EASY] Kerdoios mutation coverage** 
**Problem:** `kerdoios/ROADMAP.md` says "mutation: not done". Unit tests green but no sabotage tests. Surviving mutants hide missing assertions.

**Acceptance:**
- `mutmut run` on `kerdoios/` passes (or documents n/a + reason)
- PR receipt binds exact head SHA to mutation score
- At minimum: cover `inventory.py` allocate logic, Pareto filter

**Risk:** Low. Kerdoios is standalone; no hermes-agent dependency.

**Suggested verify:** `mutmut run` green → receipt in PR → independent CodeRabbit review

---

### 2. **[EASY] Onboard kerdoios to verified-oss-loop**
**Problem:** Kerdoios has `CONTRIBUTING.md` + `ROADMAP.md` but no `.verified-oss-loop/` kit. Missing: receipt template, autodevelop skill, stale-claim automation.

**Acceptance:**
```bash
cd /path/to/kerdoios
python3 /path/to/verified-oss-loop/bin/oss-onboard . --scheme rolling --with-automation
git diff .verified-oss-loop/ .github/PULL_REQUEST_TEMPLATE.md
```
- Kit copied under `.verified-oss-loop/`
- Receipt template includes RED/GREEN/sabotage fields
- Automerge workflows (preview → nightly) installed
- `rollout.yml` scheme=rolling

**Risk:** Low. Mechanical copy, no code changes.

**Suggested verify:** `bash verified-oss-loop/tests/smoke.sh` on kerdoios tree

---

### 3. **[MEDIUM] Evidence engine — check-run ingestion (M2 partial)**
**Problem:** `hermes-maintainer` M2 design exists but not shipped. Evidence receipts are markdown comments, not structured data bound to SHAs.

**Acceptance:**
- `hermes-maintainer sync --evidence` fetches GitHub check-runs for open PRs
- Stores `evidence` table rows: `(subject_id, evidence_type, level, status, source_sha, payload_json)`
- Dashboard API `GET /evidence/{pr_id}` returns RED/GREEN/sabotage by exact SHA
- Unit test: mock GitHub checks API, assert `evidence.source_sha == head_sha`

**Risk:** Medium. Depends on GitHub API pagination, rate limits, CI matrix explosion.

**Suggested verify:** 
- Unit: mock `GET /repos/{owner}/{repo}/commits/{sha}/check-runs`
- E2E: fetch real check-runs from a known hermes-agent PR (read-only)
- Mutation: sabotage `source_sha` binding assertion

---

### 4. **[MEDIUM] Claim-lease API + expiry automation**
**Problem:** Campaign coordination (M4) design exists but issues no bounded leases. Duplicate work / stale claims are manual.

**Acceptance:**
- `POST /campaigns/{id}/claim` → 201 + `{claimant, base_revision, expires_at, lease_token}`
- Returns 409 if live claim exists and not expired
- Expiry enforced: `DELETE /campaigns/{id}/claim` after 24h (project configurable)
- GitHub issue comment posted: `claiming for autodevelop / claimant: {id} / base: {sha} / expires: {RFC3339}`
- Stale-claim workflow (`stale-labels.yml`) adds `claimable`, removes `claimed` after expiry

**Risk:** Medium. Requires GitHub API write (labels, comments). Race conditions (two agents claim same issue).

**Suggested verify:**
- Unit: claim → 201, second claim → 409, claim after expiry → 201
- E2E: claim real hermes-agent issue (on kvnloo fork, not origin)
- Mutation: sabotage expiry check (`expires_at > now()`)

---

### 5. **[MEDIUM] Work-packet generator for campaigns**
**Problem:** M4 design exists but no `hermes-maintainer campaign 123 --generate-task`. Humans write AODL task JSON by hand.

**Acceptance:**
- `hermes-maintainer campaign {id} --generate-task` outputs JSON:
  ```json
  {
    "campaign_id": "campaign:abc123",
    "issue": 5114,
    "scope": "one sentence",
    "base_revision": "abc123",
    "acceptance": ["test_foo.py passes", "mutation score >= 80%"],
    "suggested_verify": "pytest + mutmut",
    "cost_estimate": {"tokens": 50000, "wall_seconds": 600}
  }
  ```
- Merges campaign canonical issue + roadmap acceptance criteria
- Includes related PRs, stacked dependencies

**Risk:** Medium. Depends on M2 evidence engine (acceptance criteria from receipts).

**Suggested verify:**
- Unit: campaign with 3 PRs → task JSON includes `related_prs`
- E2E: generate task for real hermes-agent campaign (read-only)

---

### 6. **[HARD] Kerdoios integration into Hermes agent**
**Problem:** Kerdoios MVP shipped but not wired into Hermes execution. Tools exist (`hermes kerdoios plan`) but agent loop doesn't route LLM calls through portfolio planner.

**Acceptance:**
- Hermes config: `compute_router: kerdoios` (opt-in)
- Before LLM call: `kerdoios.plan(WorkRequirement) → ExecutionPlan`
- Hermes executes plan (N workers, quota-aware)
- Observed outcome (`success`, `tokens_used`) → `kerdoios.record_outcome()`
- Documented in `hermes-agent/docs/compute-routing.md`

**Risk:** High. Touches Hermes agent core. Requires: AODL work spec, LiteLLM quota-pool PR upstream, perishable-quota state machine.

**Suggested verify:**
- Unit: mock `kerdoios.plan()`, assert Hermes submits N parallel workers
- E2E: run real Hermes task with `KERDOIOS_MODE=cheap`, assert free-tier models used
- Runtime: `hermes serve`, observe `/metrics` quota utilization
- Mutation: sabotage quota-remaining check

---

### 7. **[HARD] Independent verify bot (frozen evaluator)**
**Problem:** Spec says "generation and verification are separate". Current: implementer self-reviews (or CodeRabbit/Greptile manually enabled).

**Acceptance:**
- Standalone verifier bot: `verify-bot` (GitHub App or Action)
- Triggered on PR label `needs-review`
- Reads receipt template, reproduces RED/GREEN at exact `head_revision`
- Posts structured verdict: `APPROVE_EXACT_HEAD` | `CHANGES_REQUIRED` | `DISCARD_*`
- Does NOT auto-merge; only posts review
- Documented in `verified-oss-loop/docs/verify-bot.md`

**Risk:** High. New service, needs secrets (GitHub App key), CI runner quota, deterministic replay.

**Suggested verify:**
- Unit: parse receipt → extract `head_revision`, `red_command`, `green_command`
- E2E: bot reviews real PR on kvnloo fork (not origin)
- Sabotage: bot posts `CHANGES_REQUIRED` when green command fails

---

### 8. **[HARD] Onboard NousResearch/hermes-agent to verified-oss-loop**
**Problem:** Origin `hermes-agent` has `AGENTS.md` but not `.verified-oss-loop/` kit. Protocol not live.

**Acceptance:**
- Fork PR on `NousResearch/hermes-agent` (or Linear HITL → GitHub via `publish-origin-from-hitl.py`)
- Kit installed: `.verified-oss-loop/`, receipt template, automerge workflows
- `rollout.yml` scheme=rolling (or staged, TBD with Nous maintainers)
- `CODEOWNERS` protects `main`, `dev` (no worker merge)
- First claimable issue: from `hermes-agent/ROADMAP.md` or failing test
- Evidence: bot posts claim comment, opens PR on preview, automerge → nightly (after checks)

**Risk:** Very high. Political (Nous approval), scale (13k files), existing contributor habits, rollout complexity.

**Suggested verify:**
- Dry-run: `oss-onboard --dry-run` on hermes-agent fork
- Staged: onboard `kvnloo/hermes-agent` fork first, test full loop (claim → work → evidence → verify → merge preview)
- Shadow: run triage bot in read-only mode for 2 weeks, measure false-positive rate
- Rollout: start with `scheme: stable` (classic PR flow), graduate to `rolling` after 10 successful merges

---

## What NOT to Do

| Anti-pattern | Why | Correct path |
|---|---|---|
| **Spray PRs on origin** | Duplicate work, overwhelms maintainers | Claim lease first; stop if claimed |
| **Self-merge to main/dev** | Bypasses human gate, breaks protocol | Automerge only on preview/nightly (when `rollout.yml` allows) |
| **SQLite replaces Linear** | Hermes-maintainer is read-only triage, not a tracker | Keep Linear/GitHub Issues as source of truth |
| **Grow second LLM gateway in kerdoios** | LiteLLM already routes 100+ providers | Upstream LiteLLM PRs first (quota pools #31823) |
| **Rewrite ROADMAP.md in PRs** | Roadmap is maintainer-owned priority | Triage mints one `needs-discussion` issue, stops |
| **Invent mutation score when `n/a`** | False claim of coverage | Write `n/a` + reason (no mutator for this stack) |
| **Run `gitnexus analyze` as side effect** | Token-expensive, slow | Only when human explicitly asks |
| **Dump pstack/eggbot into tree** | Skills are pointers, not vendored copies | Reference via `skills/{tool}/SKILL.md` |
| **Post on NousResearch issues from fork claim** | Origin is read-only for this loop | All writes on `kvnloo/*` until human merge |
| **Merge preview/nightly yourself** | Automerge is the authorized path | Push to preview; workflow merges it |
| **Claim multiple issues in one pass** | Lease protocol is one-at-a-time | Finish first claim, then claim next |

---

## Integration Sequence (Suggested)

**Phase 1: Kerdoios hardening** (1–2 work units)
1. ✅ Mutation coverage (package 1)
2. ✅ Onboard to verified-oss-loop (package 2)

**Phase 2: Hermes-maintainer evidence engine** (2–3 units)
3. ✅ Evidence ingestion (package 3)
4. ✅ Claim-lease API (package 4)
5. ✅ Work-packet generator (package 5)

**Phase 3: Hermes integration** (3–5 units)
6. ✅ Kerdoios → Hermes wiring (package 6)
7. ✅ Independent verify bot (package 7)

**Phase 4: Origin onboarding** (5–8 units)
8. ✅ Staged onboard on kvnloo fork (shadow mode)
9. ✅ First 10 successful loop cycles (claim → evidence → verify → merge preview)
10. 🎯 Proposal to NousResearch maintainers
11. 🎯 Origin onboard (package 8)

**Estimated scope:** 15–25 claimable work units. Each unit = one isolated PR with evidence receipt. Phases 1–2 can start now (no origin dependency). Phase 4 blocks on Nous approval.

---

## Success Metrics (S+ Threshold)

| Metric | Target | Measurement |
|---|---|---|
| **Duplicate work rate** | < 5% | Claims issued / issues closed by non-claimant |
| **Evidence binding accuracy** | 100% | Receipts reference exact `head_sha` (audit via `git log`) |
| **Lease expiry enforcement** | 100% | Stale claims auto-removed after 24h (CI workflow logs) |
| **Independent verify coverage** | ≥ 80% | PRs reviewed by bot / total PRs |
| **Human merge gate preserved** | 100% | Zero worker merges to `main`/`dev` (GitHub audit log) |
| **Cost advantage (kerdoios)** | ≥ 50% | $ spent vs naive paid-only (when free quota available) |
| **False-positive escape rate** | < 2% | Bugs merged despite green evidence (post-merge bug reports) |
| **Loop cycle time** | < 48h | Claim → evidence → verify → merge (P50, excluding review wait) |

---

## Conclusion

**Bottom line:** The factory exists. The protocol exists. The compute router exists. Integration is mechanical but requires:
1. M2 evidence engine (check-run ingestion)
2. M4 claim-lease API + work-packet generator
3. Independent verify bot
4. Origin onboarding (political + technical)

**Next action:** Pick packages 1–2 (kerdoios mutation + onboard). Token-light, no dependencies, immediate proof. Then evidence engine (package 3). Defer origin onboarding (package 8) until Phases 1–3 prove the loop on forks.

**Risk mitigation:** Start on `kvnloo/*` forks only. Never write to `NousResearch/hermes-agent` until a human approves the onboard proposal. Shadow mode first; production rollout only after 10 successful cycles with zero false-merge escapes.
