---
id: TASK-002
title: B1 · Put links in the digest
status: In Progress
assignee: []
created_date: '2026-08-26 17:29'
updated_date: '2026-08-26 18:56'
labels:
  - 'track:digest'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 2000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
The digest template renders category, summary, title and agency and no href anywhere. Act.source_url and Act.source_anchor already exist on the model and are exposed through the API. Highest value-per-line change available in the product: a client who reads a summary today has no way to reach the act.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Every digest item links to its act in the DOU
- [x] #2 Link uses source_anchor where available
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Added Act.dou_url (src/gazette/models.py) and rendered it under each digest item.

source_anchor is INlabs' pdfPage -- a public pesquisa.in.gov.br page view of the exact page the act ran on. Verified live: it 200s, and the stored http:// 301s to https://, so dou_url upgrades the scheme rather than send readers through a redirect that mail filters flag.

Edition.source_url is deliberately NOT the fallback: the task description called it 'Act.source_url', but it is actually on Edition and holds the authenticated INlabs zip endpoint (login wall, then an archive) -- useless to a reader. When source_anchor is blank the fallback is https://www.in.gov.br/leiturajornal?data=DD-MM-YYYY&secao=doN, verified 200 for do1/do2/do3/do1e.

Also wrapped daily.txt in {% autoescape off %}: Django autoescapes .txt templates, which would have shipped &amp; inside the query string and broken every link. Same fix stops agency names like 'MDIC & BNDES' arriving escaped.

Widened the notifier select_related to act__edition so the fallback branch does not N+1.

10 new tests; full suite 270 passed (was 260).
<!-- SECTION:NOTES:END -->
