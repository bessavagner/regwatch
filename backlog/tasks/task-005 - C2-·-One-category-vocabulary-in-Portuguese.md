---
id: TASK-005
title: 'C2 · One category vocabulary, in Portuguese'
status: In Progress
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-26 22:01'
labels:
  - 'track:ptbr'
  - 'size:S'
dependencies:
  - TASK-003
documentation:
  - docs/backlog.md
priority: high
ordinal: 5000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The email prints raw enum values (other, regulation, grant) while the web app already translates the same values to outro, norma, fomento in web/src/lib/constants.ts. Two vocabularies for one field. Make the Portuguese labels a single source of truth served from the API so email and SPA cannot drift again.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 No English category string reaches a user
- [x] #2 Email and SPA read the same label source
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Single source of truth: src/enrichment/categories.py::CATEGORY_LABELS.

Three readers: the digest via a category_label template filter, the match API
via a serialized category_label field, and the SPA filter dropdown via
GET /api/vocabulary. web/src/lib/constants.ts::CATEGORIES deleted.

Serialized the label onto each match rather than looking it up client-side, so
a badge can never show the enum while a fetch is in flight or after one fails.

Also fixed a misplaced string: the digest printed 'resumo indisponível' -- a
summary message -- in the category slot for unenriched matches. Now
'sem categoria'. test_unenriched_match_says_the_summary_is_missing had locked
that bug in; rewritten as test_unenriched_match_falls_back_to_the_act_text.

Stored values stay English per decision-002.

Python 294 passed; SPA 65 passed, lint and vite build clean, svelte-check at
its pre-existing baseline of 9 errors (all in e2e/config files, none in src).
<!-- SECTION:NOTES:END -->
