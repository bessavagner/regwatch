---
id: TASK-004
title: B2 · Order digest items by rank
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
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
- [ ] #1 Digest orders by -rank then section
- [ ] #2 Highest-ranked match is the first item in the email
<!-- AC:END -->
