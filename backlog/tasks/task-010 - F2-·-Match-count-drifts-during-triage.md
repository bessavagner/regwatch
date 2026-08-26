---
id: TASK-010
title: F2 · Match count drifts during triage
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:console'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: low
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
With a state filter active, applyUpdate removes the row from the list but leaves count untouched, so the header and the hero SignalDial keep reporting the old number.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Count and dial stay consistent with the visible list
<!-- AC:END -->
