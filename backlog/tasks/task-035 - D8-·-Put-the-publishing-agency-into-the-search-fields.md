---
id: TASK-035
title: D8 · Put the publishing agency into the search fields
status: To Do
assignee: []
created_date: '2026-08-28 10:51'
updated_date: '2026-08-28 10:52'
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
- [ ] #1 agency is included in search_text and in search_vector_pt at ingest
- [ ] #2 Existing retained acts are backfilled so old and new rows agree
- [ ] #3 Watch 9 reaches its measured volume without the Ceara helper group
<!-- AC:END -->
