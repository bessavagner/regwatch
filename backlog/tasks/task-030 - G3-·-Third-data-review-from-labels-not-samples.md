---
id: TASK-030
title: 'G3 · Third data review, from labels not samples'
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-30 15:44'
labels:
  - 'track:ops'
  - 'size:S'
dependencies:
  - TASK-006
  - TASK-022
documentation:
  - docs/backlog.md
priority: low
ordinal: 30000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Do NOT open this by re-measuring precision from samples; that has now been done twice and says the same thing. See docs/analysis/2026-08-20-pilot-data-review.md and docs/analysis/2026-08-26-production-re-evaluation.md.

Open it with the labels the operator produces by triaging in-app. The original wording said 'whatever labels E5 has produced', but Track E left the critical path in decision-006 and E5 (TASK-018, deep links from the digest) is not being built. The labels now come from TASK-024's keyboard triage instead. Nothing else about this task changes - the source of the labels moved, not the question.

Wait for enough of them. Below ~150 triaged matches spanning at least two weeks any precision figure is noise; state the actual count in the document and say so plainly if it is thin rather than rounding up the confidence.

Beyond precision, answer what D5 could not: does signal_score predict 'relevant'? Cross the known distribution (31/57/13 across scores 1/2/3) with the human label. If score 3 is no more often relevant than score 1, the ranking is decorative, and that finding is worth more than a precision number. Same for category, and per-watch: watch 12 produced 40 of 101 matches, so if its precision is poor that is one watch edit worth more than any model change. Treat the 8 pre-existing dismissals as suspect - they were made while testing the dismiss fix - or re-judge them.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Precision reported from human labels, not from my sampling
- [ ] #2 Filed as a document in docs/analysis
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-08-30, during the close-the-loop plan: corrected the stale premise in the description only.

The plan instructed rewriting AC#1 because it 'says labels come from E5'. It does not - AC#1 reads 'Precision reported from human labels, not from my sampling', which is correct however the labels were produced. The E5 dependency was in the description. Rewriting a sound AC to satisfy a plan step would have been the worse of the two errors, so the description was corrected and both ACs left exactly as written.

Still blocked, and deliberately so: this needs ~150 triaged matches spanning two weeks. Production currently holds 101 matches, of which 93 are 'new' and 8 are dismissed - and those 8 were made while testing the dismiss fix, so they are suspect labels. TASK-024 shipped the triage tooling on 2026-08-30; the labels do not exist yet.

Next step is not code: triage real days with the new keyboard flow until the count is honest, then write the document.
<!-- SECTION:NOTES:END -->
