---
id: TASK-001
title: A1 · Commit and deploy the 08-26 fixes
status: In Progress
assignee: []
created_date: '2026-08-26 17:28'
updated_date: '2026-08-26 17:56'
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
- [ ] #1 Changes committed and tagged
- [ ] #2 Deployed via tag push
- [ ] #3 A midday run logs ingested=0 instead of rewriting ~3,400 unchanged rows
<!-- AC:END -->
