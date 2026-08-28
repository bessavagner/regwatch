---
id: TASK-001
title: A1 · Commit and deploy the 08-26 fixes
status: Done
assignee: []
created_date: '2026-08-26 17:28'
updated_date: '2026-08-28 10:52'
labels:
  - 'track:ship'
  - 'size:XS'
dependencies: []
documentation:
  - docs/backlog.md
priority: high
ordinal: 1000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Today's fixes sit uncommitted: provision.sh (prune added to the invoker loop), policy-scheduler-trigger-denied.json, gazette/ingest.py (diff-then-write), pipeline/runner.py, three test files, runbook.md. 260 tests green. The IAM grant, alert policy and prune run are ALREADY applied to production; only the repo changes and the ingest fix need a deploy.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 Changes committed and tagged
- [x] #2 Deployed via tag push
- [x] #3 A midday run logs ingested=0 instead of rewriting ~3,400 unchanged rows
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
AC3 verified on the 2026-08-27 13:00 run: ingested_acts=0 against acts=3274, 142s versus 226s for the morning run. The diff-then-write fix shipped in v0.18.2 and no longer rewrites unchanged rows.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
Shipped as v0.18.2 (run 32997247393). All five workloads on the tag; the midday re-ingest is gone, measured in production.
<!-- SECTION:FINAL_SUMMARY:END -->
