---
id: TASK-008
title: D1 · Centre the snippet on the matched term
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:signal'
  - 'size:S'
dependencies: []
documentation:
  - docs/backlog.md
priority: medium
ordinal: 8000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
snippet is act.raw_text[:280], the first 280 characters, which for a DOU act is the header. Every snippet restates the title and shows nothing about why the act matched. Four consecutive Sertao snippets all begin 'DESPACHO No ..., DE ... DE AGOSTO DE 2026 A SUPERINTENDENTE'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Snippet shows the matched term with surrounding context
- [ ] #2 Fallback display in the app is useful when enrichment failed
<!-- AC:END -->
