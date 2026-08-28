---
id: TASK-007
title: 'D4 · Rank from the stored tsvector, not a rebuilt one'
status: Done
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 13:21'
labels:
  - 'track:signal'
  - 'size:S'
milestone: m-0
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 7000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
match_edition computes rank as SearchRank(SearchVector(title, raw_text, config=portuguese)) which rebuilds the tsvector from scratch for every act on every watch instead of reading the stored search_vector_pt column. At six watches over ~3,400 acts that is ~20,000 full-body tsvector computations per run. Worse than perf: the rebuild omits the NormalizeNFC wrapper that ingest_edition applies, so NFD-decomposed text ranks differently from how it matches. Upgrades the stale 'performance at scale' item in docs/sprints/backlog.md.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Ranking reads search_vector_pt
- [x] #2 Rank is stable for NFD-decomposed input
- [x] #3 Run time measured before and after
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
SearchRank now reads F('search_vector_pt'). NFD-decomposed and agency-only matches both rank > 0 (both scored exactly 0.0 before). Measured over 3400 acts x 6 watches, same acts/watches/rank query, queryset evaluation only: BEFORE (rebuilt vector) 9.01s, AFTER (stored column) 0.49s -- 18.2x.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Ranking reads the stored Portuguese vector, so it agrees with the predicate that produced the match (NFC-normalised, agency included) and stops recomputing ~20k tsvectors per run.
<!-- SECTION:FINAL_SUMMARY:END -->
