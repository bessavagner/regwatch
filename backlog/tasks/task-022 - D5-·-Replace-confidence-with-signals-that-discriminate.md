---
id: TASK-022
title: D5 · Replace confidence with signals that discriminate
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-28 10:52'
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
- [ ] #2 Feed and digest can sort by them
- [ ] #3 confidence is removed from the model contract or given a real rubric
<!-- AC:END -->
