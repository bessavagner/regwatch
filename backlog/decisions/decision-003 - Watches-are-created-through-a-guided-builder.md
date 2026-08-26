---
id: decision-003
title: 'Watches are created through a guided builder'
date: '2026-08-26 17:30'
status: accepted
---
## Context

A `Watch` is `groups` — a list of ANDed groups, each a list of ORed terms, each
term typed `entity` (substring) or `concept` (Portuguese-stemmed full text) —
plus a flat `exclude` list evaluated with substring semantics.

That is expert-level. Meridiano's watch reads
`(aviso de licitação | pregão eletrônico | concorrência pública)` AND
`(saneamento | pavimentação)`, and the difference between the two term kinds is
the difference between matching `licitações` and not matching it.

Meanwhile **every watch in production had an empty `exclude` list on
2026-08-26**, despite the 08-20 review showing excludes were the correct fix for
the `saneamento` noise and despite `watch_term_contexts` being built to find the
phrases. The mechanism was never the problem; reachability was.

## Decision

Beta users create watches through three plain-language inputs, compiled down to
the existing JSON:

| Input | Compiles to |
|---|---|
| *Avise-me sobre estas palavras* | one OR group |
| *Somente quando também mencionar* | a second ANDed group |
| *Nunca quando disser* | `exclude` |

Term `kind` is **inferred, not asked** — proper nouns and acronyms become
entities, everything else concepts. The matcher does not change at all.

## Consequences

- Nobody has to learn AND/OR group semantics or term kinds to use the product.
- The third input is the important one: it puts excludes in front of the person
  who actually knows which phrases are noise, at the moment they are thinking
  about the watch. `watch_term_contexts` then feeds it suggestions (TASK-023).
- Cost: inference will sometimes pick the wrong kind. The builder must show what
  it inferred and let it be overridden, or a user will be unable to explain why
  their watch missed something.
- The operator console keeps the raw form; this does not replace it.

Implemented by TASK-016, fed by TASK-023.
