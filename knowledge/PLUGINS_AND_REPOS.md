# The plugin catalog and the sibling repos

*Checked 2026-11-24 against `NousResearch/hermes-agent` main [`8545fee`](https://github.com/NousResearch/hermes-agent/tree/8545feeb1a53fc73375dfa98cf65cafadba66bf0). Upstream wins if this page disagrees with it.*

## The catalog is a list of SHA pins

`plugin-catalog/*.yaml` in hermes-agent holds one file per community plugin (2,633 entries at `8545fee`). Each entry pins a full 40-character commit SHA. Branches, tags and short SHAs are rejected, and installs check out exactly that commit. ([plugin-catalog/README.md L17-L19](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/plugin-catalog/README.md#L17-L19), example: [0bull.yaml](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/plugin-catalog/0bull.yaml#L3))

Consequences ([L20-L32](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/plugin-catalog/README.md#L20-L32)):

- **The pin is the trust model.** A listed plugin must not update itself. Users get updates only through a SHA-bump PR plus `hermes plugins update <name>`.
- **A SHA bump is a new PR**, and reviewers read the upstream commit range being adopted.
- Only the plugin's owner or a major contributor may submit it. Drive-by listings of other people's repos are declined.

This is why "plugin-catalog" dominates merge counts. 2,598 of the 3,390 PRs teknium1 merged in the last 30 days touched it (see [WHO_MAINTAINS_WHAT.md](./WHO_MAINTAINS_WHAT.md)).

## Sibling repos under NousResearch

Third-party products don't belong in the core tree ([AGENTS.md L47-L48](https://github.com/NousResearch/hermes-agent/blob/8545feeb1a53fc73375dfa98cf65cafadba66bf0/AGENTS.md#L47-L48)), so plugins live in separate repos. Activity window: PRs merged 2026-10-25..11-24, read with `gh` on 2026-11-24.

| Repo | What it is | Merged PRs (30d) | Who merged | Open PRs / issues |
|---|---|---:|---|---|
| [hermes-official-plugins](https://github.com/NousResearch/hermes-official-plugins) | Supported Nous plugins (Home Assistant, Spotify, …) | 75 | teknium1 47, unsupportedpastels 25, alt-glitch 3 | 59 / 33 |
| [hermes-labs-plugins](https://github.com/NousResearch/hermes-labs-plugins) | Experimental, unsupported; community tier, "up for adoption" | 19 | teknium1 19 | 11 / 8 |
| [hermes-collective-wisdom](https://github.com/NousResearch/hermes-collective-wisdom) | Collective wisdom plugin | 7 | victor-kyriazakos 7 | 3 / 9 |
| [hermes-plugin-sprites](https://github.com/NousResearch/hermes-plugin-sprites) | Sprites (Fly.io) terminal backend | 9 | benbarclay 9 | 1 / 0 |
| [hermes-plugin-solstice](https://github.com/NousResearch/hermes-plugin-solstice) | Solstice (Gemini OAuth) provider | 1 | benbarclay 1 | 0 / 3 |
| [hermes-nvidia](https://github.com/NousResearch/hermes-nvidia) | NVIDIA App/Broadcast MCP + skills (Windows) | 1 | alt-glitch 1 | 3 / 1 |
| [hermes-foundry](https://github.com/NousResearch/hermes-foundry) | Hermes on Microsoft Foundry | 0 (7 direct commits) | — | 0 / 0 |
| [hermes-example-plugins](https://github.com/NousResearch/hermes-example-plugins) | Reference plugins for the docs | 0; last commit 2026-10-05 | — | 2 / 1 |
| [hermes-agent-self-evolution](https://github.com/NousResearch/hermes-agent-self-evolution) | DSPy + GEPA self-improvement | 0; last commit 2026-06-17 | — | 106 / 30 |

How to read it: a repo with a single merger is effectively owned by that person, so ask them. A large open-PR count with no recent merges (self-evolution) means a new PR there is unlikely to be reviewed soon. Several older `hermes-plugin-*` repos are archived; check `isArchived` before you contribute.

Reproduce:

```bash
gh api graphql -f query='query($q:String!){search(query:$q,type:ISSUE,first:100){issueCount nodes{... on PullRequest{mergedBy{login}}}}}' \
  -f q='repo:NousResearch/hermes-official-plugins is:pr is:merged merged:>=2026-10-25'
gh repo list NousResearch --limit 200 --json name,pushedAt,isArchived
```

Next: [WHO_MAINTAINS_WHAT.md](./WHO_MAINTAINS_WHAT.md).
