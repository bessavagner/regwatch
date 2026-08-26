---
id: TASK-002
title: B1 · Put links in the digest
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:digest'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The digest template renders category, summary, title and agency and no href anywhere. Act.source_url and Act.source_anchor already exist on the model and are exposed through the API. Highest value-per-line change available in the product: a client who reads a summary today has no way to reach the act.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every digest item links to its act in the DOU
- [ ] #2 Link uses source_anchor where available
<!-- AC:END -->
