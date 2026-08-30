---
id: TASK-028
title: G1 · Extend alerting to delivery
status: In Progress
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-30 15:22'
labels:
  - 'track:ops'
  - 'size:S'
dependencies: []
documentation:
  - docs/backlog.md
priority: medium
ordinal: 28000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
2026-08-26 showed the alert policies only catch jobs that ran and failed: a scheduler trigger that never launched was invisible for six days. That hole is now covered by policy-scheduler-trigger-denied.json. The remaining one is silent partial delivery, where a digest fails for one client while the run still exits 0.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 A digest that fails for one client raises an alert
- [x] #2 Alert fires without failing the whole run
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Verification, not construction - the alerting was already built and the missing piece was the row it inspects (TASK-012).

Confirmed live in the project, not merely present as files:
  gcloud alpha monitoring policies list ->
    RegWatch run_daily execution failed             True
    RegWatch scheduler trigger failed (job never started)  True
    RegWatch heartbeat failed (no successful run today)    True
  gcloud alpha monitoring channels list -> 'RegWatch alerts' (email), exactly one
  gcloud scheduler jobs list --location=us-east4 ->
    regwatch-heartbeat  0 14 * * 1-5  ENABLED
No duplicate policies or channels, so provision.sh has not been re-run.

Regression test added: test_a_digest_failing_for_one_client_alerts_without_failing_the_run. One client's send is rejected (403), the other succeeds, run_daily exits 0 and still serves the healthy client, RunLog is 'partial' with digests=2/sent=1, and check_heartbeat for that date raises CommandError naming '1 digests not sent'. That is both ACs in one test: the alert fires (heartbeat job fails -> policy pages) and the run is not failed by it.

AC#1 and AC#2 ticked on that evidence. Outstanding before Done: deploy with v0.28.0 so the quiet-day rows exist in production for the heartbeat to inspect.
<!-- SECTION:NOTES:END -->
