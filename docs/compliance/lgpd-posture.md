# RegWatch — LGPD posture note

**Status:** Approved · 2026-07-16. **Date:** 2026-07-15.

## What RegWatch does

RegWatch monitors the Diário Oficial da União (DOU) — Brazil's federal official
gazette, a public government publication — for client-defined watch terms (names of
people, entities, or organizations a professional-services firm needs to track). When
a published act matches a term, RegWatch forwards the excerpt plus an AI-generated
one-line summary and category to that firm via a per-client email digest and a web
dashboard.

## Legal basis

Processing is grounded in **legitimate interest** (LGPD Art. 7, IX / Art. 10):
professional-services firms (law firms, accounting firms, compliance teams) have a
recognized, ordinary business interest in monitoring official government publications
for events affecting people or organizations they represent — appointments,
exonerations, sanctions, contract awards, and similar acts. The source data (the DOU)
is already public by law; RegWatch does not access, infer, or publish anything beyond
what the federal government has already published.

No special category of personal data (LGPD Art. 5, II) is targeted — watch terms are
names/entities, not health, biometric, racial, religious, political, or similar data.

## What RegWatch explicitly does NOT do

- **No persistent individual profile.** A `Match` record exists only in the context of
  one workspace's own `Watch` and is scoped to that workspace — RegWatch does not
  build a standing dossier on any named individual independent of a client's own
  watch terms.
- **No cross-database/cross-workspace aggregation.** Every API query is scoped by
  `Membership` (Plan 7); one firm's data — including its matches on a given name — is
  invisible to another firm, proven by an automated cross-workspace isolation test.
  RegWatch does not correlate mentions of the same name across different client
  workspaces.
- **No secondary use or resale.** Match/digest data is used only to notify the
  workspace that requested the watch; it is not sold, shared, or repurposed.

## Sub-processors

- **Resend** (`RESEND_API_KEY`) — transactional email delivery for digests. Receives
  the digest body and the client's recipient email address per send.
- **Anthropic** (`ANTHROPIC_API_KEY`) — LLM summarization/categorization of matched
  act text. Receives the matched excerpt (already-public DOU text) per enrichment
  call; per the cross-cutting resilience rule, a failed enrichment call never blocks
  or corrupts a run — it simply leaves `ai_summary` null.

## Retention

Match and digest records persist for the operational life of the workspace's watch —
a firm reasonably needs its own match history. Deleting a `Workspace` cascades to its
`Client`/`Watch`/`Match`/`Digest` records.

## Data subject requests

An individual named in a DOU act who wishes to exercise LGPD rights (Art. 18) should
be directed to the professional-services firm operating the relevant workspace, which
holds the underlying watch relationship; RegWatch does not have an independent
relationship with the named individual. <Owner: confirm/adjust this framing —
whether RegWatch acts as controller or operator for this data flow is a legal
determination this draft does not make.>

## Open item flagged from Gate 3

Supabase backup/restore posture (automated backups vs Point-in-Time Recovery) is
documented in `deploy/RUNBOOK.md`'s "Gate 3 evidence" section — see that doc for
current status before onboarding real client/personnel data.
