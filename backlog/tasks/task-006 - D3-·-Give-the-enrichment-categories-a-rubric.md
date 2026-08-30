---
id: TASK-006
title: D3 · Give the enrichment categories a rubric
status: Done
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-30 13:11'
labels:
  - 'track:signal'
  - 'size:S'
milestone: m-0
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 6000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The system prompt names six categories and defines none, so the model has no criteria to be consistent against. Measured on Sertao: acts summarised 'anuiu previamente a celebracao de contrato' split 12 regulation / 5 other; 'declarou de utilidade publica' splits 10 / 2. About 29 percent of identical act types are labelled inconsistently.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Each category defined in one line with one example in the prompt
- [x] #2 The measured phrase clusters come back single-valued
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Rubric shipped in v0.21.0 (enrichment/prompt.py): six categories, each one definition line plus a worked example; the two originally measured phrase clusters are routed explicitly in the regulation line. AC#1 verified by src/enrichment/tests/test_prompt.py.

AC#2 measured 2026-08-30 on a 101-act corpus (backfill_watches over 2026-08-24 -> 08-28, then reenrich_matches --apply, exec regwatch-run-daily-wt47j; report exec regwatch-run-daily-gn22g). enrichment_report: clusters_measured 3, split_clusters [], inconsistency_rate 0.0%. Every cluster of >= 3 identical act types came back single-valued under the rubric. NOT a delta against the 29% pilot figure -- those acts were deleted with the dummy clients on 08-28, so there is no paired before/after; this is a fresh measurement. Caveat: 3 clusters is a thin base, so 0.0% is consistent with a working rubric rather than proof of one; the number gets stronger for free as matches accumulate. Detail in docs/analysis/2026-08-28-enrichment-baseline.md.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Rubric shipped v0.21.0 and measured 2026-08-30 on 101 re-enriched acts: 3 clusters of >= 3 identical act types, all single-valued, inconsistency rate 0.0%. Fresh measurement under the rubric, not a paired delta against the 29% pilot figure (that corpus was deleted).
<!-- SECTION:FINAL_SUMMARY:END -->
