---
id: TASK-022
title: D5 · Replace confidence with signals that discriminate
status: Done
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-30 13:12'
labels:
  - 'track:signal'
  - 'size:M'
milestone: m-0
dependencies:
  - TASK-006
documentation:
  - docs/backlog.md
priority: high
ordinal: 22000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The prompt asks for 'um numero entre 0 e 1' with no rubric and gets 0.98 to 0.99 for everything including the other bucket. Hiding it from the UI was right; it left the feed with no ordering at all. Ask instead for things the model can check: does this act name a specific company, a monetary value, a deadline. Those are verifiable and they rank.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The new signals have measurable spread across a day of matches
- [x] #2 Feed and digest can sort by them
- [x] #3 confidence is removed from the model contract or given a real rubric
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
confidence removed from Summary, from both provider request bodies (including OpenAI's strict json_schema), from the enricher, the serializer, the report command and the TS type. Column dropped in migration 0005_remove_match_confidence -- verified forward and reverse against Postgres; note the reverse restores the column but not the values.

AC#1 measured 2026-08-30 on the same 101-act corpus as TASK-006 (report exec regwatch-run-daily-gn22g). signal_histogram {1: 31, 2: 57, 3: 13} -- three populated buckets, modal share 56.4%, against confidence's 82.6% over three values that ordered nothing. flag_rates: names_party 78.2%, has_amount 19.8%, has_deadline 84.2%. The spread is real, but most of the ordering comes from has_amount; has_deadline and names_party are near-ubiquitous in DOU acts. Weighting has_amount is the first thing to try if ranking needs sharpening. Detail in docs/analysis/2026-08-28-enrichment-baseline.md.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
confidence dropped from the contract and the column (v0.23.0); signal_score measured 2026-08-30 across 101 acts spreads over three buckets (31/57/13) at 56.4% modal share, versus confidence's 82.6% that ordered nothing. has_amount (19.8%) carries most of the discrimination.
<!-- SECTION:FINAL_SUMMARY:END -->
