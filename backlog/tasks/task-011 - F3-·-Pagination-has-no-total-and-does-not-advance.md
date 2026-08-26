---
id: TASK-011
title: F3 · Pagination has no total and does not advance
status: In Progress
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-26 23:33'
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
- [x] #1 Shows Page N of M
- [x] #2 Next page loads automatically when triage empties the current one
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
config.pagination.CountedPageNumberPagination adds page,
total_pages and page_size to every paginated payload; the SPA renders
'Page N of M' from them and never learns PAGE_SIZE. See decision-005.

AC #2: pagination is server-side over a set that shrinks during triage, so
emptying a page reloads the current page number -- the rows behind it have
shifted down into it, and page + 1 would skip a whole page. Only a page that no
longer exists steps back.
<!-- SECTION:NOTES:END -->
