---
id: TASK-040
title: 'D10 · Dismissing archives, and the archive can be emptied'
status: In Progress
assignee: []
created_date: '2026-08-30 20:43'
updated_date: '2026-08-30 20:43'
labels:
  - 'track:signal'
  - 'size:M'
dependencies: []
priority: medium
ordinal: 40000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Dismissing already hid a match rather than deleting it, but nothing said so: the button read 'descartar' and the only route back to a hidden row was knowing the state filter reached it. A reversible action that looks irreversible makes the operator hesitate over a feed they are meant to clear fast.

Rename the verb to 'arquivar', add an /arquivo screen listing archived matches, and give it the two actions an archive needs: put a row back, or delete it for good. Deletion is the only operation in the app that actually loses data, so it must reach archived rows only and take an explicit id list.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Dismissing is presented as archiving, not discarding
- [x] #2 Archived matches are listed on their own screen and can be restored
- [x] #3 Permanent delete reaches only archived rows, by explicit id, behind a confirmation
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Code complete on main, not yet deployed.

Backend: Match.state values are unchanged (decision-002) - 'dismissed' is still the
stored value, only the label moved to 'arquivada'. Two new endpoints:
  POST /api/matches/<id>/reopen        -> state='new'
  POST /api/matches/bulk_delete {ids}  -> hard delete, archived rows only

Both look their rows up through WorkspaceScopedQuerysetMixin.workspace_queryset()
rather than the viewset's get_queryset(), which hides dismissed rows when no state
filter is given and would therefore 404 on everything the archive exists to act on.
That scoping is now a named method on the mixin instead of an implicit side effect
of get_queryset(); every existing caller is unaffected.

Delete is fenced twice, because it is the only operation in the app that loses
data: it reaches only rows already in state='dismissed', so there is always one
deliberate step between reading a feed and losing a row; and it takes an explicit
id list, never a filter and never 'everything', so the blast radius is whatever the
operator could see and tick. Mixed lists are all-or-nothing (404), so a request
containing one un-archived or out-of-workspace id changes nothing.

Frontend: 'descartar' -> 'arquivar' across TriageActions, the Feed bulk bar, the
command palette shortcut and the state label. New /arquivo route with restore and
permanent delete, the delete armed behind a confirmation that names the count and
says it cannot be undone.

Evidence: uv run pytest src -> 426 passed (9 new: 6 bulk_delete, 3 reopen).
pnpm test -> 20 files / 120 tests passed (6 new Archive tests). pnpm lint exit 0.
pnpm run build ok. npx tsc --noEmit: 9, unchanged baseline. pt-BR sweep over all 21
components: clean.

Glossary addition for future copy: dismiss -> arquivar, dismissed -> arquivada,
archive -> arquivo, restore -> restaurar, permanent delete -> excluir
definitivamente. This supersedes 'descartar' in the TASK-013 glossary.

Outstanding before Done: deploy, and the Playwright run.
<!-- SECTION:NOTES:END -->
