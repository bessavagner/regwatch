---
id: TASK-008
title: D1 · Centre the snippet on the matched term
status: Done
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 13:32'
labels:
  - 'track:signal'
  - 'size:S'
milestone: m-0
dependencies:
  - TASK-021
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
- [x] #1 Snippet shows the matched term with surrounding context
- [x] #2 Fallback display in the app is useful when enrichment failed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
matching/snippet.py cuts a 280-char window centred on the first term that literally occurs, snapped to word boundaries, with the old head-of-act behaviour as the fallback for stemmed-only concept matches. Length-preserving per-character fold keeps offsets valid into the original text. The app marks the term inside the fallback snippet via a parts array, never {@html} (XSS regression test included). Verified: pytest 324 passed, vitest 96 passed; mark computed style checked in a real browser -- bg accent-bg, color ink, Geist at body size, no serif/size drift.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Snippets show the matched term in context instead of the DOU header, and the app marks it.
<!-- SECTION:FINAL_SUMMARY:END -->
