---
id: TASK-004
title: B2 · Order digest items by rank
status: Done
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 10:52'
labels:
  - 'track:digest'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 4000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
build_and_send_digests has no order_by, so items arrive in whatever order Postgres returns. On 2026-08-26 Sertao's tariff revision, the single act an energy consultancy most wants, landed third between two routine generator clearances. Note rank is a weak signal until D4 and D5 land; this is the cheap improvement, not the durable one.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Digest orders by -rank then section
- [x] #2 Highest-ranked match is the first item in the email
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
build_and_send_digests now orders by -rank, then act__edition__section, then id.

Added id as a final tiebreak beyond what the AC asked for: rank and section alone leave equal-ranked same-section matches in whatever order Postgres returns, which can differ between two runs of the same date. The digest body is stored on the row, so an unstable order would show up as a spurious body change on re-send.

rank is a FloatField(default=0.0), not nullable, so there is no NULLS FIRST surprise in the DESC sort.

Ordering only; rank stays the weak signal the description calls out until D4 (TASK-007) and D5 (TASK-022) land.

Two tests: highest rank leads the mail, and equal ranks fall back to section. Full suite 279 passed.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Digest orders by -rank, then section, then id. On main, ships in TASK-034. rank stays a weak signal until TASK-007 and TASK-022.
<!-- SECTION:FINAL_SUMMARY:END -->
