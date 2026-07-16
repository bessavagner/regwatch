# RegWatch Ops Runbook (Plan 6)

## One-time setup
1. `export PROJECT_ID=... REGION=us-east4 ALERT_EMAIL=you@example.com`
   REGION **must be co-located with the Supabase DB region** (see Database below).
2. `bash deploy/provision.sh` — enables APIs, creates SAs, Artifact Registry, secrets, the three
   Cloud Run Jobs, the three schedulers, and the two alert policies. Add secret versions when prompted.
3. Configure GitHub → GCP **Workload Identity Federation** (see `.github/workflows/deploy.yml` header),
   then push a tag `vX.Y.Z` to build and deploy the real image.
4. Scheduler auth: per-job `roles/run.invoker` on `regwatch-run-daily` and `regwatch-heartbeat`;
   triggers hit the Cloud Run Jobs **v2** `:run` endpoint.

## CI dependency vulnerability scan (Gate 2, pre-Phase-5)

- `test` job: `uv run pip-audit` after `uv sync` — fails the build on any known Python
  dependency vulnerability (pip-audit's exit code cannot be globally suppressed;
  per-CVE/GHSA exceptions go through `--ignore-vuln <ID>` with a comment explaining why).
- `frontend` job: `pnpm audit --audit-level=high` after `pnpm install` — fails the build on
  high/critical web dependency vulnerabilities only (low/moderate transitive build-tooling
  findings are noise at this project's scale).
- Both run on every push to `main` and every PR (`on.push.branches`/`on.pull_request`), not
  just on a version tag. The `deploy` job is unaffected — it still only runs on a `v*` tag
  push or `workflow_dispatch`, gated by `if: github.event_name == 'workflow_dispatch' ||
  startsWith(github.ref, 'refs/tags/')`. Verified live 2026-07-16: push to `main` (run
  [29497619356]) ran `test`+`frontend` (both green, including the two new audit steps) while
  `deploy` showed skipped, not failed.
- **Current exemption (revisit when Django 5.2.16 ships):** `django` `5.2.15` carries three
  known CVEs (`PYSEC-2026-2090`, `PYSEC-2026-2091`, `PYSEC-2026-2092`) with no in-range fix —
  the fix version `5.2.16` isn't published on PyPI yet; only the major-version `6.0.7` carries
  it, and this repo pins `django>=5.0,<6.0` deliberately. None of the three affected code paths
  (`cache_page`/`UpdateCacheMiddleware`, `GDALRaster`, `DomainNameValidator`) are used in this
  codebase. Exempted via `--ignore-vuln` in the `test` job (see the comment above that step in
  `.github/workflows/deploy.yml`). Once `5.2.16` is published, `uv lock` will pick it up
  automatically (constraint is already `<6.0`) — remove the three `--ignore-vuln` flags and
  their comment at that point.

## Database
- Prod `DATABASE_URL` MUST be the Supabase **session pooler** URI (IPv4, port 5432,
  user `postgres.<project-ref>`), with `?sslmode=require`. The direct host `db.<ref>.supabase.co`
  is IPv6-only and unreachable from Cloud Run.
- **Region co-location is mandatory.** Deploy Cloud Run in the GCP region nearest the
  Supabase AWS region (e.g. `us-east4` for a Supabase in `aws us-east-2`). `run_daily`
  does thousands of DB round-trips per day; cross-region RTT (~150 ms São Paulo→Ohio)
  makes it exceed even a 1 h task timeout, while co-located (~10 ms) it finishes in ~10 min.
- **Task timeout:** `regwatch-run-daily` needs `--task-timeout=3600 --cpu=2 --memory=2Gi`
  (Cloud Run's 600 s default is far too short for a full DOU day). `provision.sh` sets this.
- Restore: use Supabase dashboard → Database → Backups / PITR. Test a restore before real client data.

## Common operations
- **Replay a day:** `gcloud run jobs execute regwatch-run-daily --region "$REGION" --args=run_daily,--date=2026-06-26 --wait`
- **Run migrations manually:** `gcloud run jobs execute regwatch-migrate --region "$REGION" --wait`
- **Force a heartbeat check:** `gcloud run jobs execute regwatch-heartbeat --region "$REGION" --wait`
- **Read a RunLog:** connect to Supabase and `SELECT * FROM pipeline_runlog ORDER BY started_at DESC LIMIT 5;`
- **Rotate a secret:** `printf '%s' 'NEWVALUE' | gcloud secrets versions add <NAME> --data-file=-` (jobs read `:latest` on next run).
- **Silence alerts during maintenance:** disable the policy in Cloud Monitoring → Alerting, re-enable after.

## Alerts
- **run_daily failed** → a `regwatch-run-daily` execution exited non-zero (pipeline error; check logs).
- **heartbeat failed** → no successful RunLog for today by 09:00 BRT (scheduler misfire, crash, or a
  failing run_daily). Check the morning execution and Cloud Scheduler.
  Note: the heartbeat runs 09:00 BRT while the morning run fires 08:05 BRT. If a morning run
  legitimately takes longer than ~55 min, move the `regwatch-heartbeat` scheduler later (e.g. 10:00)
  to avoid a false "no successful run today" alert. The 13:00 sweep + idempotent re-runs already
  cover the real gap.

## API Service (Plan 7)

The API is an always-on Cloud Run **Service** (`regwatch-api`) built from the
same image as the batch Jobs. Deploy with `deploy/deploy-api.sh` (set PROJECT,
IMAGE, RUNTIME_SA, ALLOWED_HOSTS, CSRF_ORIGINS). It overrides the container
command to run gunicorn on `config.wsgi`; the Jobs are unaffected.

A Cloud Run service answers on **two** hosts — the canonical
`regwatch-api-<hash>-<regioncode>.a.run.app` and
`regwatch-api-<projectnumber>.<region>.run.app`. Register **both** by passing
comma-separated lists, e.g.
`ALLOWED_HOSTS=hostA,hostB CSRF_ORIGINS=https://hostA,https://hostB`
(the script uses gcloud's `^@^` delimiter so the commas survive).

**First deploy order:** push the image → run the `migrate` Job once (creates
`django_session`) → `deploy/deploy-api.sh` → provision a user with
`invite_user`. Provision a user by running `invite_user` as a one-off Job that
mounts the `DATABASE_URL` secret; supply the password via a Secret Manager
secret bound to `INVITE_USER_PASSWORD` (never `--password` on the Job, which
persists in inspectable Job config).

**Smoke (public Service, `--allow-unauthenticated`, app-gated):** the Service
itself accepts unauthenticated HTTP requests — there is no Cloud Run IAM/token
gate to work around. `curl https://<host>/api/me` (no credentials) directly.
Django invite-only session auth is the actual gate: `POST /api/auth/login`
with the seeded credentials returns the `me` payload, `GET /api/me` returns
the workspace, and a cross-workspace id returns 404. Any other `/api` route
called without a valid session cookie returns 401/403.

### Same-origin SPA + public access (Plan 8)

The image is now multi-stage: a Node stage builds `web/` and the Python image
carries the bundle at `/app/web-dist`. Django serves it same-origin with `/api`
via WhiteNoise (assets + `/`) and a non-`/api` catch-all (`config.spa.spa_index`)
for client-side routes. `SPA_DIST_DIR` overrides the bundle location (default
`/app/web-dist`).

The Service runs `--allow-unauthenticated`: **Django invite-only session auth is
the only gate**; every `/api` view is `IsAuthenticated`, so the unauthenticated
surface is the login form only. Confirm `DJANGO_ALLOWED_HOSTS` and
`DJANGO_CSRF_TRUSTED_ORIGINS` include **both** Service hosts (see the two-host
note above) before first browser use.

### Dashboard first-deploy (Plan 8)

1. Build+push the multi-stage image (the Node stage builds `web/`; the bundle
   ships at `/app/web-dist`).
2. `migrate` Job once (django_session), if new.
3. `deploy/deploy-api.sh` with **both** Service hosts in `ALLOWED_HOSTS`/`CSRF_ORIGINS`
   (`--allow-unauthenticated`, app-gated).
4. Seed the pilot user via the `invite_user` one-off Job (`INVITE_USER_PASSWORD` secret).
5. Live smoke: `PLAYWRIGHT_BASE_URL=https://<host> E2E_USER=… E2E_PASS=… pnpm run e2e`.
   Login → `/api/me` (csrf) → triage `relevant` (X-CSRFToken) must all pass over HTTPS.

The unauthenticated surface is the login form only; every `/api` view is
`IsAuthenticated`. If a write 403s, check `csrftoken` is set (GET `/api/me` first)
and that `CSRF_TRUSTED_ORIGINS` includes the app origin.

## Gate 1 evidence — live-deploy confirmation (pre-Phase-5)

- Infra check (2026-07-15): `gcloud run jobs list` showed `regwatch-migrate`,
  `regwatch-run-daily`, `regwatch-heartbeat` (plus `regwatch-invite-user`, a Plan 8
  pilot-seeding leftover); `regwatch-api` Service printed its URL and `True`;
  `gcloud scheduler jobs list` showed all three jobs (`regwatch-morning` `5 8 * * 1-5`,
  `regwatch-midday` `0 13 * * 1-5`, `regwatch-heartbeat` `0 9 * * 1-5`, all
  `America/Sao_Paulo`) `ENABLED`.
- Unattended runs: 2026-07-15, both `regwatch-morning` (08:05 BRT) and `regwatch-midday`
  (13:00 BRT) fired naturally before this check — `RunLog#12` (08:05 run) and `RunLog#13`
  (13:00 run), both `status=success` (editions=3 acts=3425 matches=0 enriched=0 digests=0).
  Noted, pre-dating this check and self-healed by the job's own retry policy:
  `RunLog#11` recorded a 1-second `failed` row at 11:05:30 UTC immediately before `RunLog#12`
  succeeded at 11:05:48 UTC — a transient retry, not an outage.
- Digest sent: no `digests_digest` rows exist for 2026-07-15 or 2026-07-14 — expected, since
  both days had `matches=0` (a zero-match day produces zero digest rows; this is a valid
  `success` outcome, not a failure).
- Alert A (run-failed): forced by rotating `INLABS_PASSWORD` to a bad value in Secret Manager,
  then running `gcloud run jobs execute regwatch-run-daily --args=run_daily,--date=2026-07-15
  --wait` (safe replay of an already-successful date — `fetch_editions` fails before any
  `Edition`/`Act` write). Execution failed as expected; secret reverted to the real value
  immediately after. Post-hoc check confirmed idempotency held: `RunLog#14`/`#15` (both
  `failed`, ~21:17 UTC) were appended, while the pre-existing `RunLog#12`/`#13` success rows for
  2026-07-15 were untouched. "RegWatch run_daily execution failed" email confirmed received at
  the `$ALERT_EMAIL` notification channel within the alert policy's aggregation window.
- Alert B (heartbeat-failed): forced via `gcloud run jobs execute regwatch-heartbeat
  --args=check_heartbeat,--date=2026-07-12 --wait` (a past Sunday with no successful `RunLog`,
  no revert needed — read-only check). Execution failed as expected (`CommandError: heartbeat:
  no successful RunLog for 2026-07-12`). "RegWatch heartbeat failed (no successful run today)"
  email confirmed received at the `$ALERT_EMAIL` notification channel.

## Gate 3 evidence — backup/restore test (pre-Phase-5)

- Checked 2026-07-16 via `GET /v1/projects/{ref}/database/backups` (Supabase Management API):
  **PITR not enabled** (`pitr_enabled: false`, `backups: []`) — this project is on the Free
  plan, with neither Point-in-Time Recovery nor automated daily backups.
- Logical restore drill performed instead: `pg_dump` (via a `postgres:17` container — the host's
  `pg_dump` 16 cannot read a Postgres 17 server, which is what Supabase runs) against the
  session pooler → restored into a scratch local Postgres 17 container → row counts verified to
  match exactly between prod and the restored copy: `pipeline_runlog` (13/13), `watches_watch`
  (2/2). The only restore errors were expected/harmless (`supabase_vault` extension and
  `vault.secrets` table don't exist outside Supabase's managed Postgres — irrelevant to
  application tables). Scratch container and dump file torn down immediately after verification.
- **This is not a substitute for a true PITR test** — flagged as a follow-up once the project
  upgrades to Supabase Pro + the PITR add-on, before real client data lands (tracked in
  `docs/sprints/backlog.md`'s cross-cutting section).
- Restore procedure (repeat before every future plan-tier change, or periodically once real
  client data is in prod):
  1. `pg_dump` via the session pooler (`SUPABASE_DB_URL`) using a `pg_dump` binary matching the
     server's major version (currently 17) — `--no-owner --no-privileges`, output to a local
     scratch file that is deleted immediately after use, never committed.
  2. `docker run --rm -d -e POSTGRES_PASSWORD=<throwaway> -p <free-port>:5432 postgres:17`.
  3. `psql` the dump into the scratch container.
  4. Compare `SELECT count(*)` on the app's core tables (`pipeline_runlog`, `watches_watch`, plus
     any tables added since) between prod and the restored copy.
  5. `docker rm -f` the scratch container and delete the local dump file — the dump contains
     real (if only dev/test) data and must not persist on disk or be committed.
