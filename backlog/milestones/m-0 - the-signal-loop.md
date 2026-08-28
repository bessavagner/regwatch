---
id: m-0
title: "The signal loop"
---

## Description

One operator, one client, one feed that corrects itself.

The board was written when five pilot clients existed and the bet was that clients would triage and produce labels. As of 2026-08-27 there is one client -- Cactarus, the house client -- and the reader, the triager and the operator are the same person. That removes Track E from the critical path and makes the quality of the daily loop the bottleneck.

Stage 0, ship what is already coded: TASK-034.
Stage 1, make it visible why an act matched: TASK-021, TASK-008, TASK-035.
Stage 2, triage fast and never confuse silence with failure: TASK-024, TASK-012, TASK-013.
Stage 3, give the feed something to order by: TASK-006, TASK-022, TASK-007.

Exit criterion: TASK-030 can be opened from human labels instead of samples.

Out of scope on purpose: Track E (TASK-014 to TASK-020) has no external user to serve; TASK-025 to TASK-027 depend on an audience that does not exist; TASK-023 waits for TASK-021. TASK-032 (Supabase Pro plus PITR) stays outside this plan but became more urgent on 2026-08-28, when 1,015 matches and 61 digests were deleted with only a CSV export as the safety net.
