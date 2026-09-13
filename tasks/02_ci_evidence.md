# Task 02: CI evidence engine

## Goal

Record exact-head verification separately from PR prose.

## Deliverables

- schema additions for check/workflow receipts;
- GitHub client support for check runs/workflow runs by head SHA;
- distinguish success, failure, cancelled, skipped, missing, action_required, and unknown;
- record disabled or not-executed acceptance lanes as unknown/not-run, never success;
- expose per-PR evidence summary in the API;
- tests with fixture payloads;
- no GitHub writes.
