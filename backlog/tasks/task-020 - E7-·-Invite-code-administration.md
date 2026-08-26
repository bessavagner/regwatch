---
id: TASK-020
title: E7 · Invite-code administration
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
labels:
  - 'track:beta'
  - 'size:S'
dependencies:
  - TASK-014
documentation:
  - docs/backlog.md
priority: medium
ordinal: 20000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Issue, list, revoke, expire. A management command is sufficient for the beta, no UI needed.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Codes can be issued, listed, revoked and expired from the CLI
- [ ] #2 A revoked or expired code cannot create an account
<!-- AC:END -->
