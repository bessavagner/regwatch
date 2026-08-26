---
id: TASK-003
title: C1 · Set locale and time zone to pt-BR
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
labels:
  - 'track:ptbr'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
LANGUAGE_CODE is unset so Django falls back to en-us and the digest date renders 'Aug. 26, 2026' in a Portuguese product, while the subject line uses ISO 2026-08-26. Two date formats in one message, neither Brazilian. TIME_ZONE is unset too.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 LANGUAGE_CODE = pt-br and TIME_ZONE = America/Sao_Paulo
- [ ] #2 Dates render as 26 de agosto de 2026 in email and app
<!-- AC:END -->
