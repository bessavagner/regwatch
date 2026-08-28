---
id: TASK-010
title: F2 · Match count drifts during triage
status: Done
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 10:52'
labels:
  - 'track:console'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: low
ordinal: 10000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
With a state filter active, applyUpdate removes the row from the list but leaves count untouched, so the header and the hero SignalDial keep reporting the old number.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Count and dial stay consistent with the visible list
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
applyUpdate decrements count when a triaged match leaves the active
filter. The header and the SignalDial both read count, so one decrement fixes
both. count is the size of the filtered set, not of the page, so the decrement
matches what a refetch would return.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
applyUpdate decrements count when a triaged match leaves the active filter; header and SignalDial agree with the list. On main, ships in TASK-034.
<!-- SECTION:FINAL_SUMMARY:END -->
