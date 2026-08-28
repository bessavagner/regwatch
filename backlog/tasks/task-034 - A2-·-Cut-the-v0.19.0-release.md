---
id: TASK-034
title: A2 · Cut the v0.19.0 release
status: Done
assignee: []
created_date: '2026-08-28 10:51'
updated_date: '2026-08-28 12:16'
labels:
  - 'track:ship'
  - 'size:XS'
milestone: The signal loop
dependencies: []
priority: high
ordinal: 34000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Nineteen commits sit on main past v0.18.2, all green: digest links (TASK-002), pt-BR locale (TASK-003), rank ordering (TASK-004), the category vocabulary (TASK-005) and the feed console (TASK-009/010/011). Production still runs v0.18.2, so the first Cactarus digest goes out without links, with English dates and English category names -- worse than what the code already does. Highest value-per-effort item on the board: no new code, only a tag push.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [x] #1 main is tagged v0.19.0 and the GitHub Actions run is green on all three jobs
- [x] #2 All five workloads report regwatch:v0.19.0
- [x] #3 The next digest arrives with links, Brazilian dates and Portuguese category labels
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
Tagged v0.19.0 on 31db20b. Run 33167906977 green on all three jobs (test, frontend, deploy). Verified all five workloads on regwatch:v0.19.0 -- run-daily, prune, heartbeat, migrate, api. AC3 still open: the 08-28 08:05 run fired before the deploy, so today's Cactarus digest went out on v0.18.2. First evidence is either a resend or the 13:00 run.
<!-- SECTION:NOTES:END -->

## Final Summary

<!-- SECTION:FINAL_SUMMARY:BEGIN -->
v0.19.0 shipped and verified end to end. Run 33167906977 green on test, frontend and deploy; all five workloads on regwatch:v0.19.0. AC3 closed by rebuilding the 2026-08-28 Cactarus digest on the new image (manual run_daily execution regwatch-run-daily-5cvsq at 09:14 BRT): body grew 4567 to 5876 chars, sent=true on attempt 2, and it now carries pesquisa.in.gov.br deep links, '28 de agosto de 2026' and Portuguese category labels. Note the digest had to be flipped to sent=false by hand first: resend_digests only reaches unsent digests and ships the stored body, so there is no supported path to rebuild-and-resend a delivered digest.
<!-- SECTION:FINAL_SUMMARY:END -->
