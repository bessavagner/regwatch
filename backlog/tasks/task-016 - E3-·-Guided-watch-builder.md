---
id: TASK-016
title: E3 · Guided watch builder
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:beta'
  - 'size:L'
dependencies:
  - TASK-014
  - TASK-013
documentation:
  - docs/backlog.md
priority: high
ordinal: 16000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Three plain-language inputs compiled to the existing groups and exclude JSON: 'Avise-me sobre estas palavras' becomes one OR group; 'Somente quando tambem mencionar' becomes a second ANDed group; 'Nunca quando disser' becomes exclude. The third input is what finally makes excludes reachable by the person who knows which phrases are noise. Term kind (entity vs concept) is inferred, not asked. The matcher does not change.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Someone who has never seen the schema can build a watch that matches what they meant
- [ ] #2 Builder output round-trips through the existing matcher unchanged
- [ ] #3 Exclude input is present and explained
<!-- AC:END -->
