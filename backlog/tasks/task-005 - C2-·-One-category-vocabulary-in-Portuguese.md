---
id: TASK-005
title: 'C2 · One category vocabulary, in Portuguese'
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:ptbr'
  - 'size:S'
dependencies:
  - TASK-003
documentation:
  - docs/backlog.md
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The email prints raw enum values (other, regulation, grant) while the web app already translates the same values to outro, norma, fomento in web/src/lib/constants.ts. Two vocabularies for one field. Make the Portuguese labels a single source of truth served from the API so email and SPA cannot drift again.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 No English category string reaches a user
- [ ] #2 Email and SPA read the same label source
<!-- AC:END -->
