---
id: TASK-035
title: D8 · Put the publishing agency into the search fields
status: In Progress
assignee: []
created_date: '2026-08-28 10:51'
updated_date: '2026-08-28 14:22'
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
PRODUCTION (2026-08-28, v0.20.0): deploy green (run 33178622723, all three jobs); image regwatch:v0.20.0 confirmed on regwatch-migrate; migration 0003 applied ([X] in showmigrations). reindex_search --all rebuilt BOTH columns over 28193 acts in 56 batches, exit 0; a follow-up run without --all reported 'reindex_search: 0 acts', proving no non-pruned act is left without a vector. AC#1 and AC#2 now verified in production, not just in tests.

AC#3 NOT verified and deliberately left open. Watch 9 is Cactarus: 13 CE municipalities in one group plus a 'Ceará' helper group. watch_term_contexts now reports only 3 matched acts still holding text -- the 7-day retention window has pruned the corpus the original 2026-08-27 measurement (138 acts / 29 from a CE body) was taken on, so that measurement cannot be reproduced as-is. Reproducing it needs: (a) editing a live pilot client's watch to swap the 'Ceará' helper for an entity term on the agency, and (b) a backfill over a 7-day range, which re-fetches pruned dates from INlabs and writes new matches into a real client's feed. Both need explicit sign-off. Noted meanwhile: the helper term currently fires on 'universidade federal do ceara' in 2 of the 3 retained acts -- the exact false positive D8 is meant to remove.
<!-- SECTION:NOTES:END -->
