---
id: TASK-028
title: G1 · Extend alerting to delivery
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
labels:
  - 'track:ops'
  - 'size:S'
dependencies: []
documentation:
  - docs/backlog.md
priority: medium
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
2026-08-26 showed the alert policies only catch jobs that ran and failed: a scheduler trigger that never launched was invisible for six days. That hole is now covered by policy-scheduler-trigger-denied.json. The remaining one is silent partial delivery, where a digest fails for one client while the run still exits 0.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A digest that fails for one client raises an alert
- [ ] #2 Alert fires without failing the whole run
<!-- AC:END -->
