---
id: TASK-001
title: A1 · Commit and deploy the 08-26 fixes
status: In Progress
assignee: []
created_date: '2026-08-26 17:28'
updated_date: '2026-08-26 18:08'
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
- [ ] #3 A midday run logs ingested=0 instead of rewriting ~3,400 unchanged rows
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Committed as four commits on main: ceb7809 (backlog board), 3cf5a0f (scheduler invoker + alert policy + runbook), 7a513e8 (ingest diff-then-write), 6eb9f2a (pip>=26.2 for the audit gate).

Tagged v0.18.1 first; its run failed at the pip-audit gate BEFORE pytest ran (PYSEC-2026-3721 against pip 26.1.2, which pip-audit pulls in via pip-api -- new advisory since the 2026-08-20 deploy, unrelated to these changes). Deploy job was skipped, so nothing shipped under v0.18.1 and it remains a dead tag. Fixed by flooring pip at 26.2 rather than adding a fourth --ignore-vuln (pip is dev-group only; the image builds with uv sync --no-dev).

Re-cut as v0.18.2, run 32997247393 green on all three jobs. Verified all five workloads now run regwatch:v0.18.2 (run-daily, prune, heartbeat, migrate, api).

AC3 not yet verifiable: today's 13:00 run predates the deploy, so the first evidence is the 2026-08-27 13:00 run.

Also confirmed roles/run.invoker IS live on regwatch-prune. Note its scheduler status.code still reads 7 -- that is the last ATTEMPT (2026-08-23T07:00Z, schedule 0 4 * * 0), which predates the grant. First attempt that can clear it is Sunday 2026-08-30.
<!-- SECTION:NOTES:END -->
