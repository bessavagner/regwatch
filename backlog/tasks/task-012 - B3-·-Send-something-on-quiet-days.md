---
id: TASK-012
title: B3 · Send something on quiet days
status: In Progress
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-30 15:22'
labels:
  - 'track:digest'
  - 'size:S'
milestone: m-0
dependencies:
  - TASK-003
documentation:
  - docs/backlog.md
priority: medium
ordinal: 12000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
A client with no matches gets no email, so silence means both 'nothing happened' and 'RegWatch is broken' and they cannot tell which. IFCE Crateus has had zero matches since 2026-08-19 and has therefore heard nothing for a week.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every client with an email address gets a message every publication day
- [x] #2 Quiet-day message is visibly different from a match digest
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Code complete on main, not yet deployed. build_and_send_digests now iterates clients (clients_expecting_delivery) instead of matches; a client with an active watch and an email gets digests/quiet.txt on any date with an ingested Edition. Gating recorded in decision-007: no edition => no message, so weekends and holidays stay silent.

daily.txt gained the header 'O que suas buscas encontraram hoje:' so the two message shapes are distinguishable by assertion rather than by eye.

POST /api/digests/send no longer 404s when nothing matched on a date that published - it sends the quiet digest. The 404 now means 'the DOU published no edition on this date'.

Evidence: 408 passed, 0 failed (uv run pytest src). 10 new notifier tests + 3 run_daily tests. Verified non-vacuous by stashing notifier.py and re-running: 'digests=0 digests_sent=0 status=success' without the change, digests=1/sent=1 with it. ruff on src/digests+src/pipeline: 28 findings before and after, no new ones.

AC#1 and AC#2 ticked on test evidence. Still outstanding before Done: v0.28.0 release, then a real quiet-day email received at admin@cactarus.com. Runbook section 'Tell a quiet day from a broken pipeline' added.
<!-- SECTION:NOTES:END -->
