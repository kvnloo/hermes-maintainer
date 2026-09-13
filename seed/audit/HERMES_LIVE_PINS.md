# Hermes-agent live pins (GET 2026-09-13T13:32Z)

Do not treat `seed/audit/HERMES_TRIAGE_AUDIT.md` or `campaign_seeds.json` as current HEAD. Those files pin `205645ee` (2026-09-07) as historical.

| Ref | SHA | When (UTC) | Note |
| --- | --- | --- | --- |
| `main` | `b05a47b9d2df4d62124a80f70d657c6b8e1b07fb` | 2026-09-13T13:11:49Z | Includes #109649 |
| Bot Screen PR | `77123c0ef3e1c24d6712a37720e912f3fc68d9b3` | 2026-09-13T13:30:10Z | [#108914](https://github.com/NousResearch/hermes-agent/pull/108914) — leftover pass + merge `origin/main` |
| Prior Bot Screen pin (void) | `bc36ddb5f9696c25acc5d51cf29a961710e2d5a3` | 2026-09-12T21:17:55Z | Superceded |
| CU approval (merged) | `9d7860b5794453310e66eadf628d3477a956e617` | 2026-09-13T13:11:46Z | [#109649](https://github.com/NousResearch/hermes-agent/pull/109649) — now also on #108914 HEAD |

## What is *not* a new Tek CUA PR

Polled teknium1 open/merged PRs, issues, events, and title search for Bot Screen / CUA / computer_use / headed cloud / cloud session / WebVNC / DisplayTarget / display lease.

**No separate follow-on PR exists.** The live CUA/desktop product PR is still #108914. Same-day Tek CUA work that landed on `main` is #109649; `77123c0e` merged `origin/main` so the fail-closed CU gate sits next to the lease fence on Bot Screen.

Tek’s leftover commits (4000 re-attach, install `session_id`, SIGTERM→SIGKILL, `_ALLOC_LOCK` out of `/tmp`, xauth via stdin, honest `auto_start` docs) **are on this HEAD**.

## Mirror + scan (local, gitignored)

`.data/repos/hermes-agent.git` blobless mirror. Detached worktrees: `.data/worktrees/hermes-main` (`b05a47b9`), `.data/worktrees/hermes-pr108914` (`77123c0e`).

`hermes-maintainer scan --mode fast` 2026-09-13T13:28Z: 520 issues + 1000 PRs. Pin-enrich then re-GET after HEAD moved.
