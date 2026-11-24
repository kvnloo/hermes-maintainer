# Source, freshness, and privacy contract

This public repository should be legible without anybody else's private memory.

## Authority order

1. Current [NousResearch/hermes-agent](https://github.com/NousResearch/hermes-agent) source, security rules, area AGENTS and contributing guide **at a stated SHA**.
2. Current upstream maintainer discussions, PR reviews, CI and issue repros.
3. Public, dated case histories and changelogs.
4. This repository's graph, seed audits and contributor-derived playbooks (helpful inference, not canonical authority).
5. Agent summaries and recollections: prompts for verification, never source-of-truth.

Every work packet should say when it was checked. Distinguish **official rule**, **verified observation**, **community heuristic**, **open proposal**, and **speculation**. A closed roadmap issue is not necessarily shipped behavior; an open issue is not necessarily unfixed code.

## Public content rules

Never copy private project trackers, internal queues, credentials, unshared chats, contact details, private roadmap claims or internal message text here. Preserve a *generalizable rule* with only public evidence. No private security reports in a public PR. Never call unverified inference a team goal.

Use source links rather than screenshots or a frozen copy of upstream docs. Source and PR history change; the knowledge base should explain why to read them and what you should test.

## Agent response contract

When helping a contributor, state:

- Checked upstream main SHA and current date.
- Exact public source(s), or explicitly say “not verified.”
- Which source is authoritative and which is a heuristic.
- All-state competing issue/PR scan and intended-user-behavior check.
- Next safest action and the proof that would change the disposition.
- No write to NousResearch/hermes-agent without explicit authorization; no merge.

The graph stores relationships and evidence, not truth-by-similarity. Contributors should be able to dispute a link with a primary-source counterexample.
