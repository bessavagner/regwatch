---
id: decision-002
title: 'pt-BR is a hard switch, not i18n'
date: '2026-08-26 17:30'
status: accepted
---
## Context

RegWatch monitors the Brazilian federal gazette and every client is Brazilian.
The product is currently a mix: the SPA is in English ("Client", "State",
"Relevant", "Dismiss") with Portuguese leaking through in places ("resumo
indisponível — mostrando o texto do ato"), the enrichment prompt and summaries
are Portuguese, and the digest is Portuguese prose wrapped in English dates and
English category enum values.

`LANGUAGE_CODE` was never set, so Django falls back to `en-us` and renders dates
as "Aug. 26, 2026" while the same email's subject line uses ISO `2026-08-26`.

## Decision

Switch everything user-visible to Portuguese. `LANGUAGE_CODE = "pt-br"`,
`TIME_ZONE = "America/Sao_Paulo"`, every string in the SPA, every email. No
gettext, no message catalogues, no locale switcher. English is dropped rather
than made optional.

The category vocabulary becomes a single Portuguese source of truth served from
the API, so the email and the SPA cannot drift apart again the way they have.

## Consequences

- Fastest path to a coherent product, and the one that matches who actually uses
  it.
- Accepted cost: adding English back later means retrofitting i18n across the
  app, string by string. This is a one-way door and was chosen knowingly.
- The internal category *values* stay English (`tender`, `penalty`, …) — they are
  a storage enum, not a user-facing string. Only the labels are translated.

Implemented by TASK-003, TASK-005, TASK-013, TASK-027.
