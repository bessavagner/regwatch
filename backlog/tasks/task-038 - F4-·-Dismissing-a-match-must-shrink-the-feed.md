---
id: TASK-038
title: F4 · Dismissing a match must shrink the feed
status: Done
assignee: []
created_date: '2026-08-29 14:31'
updated_date: '2026-08-29 14:31'
labels:
  - 'track:feed'
  - 'size:S'
dependencies: []
priority: high
ordinal: 38000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The feed only filtered by state when a state param was present, and the SPA sent none by default, so dismissed matches stayed on screen wearing a red badge and the pile only grew. Triage had no visible payoff, which is a likelier cause of 947/950 untriaged than the mouse-only interaction TASK-024 blames. Fixed: the API excludes dismissed unless a state filter names one, the SPA drops the card on dismiss, and the state select's empty option now reads 'active' rather than 'all'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 The default feed returns only new and relevant
- [x] #2 count excludes dismissed so the number falls as you triage
- [x] #3 state=dismissed still reaches them
<!-- AC:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
API excludes dismissed unless a state filter names one; SPA drops the card on dismiss and relabels the empty state option 'active'. Verified by four API tests and one Feed test.
<!-- SECTION:FINAL_SUMMARY:END -->
