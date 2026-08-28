---
id: TASK-013
title: C3 · Translate the SPA to pt-BR
status: To Do
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 10:52'
labels:
  - 'track:ptbr'
  - 'size:M'
milestone: m-0
dependencies:
  - TASK-005
documentation:
  - docs/backlog.md
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Client, State, Section, Order, Relevant, Dismiss, Page: the console is in English with Portuguese leaking through in places such as 'resumo indisponivel - mostrando o texto do ato'. Includes the login screen, which is the first thing a beta user sees. Hard switch, no gettext, no locale switcher, English dropped.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 No English remains in any user-visible SPA string
- [ ] #2 Login and error states covered
<!-- AC:END -->
