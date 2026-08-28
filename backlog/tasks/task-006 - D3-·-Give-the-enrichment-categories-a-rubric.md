---
id: TASK-006
title: D3 · Give the enrichment categories a rubric
status: In Progress
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 16:50'
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
- [ ] #2 The measured phrase clusters come back single-valued
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Rubric shipped in v0.21.0 (enrichment/prompt.py): six categories, each one definition line plus a worked example; the two measured phrase clusters are routed explicitly in the regulation line. AC#1 verified by src/enrichment/tests/test_prompt.py. AC#2 NOT yet measurable: the pilot corpus was deliberately removed with the dummy clients, so enrichment_report returns 23 matches / 1 cluster / 0.0% inconsistency at every window -- the before-number has no room to improve. Re-measure ~2026-09-04 once a week of real matches has accumulated (~100-160 acts). Detail in docs/analysis/2026-08-28-enrichment-baseline.md.
<!-- SECTION:NOTES:END -->
