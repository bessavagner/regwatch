# RegWatch Ops Runbook (Plan 6)

## One-time setup
1. `export PROJECT_ID=... REGION=southamerica-east1 ALERT_EMAIL=you@example.com`
2. `bash deploy/provision.sh` — enables APIs, creates SAs, Artifact Registry, secrets, the three
   Cloud Run Jobs, the three schedulers, and the two alert policies. Add secret versions when prompted.
3. Configure GitHub → GCP **Workload Identity Federation** (see `.github/workflows/deploy.yml` header),
   then push a tag `vX.Y.Z` to build and deploy the real image.
4. Scheduler auth: per-job `roles/run.invoker` on `regwatch-run-daily` and `regwatch-heartbeat`;
   triggers hit the Cloud Run Jobs **v2** `:run` endpoint.

## Database
- Prod `DATABASE_URL` MUST be the Supabase **session pooler** URI (IPv4, port 5432,
  user `postgres.<project-ref>`), with `?sslmode=require`. The direct host `db.<ref>.supabase.co`
  is IPv6-only and unreachable from Cloud Run.
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
