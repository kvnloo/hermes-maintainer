# Data schemas and contracts

## Node IDs

Stable local IDs use prefixes:

- `issue:109495`
- `pr:109500`
- `commit:<sha>`
- `campaign:<digest>`
- `atom:<pr>:<scope>`

## Evidence receipt

Target schema for agent and verifier output:

```json
{
  "subject_id": "pr:109500",
  "acceptance_id": "gateway-yolo-admin-boundary",
  "level": "reproduced",
  "status": "pass",
  "source_sha": "...",
  "environment": {
    "os": "linux",
    "python": "3.11"
  },
  "command": "scripts/run_tests.sh ...",
  "artifacts": [],
  "notes": "fails on base, passes on candidate"
}
```

A receipt should be immutable once recorded. A newer run creates another receipt.

## Work packet

```json
{
  "campaign_id": "campaign:...",
  "task_type": "windows_reproduction",
  "problem": "...",
  "pinned_base_sha": "...",
  "candidate_refs": ["pr:..."],
  "acceptance": ["..."],
  "must_not": ["open another competing full implementation"],
  "deliverables": ["receipt.json", "notes.md"],
  "budget": {"minutes": 45, "max_changed_files": 0}
}
```

## Relationship proposal

```json
{
  "src_id": "pr:109503",
  "dst_id": "pr:109500",
  "relation_type": "complements",
  "confidence": 0.91,
  "evidence_level": "source_confirmed",
  "evidence": [
    "both target #109495",
    "one contains the broader multi-principal guard",
    "the other adds a full dispatch-path regression"
  ]
}
```

No automated closure should be derived directly from a `possible_duplicate` proposal.
