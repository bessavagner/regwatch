---
id: TASK-011
title: F3 · Pagination has no total and does not advance
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:console'
  - 'size:S'
dependencies: []
documentation:
  - docs/backlog.md
priority: low
ordinal: 11000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Page 1 with Prev/Next and no count. At 25 per page, Meridiano's 429 matches are 18 pages of blind clicking. Triaging a page also empties it without advancing, leaving an empty list and a Next button.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Shows Page N of M
- [ ] #2 Next page loads automatically when triage empties the current one
<!-- AC:END -->
