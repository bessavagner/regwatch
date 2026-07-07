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

**First deploy order:** push the image → run the `migrate` Job once (creates
`django_session`) → `deploy/deploy-api.sh` → provision a user with
`invite_user`. Provision a user against the Service by running the
`invite_user` command as a one-off Job execution, or via a `migrate`-style
admin Job.

**Smoke (private Service, authenticated caller):**
`TOKEN=$(gcloud auth print-identity-token)`; `POST /api/auth/login` with the
seeded credentials returns the `me` payload; `GET /api/me` returns the
workspace. A cross-workspace id returns 404.
