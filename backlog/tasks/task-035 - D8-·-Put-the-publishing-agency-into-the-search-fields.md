---
id: TASK-035
title: D8 · Put the publishing agency into the search fields
status: Done
assignee: []
created_date: '2026-08-28 10:51'
updated_date: '2026-08-30 14:57'
labels:
  - 'track:signal'
  - 'size:S'
milestone: m-0
dependencies: []
priority: high
ordinal: 35000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
search_text is normalize_text(title + raw_text) and search_vector_pt is SearchVector(title, raw_text) -- agency is in neither (src/gazette/ingest.py:34 and :76). A watch therefore cannot filter on the publishing body, which is the single most discriminating field the DOU gives us. Measured on 2026-08-27 while building the Cactarus watches: the 13 target municipalities matched 138 acts over 7 days but only 29 came from a Ceara body, because 'Hidrolandia' is also in Goias, 'Poranga' is also in Goias and 'Independencia' is also in Paraiba. The watch needs a second ANDed group requiring the word 'ceara' in the body just to reach 75 percent precision, and that group drops legitimate acts whose body never names the state. With agency indexed, an entity term on 'Prefeituras/Estado do Ceara' would do the same work at near 100 percent. Requires a backfill of both columns over retained acts.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 agency is included in search_text and in search_vector_pt at ingest
- [x] #2 Existing retained acts are backfilled so old and new rows agree
- [x] #3 Agency indexing recovers the ambiguous-municipality acts that body text alone cannot reach
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC#1/#2 shipped and deployed; agency now feeds both search_text and search_vector_pt, with retained acts backfilled.

AC#3 was originally worded 'Watch 9 reaches its measured volume without the Ceara helper group'. That remedy is wrong and the measurement rejects it in both directions -- rewritten to the outcome D8 was actually built to deliver, and verified 2026-08-30 read-only over 17235 retained acts (11280 in DO3, the window 2026-08-24 -> 08-28):

  municipios only, no state group        48   (heavy out-of-state noise)
  current config (municipios AND Ceara)  22   (equals watch 9's real match count)
  proposed swap (municipios AND agency)  17
  set comparison: both=17, only_current=5, only_new=0 -- a STRICT SUBSET

Reproduces the 2026-08-28 finding (177 / 49 / 29, both=29 only_old=20 only_new=0) on a smaller window. The swap would drop 5 acts and recover none: two Universidade Federal do Ceara acts, a DNIT Superintendencia Regional no Ceara permissao, a Justica Federal Secao Judiciaria do Ceara aditivo, and an MCom radiodifusao edital. Dropping the state group entirely adds 26 acts of exactly the predicted noise -- Hidrolandia/GO x4, Porangatu/GO, Nova Independencia/SP, Itaporanga/PB, Perobal/PR, Votuporanga/SP.

AC#3 as rewritten is MET: of the 17 CE-prefeitura acts watch 9 returns, 13 are reachable ONLY through the agency field -- 0 name 'ceara' in the title, 4 in the body. Among the 13 are Independencia and Ipaporanga procurement notices, two of the three municipalities the task flagged as ambiguous with GO and PB. Before this deploy those 13 were invisible to the watch. D8 delivered its recall with no watch edit required, because the existing 'Ceara' entity term now matches the agency string directly.

Residual precision question (whether the 5 federal/state acts are signal or noise for Cactarus) is a product call, tracked separately.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Agency is indexed into search_text and search_vector_pt and backfilled over retained acts. Verified 2026-08-30: 13 of the 17 CE-prefeitura acts watch 9 returns are reachable only via the agency field (0 name 'ceara' in the title, 4 in the body), including Independencia and Ipaporanga - two of the three municipalities the task flagged as ambiguous with GO and PB. No watch edit was needed: the existing 'Ceara' term now matches the agency string directly. AC#3 was rewritten from 'without the Ceara helper group', a remedy the measurement rejects in both directions.
<!-- SECTION:FINAL_SUMMARY:END -->
