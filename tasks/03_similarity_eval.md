# Task 03: similarity evaluation

## Goal

Turn duplicate retrieval into a measurable system instead of a model-confidence heuristic.

## Deliverables

- fixture format for labeled same-defect / related / unrelated pairs;
- evaluator for precision@k, recall@k, and false-link rate;
- time-split evaluation support;
- hard-negative sampling from same component/labels;
- optional embedding reranker interface, but lexical retrieval remains available;
- seed evaluator with examples from `seed/audit/campaign_seeds.json` where appropriate.
