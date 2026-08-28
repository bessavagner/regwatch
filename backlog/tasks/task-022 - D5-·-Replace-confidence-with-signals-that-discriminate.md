---
id: TASK-022
title: D5 · Replace confidence with signals that discriminate
status: In Progress
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-28 16:56'
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
- [ ] #1 The new signals have measurable spread across a day of matches
- [x] #2 Feed and digest can sort by them
- [ ] #3 confidence is removed from the model contract or given a real rubric
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Signals stored, ordered and rendered: Summary + Match gain names_party/has_amount/has_deadline and a derived signal_score 0-3 (migration 0004, additive, all defaults). ordering=signal on the feed, -signal_score before -rank in the digest, badges on MatchCard in pt-BR. enrichment_report now prints signal spread and per-flag rates beside confidence's. AC#1 (measured spread) needs the v0.22.0 deploy plus a few days of real matches; AC#3 is Task 4 (confidence leaves the contract).
<!-- SECTION:NOTES:END -->
