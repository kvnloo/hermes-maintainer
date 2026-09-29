# Hermes contributor / maintainer network cache

As of: 2026-09-29
Source: Deep Research + connected GitHub verification
Target repo: NousResearch/hermes-agent
Operator identity used for interaction mapping: @kvnloo

## Data-quality boundary

This is a collaboration cache, not an exact lifetime commit leaderboard. The canonical GitHub contributor-statistics endpoint was not available during the research run. Rankings combine official Hermes release-note contribution counts, current-release activity, merged/salvaged work, review/triage activity, and direct @kvnloo interaction history. Bots/automated triage are not treated as human endorsement.

## Highest-value collaboration map

| Person | Evidence-backed domain | Current relationship with @kvnloo | Working-style evidence | UX/TUI relevance |
|---|---|---|---|---|
| @OutThisLife (Brooklyn) | TUI, CLI, Desktop/product UX, packaging | Direct interaction on #97505 and #112410; has closed/superseded some work after upstream equivalents landed | Current-main/product-state oriented; pushes against stale inventories; high-volume integration work | Very high |
| @harshmoney123 | Perf, architecture, UX-engineering review | Responded to #99773; reviewed #127152 | Explicitly endorsed measured mechanism -> bounded slice -> invariant test; asked for ~3 open PRs and design agreement before #113241 code | Very high |
| @teknium1 | Core architecture/product/triage | Direct responses on #116620, #116991 and many cleanup/reliability threads; repeated salvage/closure patterns | Favors concrete observed seam + local invariant; rejects generalized harnesses without repeated bug evidence | High / gatekeeper |
| @austinpickett | TUI/CLI/session/input/config UX | No direct @kvnloo engagement found | Official release notes show a large TUI/CLI contribution stream | Very high |
| @kshitijk4poor | Core implementation/refactoring | #120677 useful kernel incorporated into #121421 with authorship preserved | Will salvage separable correct kernels and discard over-broad/failed experiments | Medium-high |
| @kyssta-exe | Model/TUI technical review | Substantive review of #111470 | Detailed semantic/code-path review | High for model picker |
| @arkheioncorp | Review/current development | Approved #127334 | Responded well to explicit spatial invariant: 1 column / 0 rows | High for composer/layout |
| @bittermelonz | Desktop/TUI/UX | No direct hit found | Release-note evidence of product-facing Desktop/TUI work | High |
| @mikolajczyk-a | CLI/TUI/Desktop UX | No direct hit found | Release-note evidence: usage/TUI/Desktop pane work | High |
| @meep-the-viking | terminal/REPL UX | No direct hit found | Release-note evidence of substantial terminal/REPL work | High |
| @Johnpapsal | TUI/telemetry/tests | No direct hit found | Repeated TUI contribution stream | High |
| @hosseinaghajaniabbasi | TUI/theme/progress UX/tests | No direct hit found | Progress/gauge/theme work | High |
| @azimjohn | terminal UX/Docker | No direct hit found | Terminal-specific UX work | Medium-high |
| @adals | TUI/slash commands/docs UX | No direct hit found | Terminal command-path fixes | Medium-high |
| @helix4u | current mixed development | No direct hit found | Current-release activity | Medium until domain evidence improves |
| @alt-glitch | triage/design | Several @kvnloo issue interactions | Some comments explicitly AI-generated; weight as triage signal, not personal endorsement | Medium |
| @whyyagswhy | technical review | Repeated review overlap | Exact-head verification / technical review pattern | Medium-high |

## Verified release-window volume leaders

These are release-window counts, not lifetime totals.

- @OutThisLife — 52 merged PRs in one documented release window; TUI/CLI/UX-heavy.
- @austinpickett — 17 PRs; TUI/CLI/UX.
- @Conway-Research — 17; web/search/tools.
- @hosseinaghajaniabbasi — 16; TUI/theme/progress UX/memory/tests.
- gamerindreams… — 15; OAuth/cron/docs.
- @Trylooney — 13; infra/retries/SSL/integrations.
- @stephengpope — 11; gateway/integrations/UX.
- @bharatb212 — 9; formatting/cleanup.
- @bittermelonz — 7; Desktop/TUI/UX.
- @bluzername-user — 7; tools/execution/cron.
- @Johnpapsal — 7; TUI/telemetry/tests.
- @mikolajczyk-a — 6; CLI/TUI/Desktop UX.
- @thilak-jinadasa — 6; startup/Docker/providers.
- @NkondaDev — 6; gateway/mobile/Telethon.
- @JohannLai — 5; tools/TUI.
- @AllSeeingEye3 — 5; infra/sandbox/execution.
- @dadukhankh — 5; CLI/agents/terminal.
- @DianCahyadi12 — 5; refactor/cleanup.
- @Ghostlike7 — 4; tests/tools/retries.
- @Antonio-Ricaurte-Grueso — 4; cron/reliability.
- @vikalpr — 4; interruptions/memory/audio.
- @Wut-one — 4; tests/tasks/docs.
- @adals — 3; TUI/slash/docs UX.
- @azimjohn — 3; terminal UX/Docker.
- @meep-the-viking — 3; terminal/REPL/UX.
- @mukesh-sharma2911 — 2; scrollbar/TUI/dependencies.
- @thangvng — 2; model-selection UX.
- @nonkronk — 1; TTY UX.

Additional current-release / relationship cohort includes @teknium1, @harshmoney123, @helix4u, @kshitijk4poor, @arkheioncorp, @kyssta-exe, @alt-glitch, @whyyagswhy, @thefailtheory, @chenlu0701, @Domomw, @0xSero, @wasnvenzorntahr, @Fordeon, @Mitali13, @chetankan12, @pjd820, @5p1d3rman, @RohitDuttaOfficial, @DeepVerse42, @NREL-TenaBrooks, @jamesbking, @matteo-rizzo, @seedevgod, @antonios1194, @The-soul-intern, @chandralegend, @jaydeep-patil1, @farabi10315-a11y, @HusseinMarzoug, @utkarshdd, @omrix00, @PyRayman, @RicardoZeco, @asjohnson123, @jimsanabria, @rdroste, and @ppp-one.

## @kvnloo interaction evidence

### Harsha
- https://github.com/NousResearch/hermes-agent/issues/99773 — explicit endorsement of the measured/bounded UX engineering method; asked to keep ~3 PRs open and hold #113241 implementation until design agreement.
- https://github.com/NousResearch/hermes-agent/pull/127152 — asked whether scrollbar reflow still works without the ticker; the follow-up led to using ScrollBox.subscribe() as the semantic invalidation source.

### Brooklyn / OutThisLife
- https://github.com/NousResearch/hermes-agent/issues/97505 — current-main verification of Desktop model-submenu behavior.
- https://github.com/NousResearch/hermes-agent/issues/112410 — pushed back on a point-in-time stalled-PR inventory as quickly stale/non-actionable.
- Historical PR closures also show a pattern of closing superseded work while crediting upstreamed ideas/authorship.

### Tek
- https://github.com/NousResearch/hermes-agent/issues/116620 — corrected the exact model-validation seam and closed as not-a-bug; discovery remained separate.
- https://github.com/NousResearch/hermes-agent/issues/116991 — declined generalized test infrastructure for a bug class not seen twice; preferred an invariant test at the actual seam when a concrete regression appears.

### kshitijk4poor
- https://github.com/NousResearch/hermes-agent/pull/120677 -> https://github.com/NousResearch/hermes-agent/pull/121421 — retained three core commits/authorship; dropped the managed-Relay/redaction/exception-mapping experiments that were not sound.

### Other useful reviewer edges
- @arkheioncorp approved https://github.com/NousResearch/hermes-agent/pull/127334.
- @kyssta-exe gave substantive review on https://github.com/NousResearch/hermes-agent/pull/111470.
- @alt-glitch has multiple triage interactions, but some are explicitly AI-generated and should not be treated as personal buy-in.

## UX/TUI workstream status

Umbrella: https://github.com/NousResearch/hermes-agent/issues/99773

Maintainer signal:
- Harsha: positive on method.
- Brooklyn/Tek/Austin: no direct RFC response found as of this cache.
- Do not manufacture engagement by broad tagging.

Current useful queue:
1. #127152 — static agents replay clock / ScrollBox semantic invalidation.
2. #127143 — composer queue subscription narrowing.
3. #127170 — theme-only leaf subscription narrowing.
Then rotate:
4. #127334 — composer visual boundary, approved.
5. #111470 — flat fuzzy /model hop, substantive prior review.
Research/design only while queue is full:
- #127449 model selection lost on rebuild.
- #127733 repeated TUI npm install/startup.
- #127805 display.pet.render_mode off contract.
- #113241 agents overlay: design only until agreement.

## Collaboration heuristics

Facts supported by repeated review/triage:
- Current-main repros beat broad parity arguments.
- One measurable mechanism per PR is receiving positive feedback.
- Tests should pin the user/system invariant: row/column cost, notification count, RPC/timer count, or actual state ownership.
- Existing semantic invalidation/event sources are preferred over new caches/timers.
- Small separable kernels survive salvage even when a larger experimental branch does not.
- Keep the visible review queue small.
- Do not use broad tagging to force engagement; join existing threads where technical overlap is real.

Inference:
- The highest-value missing UX relationship is Brooklyn on the current RFC direction.
- Austin is the strongest under-engaged TUI/CLI contributor based on release-note volume.
- Landing the first measured slices is likely a better invitation to those people than another umbrella design comment.

## Domain -> people index

- TUI/terminal architecture: OutThisLife, austinpickett, meep-the-viking, Johnpapsal, mikolajczyk-a, azimjohn, adals.
- Desktop/TUI parity: OutThisLife, bittermelonz, mikolajczyk-a.
- Composer/layout: arkheioncorp, austinpickett, OutThisLife.
- Model picker/switching: kyssta-exe, austinpickett, thangvng, OutThisLife.
- Performance/subscriptions: harshmoney123, Johnpapsal, austinpickett.
- Theme/progress/motion: hosseinaghajaniabbasi, bittermelonz.
- Core architecture/product gate: teknium1.
- Salvage/refactor bridge: kshitijk4poor.
- Technical exact-head review: whyyagswhy, kyssta-exe.
- Triage/design: alt-glitch (with AI-generated-triage caveat).

## Sources

Primary repository:
https://github.com/NousResearch/hermes-agent

Contributing guide:
https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md

Releases:
https://github.com/NousResearch/hermes-agent/releases

This cache should be refreshed as PRs land and ownership shifts.