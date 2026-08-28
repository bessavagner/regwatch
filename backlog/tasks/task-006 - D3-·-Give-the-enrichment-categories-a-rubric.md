---
id: TASK-006
title: D3 · Give the enrichment categories a rubric
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 10:52'
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
- [ ] #1 Each category defined in one line with one example in the prompt
- [ ] #2 The measured phrase clusters come back single-valued
<!-- AC:END -->
