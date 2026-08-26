---
id: TASK-012
title: B3 · Send something on quiet days
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:digest'
  - 'size:S'
dependencies:
  - TASK-003
documentation:
  - docs/backlog.md
priority: medium
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A client with no matches gets no email, so silence means both 'nothing happened' and 'RegWatch is broken' and they cannot tell which. IFCE Crateus has had zero matches since 2026-08-19 and has therefore heard nothing for a week.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every client with an email address gets a message every publication day
- [ ] #2 Quiet-day message is visibly different from a match digest
<!-- AC:END -->
