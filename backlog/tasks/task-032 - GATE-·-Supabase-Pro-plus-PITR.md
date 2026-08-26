---
id: TASK-032
title: GATE · Supabase Pro plus PITR
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
labels:
  - 'track:gate'
  - 'size:S'
dependencies: []
documentation:
  - docs/backlog.md
priority: medium
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The project is on the Free plan: PITR is not enabled and there are no automated daily backups. Only a logical pg_dump restore drill has been done, which proves the procedure but is not a PITR test. Upgrade, then repeat the drill via the real restore-pitr path. See deploy/RUNBOOK.md Gate 3 evidence. Also note storage sat at 285 MB against the 500 MB free tier before the 08-26 prune took it to 152 MB.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Project on Pro with the PITR add-on
- [ ] #2 Restore drill repeated through the real PITR endpoint
<!-- AC:END -->
