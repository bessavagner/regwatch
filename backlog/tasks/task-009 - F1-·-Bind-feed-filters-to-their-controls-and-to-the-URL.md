---
id: TASK-009
title: F1 · Bind feed filters to their controls and to the URL
status: Done
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 10:52'
labels:
  - 'track:console'
  - 'size:S'
dependencies: []
documentation:
  - docs/backlog.md
priority: medium
ordinal: 9000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
initialFilters() reads client, state, section, category, date_from and date_to out of the query string and applies them, but no select or date input is bound to those values, so every control reads 'all' while a filter is silently active. Nothing writes filters back to the URL either, so a filtered view cannot be bookmarked, shared, or reached with the back button.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every control reflects the active filter on load
- [x] #2 Changing a filter updates the query string
- [x] #3 Browser back restores the previous filter set
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
web/src/lib/feedFilters.ts is the one converter between a query
string and a feed view; Feed.svelte reads and writes through it. Every select
and date input now carries a value, so a control can no longer read 'all' over
an active filter. setFilter pushes a history entry; a popstate listener
restores the whole view.

The Client select needed a second fix: Svelte matches a select's value against
the raw option expression, and the option carried a numeric id, so a client id
read out of the query string never matched and the browser left selectedIndex
at -1. The option value is now String(c.id).

Included beyond the task text, deliberately: 'ordering' (the Order select had
the identical defect and sits in the same group) and 'page' (TASK-011 landed
in the same plan, and Back restoring filters but not the page would half-honour
AC #3).
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
feedFilters.ts round-trips the whole feed view through the query string; every control carries a value and popstate restores. On main, ships in TASK-034.
<!-- SECTION:FINAL_SUMMARY:END -->
