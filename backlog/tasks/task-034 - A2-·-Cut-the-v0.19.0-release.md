---
id: TASK-034
title: A2 · Cut the v0.19.0 release
status: To Do
assignee: []
created_date: '2026-08-28 10:51'
labels:
  - 'track:ship'
  - 'size:XS'
milestone: The signal loop
dependencies: []
priority: high
ordinal: 34000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Nineteen commits sit on main past v0.18.2, all green: digest links (TASK-002), pt-BR locale (TASK-003), rank ordering (TASK-004), the category vocabulary (TASK-005) and the feed console (TASK-009/010/011). Production still runs v0.18.2, so the first Cactarus digest goes out without links, with English dates and English category names -- worse than what the code already does. Highest value-per-effort item on the board: no new code, only a tag push.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 main is tagged v0.19.0 and the GitHub Actions run is green on all three jobs
- [ ] #2 All five workloads report regwatch:v0.19.0
- [ ] #3 The next digest arrives with links, Brazilian dates and Portuguese category labels
<!-- AC:END -->
