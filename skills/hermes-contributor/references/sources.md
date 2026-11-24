# Sources and authority order

1. Current [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent)
   source, `AGENTS.md` (root and area), `CONTRIBUTING.md`, `SECURITY.md`, at a
   stated SHA.
2. Current upstream maintainer discussion: PR reviews, CI, issue repros.
3. Public, dated case histories and changelogs.
4. The [hermes-maintainer](https://github.com/kvnloo/hermes-maintainer)
   knowledge base (`knowledge/`): community inference, not authority.
5. Agent summaries and recollections: prompts for verification only.

When answering a contributor, state: upstream SHA and date checked; exact public
sources or "not verified"; which source is authoritative and which is a
heuristic; the all-state competing PR/issue scan; the next safest action and the
proof that would change it. Distinguish OBSERVED, INFERRED and PROPOSED.

## Upstream entry points

- [AGENTS.md](https://github.com/NousResearch/hermes-agent/blob/main/AGENTS.md)
- [CONTRIBUTING.md](https://github.com/NousResearch/hermes-agent/blob/main/CONTRIBUTING.md)
- [SECURITY.md](https://github.com/NousResearch/hermes-agent/blob/main/SECURITY.md)
- [Developer guide](https://github.com/NousResearch/hermes-agent/tree/main/website/docs/developer-guide)
- [All PRs](https://github.com/NousResearch/hermes-agent/pulls?q=is%3Apr)

## Public-content rules

Keep private trackers, credentials, unshared chats, contact details and private
security reports out of public issues, PRs and comments. Generalize the lesson;
cite only public primary sources. No write to NousResearch/hermes-agent without
explicit authorization, and never merge.
