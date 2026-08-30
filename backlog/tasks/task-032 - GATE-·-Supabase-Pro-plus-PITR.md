---
id: TASK-032
title: GATE · Backups that survive losing the machine
status: To Do
assignee: []
created_date: '2026-08-26 17:30'
updated_date: '2026-08-30 20:25'
labels:
  - 'track:gate'
  - 'size:S'
dependencies: []
documentation:
  - docs/backlog.md
priority: medium
ordinal: 32000
---

## Description

<!-- SECTION:DESCRIPTION:BEGIN -->
Supabase Free has no PITR and no automated backups. The original plan was to upgrade to Pro plus the PITR add-on; the operator has decided not to pay for that while RegWatch is still in development and has no external users.

Replacement: local logical backups, taken deliberately rather than continuously. scripts/backup-db.sh dumps to .backups/ (gitignored) via a postgres:17 container, refuses to keep a dump missing any table that carries irreplaceable data, and prunes to the last 10. scripts/restore-drill.sh restores the newest dump into a throwaway container and compares row counts table by table.

What this protects: human triage labels on matching_match.state, watch definitions, clients. Acts and summaries are regenerable and do not need insuring.

What this does NOT protect against, stated plainly so it is not discovered later: everything since the last run, and the loss of this machine. The dumps live in one place. Revisit both limits before any real client data lands.
<!-- SECTION:DESCRIPTION:END -->

## Acceptance Criteria
<!-- AC:BEGIN -->
- [ ] #1 Project on Pro with the PITR add-on
- [ ] #2 Restore drill repeated through the real PITR endpoint
<!-- AC:END -->

## Implementation Notes

<!-- SECTION:NOTES:BEGIN -->
2026-08-30: retargeted away from Supabase Pro on the operator's decision not to upgrade.

Delivered and verified, not merely written:
  scripts/backup-db.sh -> 'ok: 26M, 101 rows in matching_match'
  scripts/restore-drill.sh -> 'restore drill PASSED' with every core table matching:
    matching_match 101/101, watches_watch 7/7, watches_client 1/1,
    digests_digest 1/1, gazette_act 17235/17235, gazette_edition 107/107,
    pipeline_runlog 115/115
That is a restore actually performed, which is the bar the plan set.

Runbook sections added: 'Back up the database to this machine' and 'Prove a
backup actually restores'.

Two defects found and fixed while building it:
  - SUPABASE_DB_URL carries a password containing a space, un-percent-encoded,
    so libpq rejects the URL outright and pg_dump echoes part of the password
    into its error message. The script now splits the URL and passes the
    password via PGPASSWORD, so it never reaches a command line or an error.
    The password was exposed in a terminal during this work - ROTATE IT.
  - The dump verification used 'grep -q' under 'set -o pipefail': grep exits
    early, gunzip dies of SIGPIPE, and the pipeline reports failure for a table
    that is present. It deleted a perfectly good backup once before this was
    caught. Now uses grep -c.

Accepted residual risk, recorded rather than hidden: backups are point-in-time
snapshots taken by hand, stored only on the operator's machine. Losing the
machine loses them. Fine for development; not fine once anyone else's data is
in there.
<!-- SECTION:NOTES:END -->
