---
id: TASK-009
title: F1 · Bind feed filters to their controls and to the URL
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
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
- [ ] #1 Every control reflects the active filter on load
- [ ] #2 Changing a filter updates the query string
- [ ] #3 Browser back restores the previous filter set
<!-- AC:END -->
