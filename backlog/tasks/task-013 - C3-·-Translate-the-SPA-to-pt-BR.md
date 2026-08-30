---
id: TASK-013
title: C3 · Translate the SPA to pt-BR
status: In Progress
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-30 15:32'
labels:
  - 'track:ptbr'
  - 'size:M'
milestone: m-0
dependencies:
  - TASK-005
documentation:
  - docs/backlog.md
priority: high
ordinal: 13000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Client, State, Section, Order, Relevant, Dismiss, Page: the console is in English with Portuguese leaking through in places such as 'resumo indisponivel - mostrando o texto do ato'. Includes the login screen, which is the first thing a beta user sees. Hard switch, no gettext, no locale switcher, English dropped.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 No English remains in any user-visible SPA string
- [x] #2 Login and error states covered
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Code complete on main, not yet deployed. Hard switch per decision-002: no gettext, no locale switcher, English dropped.

Glossary - Phase 3's new copy must match these:
  triage -> triagem | watches -> buscas | clients -> clientes | digests -> boletins
  match(es) -> ocorrência(s) | state -> situação | section -> seção | category -> categoria
  new/relevant/dismissed -> nova/relevante/descartada (labels only; stored values stay English)
  from/to -> de/até | order -> ordenar | prev/next -> anterior/próxima | page X of Y -> página X de Y
  save/edit/cancel -> salvar/editar/cancelar | dismiss -> descartar | run -> rodar
  sign in/username/password -> entrar/usuário/senha | log out -> sair | source -> fonte
  house -> interno | sent/not sent -> enviado/não enviado | active/inactive -> ativa/inativa

All copy authored lowercase: app.css:56 sets text-transform:lowercase as the prose
default (design.md's two-register split), with .as-typed and .field opting live data
out. Select <option> labels sit inside .field, so they are NOT auto-lowercased and had
to be authored lowercase by hand.

MatchCard rendered the raw English Match.state; added stateLabel() in constants.ts so
the stored enum stays English while the badge reads pt-BR.

Beyond the plan's file list: the 11 hand-written DRF validation messages in
src/watches/api.py are rendered verbatim in the SPA via err.detail/fieldErrors, so
leaving them would have made AC#1 false. Translated, with their web test mocks.
DRF's own built-ins were already pt-BR (LANGUAGE_CODE='pt-br', USE_I18N=True).

AC#1 verified by script, not asserted: parsed all 20 .svelte files for rendered text
nodes and display attributes (placeholder/aria-label/title/alt), matched against an
English word list excluding words that are also Portuguese -> 'CLEAN - no English in
any rendered string or display attribute'. Error copy inside <script> checked
separately: all 6 fallback literals are pt-BR.

Evidence: pnpm lint exit 0; pnpm test 18 files / 98 tests passed; pnpm run build 'built
in 635ms'; uv run pytest src -> 408 passed. npx tsc --noEmit: 9 errors, all
pre-existing (baseline was 10), none introduced.

NOT run: the Playwright suite. login.spec.ts and triage.spec.ts were translated
(triage.spec now scopes the badge assertion to a span, because the situação filter's
option carries the same 'relevante' text), but they need a live stack plus a seeded
E2E user, which is not available here. web/e2e/smoke.spec.ts is dead on main - it
still asserts the Vite starter counter ('count is 1') - and was left alone.

Outstanding before Done: v0.29.0 release, then the Playwright run.
<!-- SECTION:NOTES:END -->
