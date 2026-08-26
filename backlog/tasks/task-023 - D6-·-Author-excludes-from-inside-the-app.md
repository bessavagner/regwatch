---
id: TASK-023
title: D6 · Author excludes from inside the app
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
labels:
  - 'track:signal'
  - 'size:M'
dependencies:
  - TASK-021
documentation:
  - docs/backlog.md
priority: medium
ordinal: 23000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
watch_term_contexts already finds the noisy phrases; it surfaced 'saude e saneamento', which was nine acts of ambulances, medical supplies and funeral services and zero real sanitation works. But it is a CLI command whose output must be copied into a watch by hand, and every watch in production still had an empty exclude list on 2026-08-26. Expose the term-context report as an endpoint and render the clusters in the watch editor with a checkbox beside each.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 An exclude can be added without opening a terminal
- [ ] #2 Suggested clusters come from watch_term_contexts
- [ ] #3 Feeds the 'Nunca quando disser' input from E3
<!-- AC:END -->
