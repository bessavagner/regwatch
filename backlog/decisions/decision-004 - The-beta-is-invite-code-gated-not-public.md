---
id: decision-004
title: 'The beta is invite-code gated, not public'
date: '2026-08-26 17:30'
status: accepted
---
## Context

`docs/sprints/backlog.md` carries two explicit pre-conditions that a public
launch trips:

1. **DOU reuse licence.** The CC BY-ND versus LAI/Open-Data conflict "must be
   resolved before billing or going public."
2. **Supabase Pro + PITR.** The project is on the Free plan with no automated
   backups and no point-in-time recovery. Only a logical `pg_dump` restore drill
   has been run — it proves the procedure, not PITR. Flagged as needed "before
   real client data lands."

A third item, the LGPD controller-versus-operator question, is open pending legal
review in `docs/compliance/lgpd-posture.md`.

"Self-serve signup" is also listed as a v1 non-goal in that same file.

## Decision

The beta is gated behind invite codes issued by the operator. Real sign-in, real
self-serve watch creation, no open registration.

Both launch gates stay **deferred and tracked**, not resolved, and not treated as
blockers on beta work.

## Consequences

- A closed beta is not "going public", so the licence question does not block it.
- Invite gating bounds how much real client data exists, so the Free plan's
  backup posture stays an accepted risk rather than a negligent one — but this
  is the reason GATE tasks exist rather than being dropped.
- The beta cannot be advertised, linked publicly, or charged for until the two
  gates close.
- Self-serve signup moves from "v1 non-goal" to "beta scope, gated" — the
  sign-up *flow* is built now, the *openness* is a config change later.

Gates tracked as TASK-031 (licence), TASK-032 (PITR), TASK-033 (LGPD).
Invite administration is TASK-020.
