---
id: TASK-024
title: D7 · Triage at speed
status: In Progress
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-30 15:44'
labels:
  - 'track:signal'
  - 'size:M'
milestone: m-0
dependencies:
  - TASK-009
documentation:
  - docs/backlog.md
priority: medium
ordinal: 24000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
947 of 950 matches are untriaged and the same three have been the only triaged ones since 08-20. The mechanical reason is that triage is mouse-only, one item at a time, at 37 items per day. The command palette exists but only navigates between routes. Add J/K to move, R/D to judge, plus a select-many bar with 'dismiss all from this agency'.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 One client's day can be triaged in about two minutes
- [x] #2 Keyboard shortcuts are discoverable from the command palette
- [x] #3 Bulk dismiss by agency works from the feed
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Code complete on main, not yet deployed.

The task description quotes 947/950 untriaged; production actually holds 101 matches
(93 new, 8 dismissed). D7 is no longer digging out from under a mountain - it is
building the pump before the volume returns.

API: POST /api/matches/bulk_dismiss takes exactly one of {ids: [int]} or
{agency: str}, both narrowed by MatchViewSet.get_queryset() so filter semantics
cannot drift from the read path and a mutation cannot leave the workspace. The
feed's current query string is forwarded, so the button means the same set as the
list above it. Deliberately NO 'dismiss everything currently filtered' form.
An id list is all-or-nothing: if any id is invisible to the caller the whole
request 404s rather than silently applying to the visible subset, which would
report a number the caller cannot act on and would answer 'does this id exist
elsewhere' for another workspace's rows.

UI: J/K move, R/D judge, X selects. Shortcuts are suppressed inside inputs,
textareas and selects (but NOT checkboxes - blocking there would strand the hands
between mouse and keyboard), while any dialog[open] is up, and under any modifier.
Every single mutation routes through the existing applyUpdate; bulk removal goes
through applyBulkRemoval, its twin, which moves the visible rows and the count by
different numbers because the server may dismiss rows that are not on this page.
Two-step confirm before any bulk dispatch.

CommandPalette went from routes to a Command discriminated union (lib/commands.ts).
Only routes take the roving selection - Enter never lands on a shortcut.

Layout fix caught before commit: the row checkbox was floated, but MatchCard's root
is a flex container and floats do not displace flex boxes, so it would have sat on
top of the card. Feed rows are now .row--triage, a two-column flex row; the other
lists keep the plain block .row.

Test-environment change: jsdom ships <dialog> without showModal()/close(), so the
palette threw under test while working in every real browser. Polyfilled in
vitest-setup.ts, keeping the open attribute honest so a closed dialog stays hidden
from the queries.

Evidence: uv run pytest src -> 417 passed (9 new bulk_dismiss API tests, scoping
tested before ergonomics). pnpm test -> 19 files / 114 tests passed (11 new Feed
keyboard/bulk tests + 5 new CommandPalette tests). pnpm lint exit 0. pnpm run build
'built in 637ms'. npx tsc --noEmit: 9, unchanged. ruff on src/matching: 21 before and
after (one I added was fixed).

AC#2 and AC#3 ticked on that evidence.

AC#1 ('one client's day in about two minutes') is NOT ticked and was NOT measured.
It cannot be: it needs a human judging real acts, which is step 3.11 of the plan and
the operator's to do. The mechanical floor is now two keystrokes per item (j then r
or d), so ~20 matches costs ~40 keystrokes and no pointer trips; the remaining cost
is reading time, which is the part worth measuring. Triage a real day, wall-clock it,
and tick or reopen AC#1 on the number.

Outstanding before Done: v0.30.0 release, the Playwright run, and the AC#1
measurement.
<!-- SECTION:NOTES:END -->
