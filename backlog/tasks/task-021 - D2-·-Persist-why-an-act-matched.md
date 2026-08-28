---
id: TASK-021
title: D2 · Persist why an act matched
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-28 10:52'
labels:
  - 'track:signal'
  - 'size:M'
milestone: m-0
dependencies:
  - TASK-008
documentation:
  - docs/backlog.md
priority: high
ordinal: 21000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The matched terms are already handed to the LLM at enrichment time (enrich_match calls term_texts on the watch groups) and then thrown away. Add matched_terms to Match, populate it in the matcher, render it in the card and the digest as 'matched saneamento'. This is the difference between a feed the client trusts and one they suspect, and it is the raw material for D6 and for a client saying 'never this word again'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Every new match records which term fired
- [ ] #2 The matched term is shown in the app and in the digest
<!-- AC:END -->
