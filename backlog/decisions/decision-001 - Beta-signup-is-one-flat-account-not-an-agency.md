---
id: decision-001
title: 'Beta signup is one flat account, not an agency'
date: '2026-08-26 17:30'
status: accepted
---
## Context

The data model is `Workspace` (the firm) → `Client` (who they monitor for) →
`Watch`, and users join a Workspace by invite only. It was built for the agency
case, which is what the pilot actually is: Aurora Compliance and Meridiano
Infraestrutura are firms that monitor the DOU on behalf of their own clients.

For a self-serve beta that model asks a new user to understand two layers of
nesting before they can create a single watch.

## Decision

A beta signup produces one flat account. No Client-picker, no Client layer, no
mention of "workspace" or "client" anywhere in the beta UI. You sign up, you get
watches and a feed.

**The `Client` table is not dropped.** Signup provisions a `Workspace` plus
exactly one `Client` behind the scenes, in one transaction, with the signup email
as the digest recipient. The flat model is an onboarding and UI contract, not a
schema change.

## Consequences

- The five pilot clients keep working untouched, and the operator console keeps
  its `/clients` screen.
- No destructive migration runs against live production data.
- The agency case stays recoverable by revealing a screen rather than restoring
  a table — which matters, because it is the case two of the five pilots
  actually represent.
- Cost: two representations of the same thing coexist (flat for beta users,
  nested for the operator), so any new client-scoped feature has to be checked
  against both.
- "Multiple production workspaces" moves out of the v1 non-goals list in
  `docs/sprints/backlog.md` — the model supported it all along, the beta now
  relies on it.

Implemented by TASK-014.
