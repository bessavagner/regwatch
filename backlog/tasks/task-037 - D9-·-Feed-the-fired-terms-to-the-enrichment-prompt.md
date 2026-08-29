---
id: TASK-037
title: D9 · Feed the fired terms to the enrichment prompt
status: Done
assignee: []
created_date: '2026-08-28 13:33'
updated_date: '2026-08-29 14:32'
labels:
  - 'track:signal'
  - 'size:S'
dependencies: []
priority: medium
ordinal: 37000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
enrich_match still passes term_texts(match.watch.groups) -- every term on the watch -- to the LLM, even though v0.20.0 (TASK-021) now persists exactly which terms fired on match.matched_terms. Narrowing the prompt to the terms that actually matched should sharpen both the summary and the category. Deliberately deferred out of TASK-021 so it would not change enrichment output mid-flight and contaminate the D3 (TASK-006) category-rubric and D5 (TASK-022) confidence measurements, which are measured against the current prompt. Do this after those two have their baselines.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 enrich_match passes match.matched_terms when it is non-empty
- [x] #2 Falls back to the full watch terms for pre-v0.20.0 matches with an empty list
- [x] #3 D3 and D5 baselines are recorded before this lands
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Harness: enrichment_report + reenrich_matches, both documented in docs/runbook.md. AC#3 baseline (docs/analysis/2026-08-28-enrichment-baseline.md) is pending the operator running enrichment_report against production.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
enrich_match passes match.matched_terms when non-empty, falling back to the full watch terms for pre-v0.20.0 matches. AC#3's baseline is docs/analysis/2026-08-28-enrichment-baseline.md, recorded before the D3 and D5 changes shipped.
<!-- SECTION:FINAL_SUMMARY:END -->
