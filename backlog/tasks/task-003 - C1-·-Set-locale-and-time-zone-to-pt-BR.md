---
id: TASK-003
title: C1 · Set locale and time zone to pt-BR
status: Done
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-28 10:52'
labels:
  - 'track:ptbr'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 3000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
LANGUAGE_CODE is unset so Django falls back to en-us and the digest date renders 'Aug. 26, 2026' in a Portuguese product, while the subject line uses ISO 2026-08-26. Two date formats in one message, neither Brazilian. TIME_ZONE is unset too.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 LANGUAGE_CODE = pt-br and TIME_ZONE = America/Sao_Paulo
- [x] #2 Dates render as 26 de agosto de 2026 in email and app
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
LANGUAGE_CODE=pt-br, TIME_ZONE=America/Sao_Paulo, USE_I18N=True in src/config/settings.py. USE_TZ stays True -- rows remain UTC.

Django's pt-BR DATE_FORMAT was already right, but its pt-BR catalogue capitalises month names: date_format() returns '26 de Agosto de 2026'. Portuguese orthography lowercases them and the AC asks for lowercase, so config/formatting.py::br_date lowercases the rendered string. Chose that over shipping a project .po override, which would need msgfmt at build time for twelve msgids.

Email: body header and subject both go through br_date, so the two no longer disagree (the subject was ISO, the body en-us).

App: the SPA had no date formatting at all -- it printed raw ISO. Added web/src/lib/format.ts::brDate (Intl, pt-BR, timeZone UTC) and used it in MatchCard and Digests. UTC matters: 'YYYY-MM-DD' parses as UTC midnight and rendering that at UTC-3 would show the previous day. Also set <html lang='pt-BR'>.

Dropped 'font-mono tabular-nums' from the Digests date line -- it was there to align ISO digits and no longer holds any.

Two existing SPA tests asserted the ISO text and now assert the Brazilian form.

Side effect worth knowing: prune_act_text counts retention from timezone.localdate(), so its cutoff is now a Brasilia day rather than a UTC one. Intended reading for a Brazilian product; shifts the boundary by at most a day on a 30-day window.

Python 277 passed; SPA 62 passed, eslint clean, build clean.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
LANGUAGE_CODE=pt-br, TIME_ZONE=America/Sao_Paulo, br_date in email and SPA. On main, ships in TASK-034.
<!-- SECTION:FINAL_SUMMARY:END -->
