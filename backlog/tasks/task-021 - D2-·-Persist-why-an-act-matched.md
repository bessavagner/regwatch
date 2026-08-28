---
id: TASK-021
title: D2 · Persist why an act matched
status: Done
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-28 13:26'
labels:
  - 'track:signal'
  - 'size:M'
milestone: m-0
dependencies:
  - TASK-008
documentation:
  - docs/backlog.md
priority: high
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The matched terms are already handed to the LLM at enrichment time (enrich_match calls term_texts on the watch groups) and then thrown away. Add matched_terms to Match, populate it in the matcher, render it in the card and the digest as 'matched saneamento'. This is the difference between a feed the client trusts and one they suspect, and it is the raw material for D6 and for a client saying 'never this word again'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every new match records which term fired
- [x] #2 The matched term is shown in the app and in the digest
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Match.matched_terms (JSONField, default list) populated from per-term boolean annotations built out of the same _term_q predicates that produced the match, so stemmed concept hits are recorded correctly (verified: 'licenca' concept term recorded against body text 'Licenças'). Rendered in MatchCard and in daily.txt. Not backfilled: acts past the 7-day text window cannot be re-evaluated. Verified: pytest 311 passed, vitest 88 passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Every new match records and displays which of the watch's terms fired, in the app and in the digest.
<!-- SECTION:FINAL_SUMMARY:END -->
