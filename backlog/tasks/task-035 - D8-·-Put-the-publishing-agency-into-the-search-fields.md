---
id: TASK-035
title: D8 · Put the publishing agency into the search fields
status: In Progress
assignee: []
created_date: '2026-08-28 10:51'
updated_date: '2026-08-28 14:51'
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
- [ ] #3 Watch 9 reaches its measured volume without the Ceara helper group
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC#3 MEASURED 2026-08-28 post-deploy, read-only, over the 28193 retained acts. Watch 9 (Cactarus) = [13 CE municipios ORed] AND ['Ceara'].
  municipios only, no state filter: 177
  current config (municipios AND 'Ceara'): 49
  proposed swap (municipios AND agency 'Prefeituras/Estado do Ceara'): 29
  set comparison: both=29, only_old=20, only_new=0 -- the swap is a STRICT SUBSET.

The swap was NOT applied. It would drop 20 acts (incl. a Governo do Estado do Ceara/Casa Civil licitacao, Banco do Nordeste contracts, MCom editais) and recover nothing.

Why the premise no longer holds: D8 put agency into search_text, so the EXISTING 'Ceara' entity term now matches the agency string 'Prefeituras/Estado do Ceara' directly. Of the 29 CE-prefeitura acts, only 6 name 'ceara' in the body and 0 in the title -- 23 are reachable ONLY via agency, among them Poranga / Hidrolandia / Independencia procurement notices, exactly the three municipalities the task flagged as ambiguous with GO and PB. Those 23 were unreachable before this deploy.

So D8 delivered the recall it promised with NO watch edit required. The AC as written ('without the Ceara helper group') asks for the wrong remedy: dropping the group entirely gives 177 with heavy out-of-state noise. What remains is a precision question for the client -- whether the 20 federal/state acts mentioning a municipality are signal or noise -- which is a product call, not a code one.
<!-- SECTION:NOTES:END -->
