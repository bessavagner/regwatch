---
id: TASK-014
title: E1 · Signup with an invite code
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:beta'
  - 'size:M'
dependencies:
  - TASK-013
documentation:
  - docs/backlog.md
priority: high
ordinal: 14000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Redeeming a code creates in one transaction a User, a Workspace, and exactly one Client carrying the signup email as its digest recipient. None of those three words appears in the UI. The Client table is NOT dropped: the flat account model is a UI and onboarding contract, not a schema change, so the five pilot clients keep working and the agency case stays recoverable. Reuse the invite_user command's logic rather than adding a second path to account creation.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 A code holder reaches a working empty account with no manual DB work
- [ ] #2 Signup provisions Workspace plus exactly one Client atomically
- [ ] #3 No occurrence of the words workspace or client in the beta UI
- [ ] #4 Existing pilot clients are unaffected
<!-- AC:END -->
