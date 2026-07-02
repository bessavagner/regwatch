#!/usr/bin/env bash
# deploy/provision.sh — one-shot GCP provisioning for RegWatch (run once, then rely on CI for deploys).
# Requires: gcloud (authenticated), the secrets listed below available to paste when prompted.
set -euo pipefail

: "${PROJECT_ID:?set PROJECT_ID}"
: "${REGION:=southamerica-east1}"
: "${ALERT_EMAIL:?set ALERT_EMAIL}"          # where failure alerts go
RUNTIME_SA="regwatch-run@${PROJECT_ID}.iam.gserviceaccount.com"
SCHED_SA="regwatch-scheduler@${PROJECT_ID}.iam.gserviceaccount.com"
AR_REPO="regwatch"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${AR_REPO}/regwatch:bootstrap"

gcloud config set project "${PROJECT_ID}"

echo "== Enable APIs =="
gcloud services enable \
  run.googleapis.com cloudscheduler.googleapis.com secretmanager.googleapis.com \
  artifactregistry.googleapis.com monitoring.googleapis.com logging.googleapis.com \
  iamcredentials.googleapis.com

echo "== Service accounts =="
gcloud iam service-accounts create regwatch-run --display-name="RegWatch runtime" || true
gcloud iam service-accounts create regwatch-scheduler --display-name="RegWatch scheduler invoker" || true

echo "== Artifact Registry =="
gcloud artifacts repositories create "${AR_REPO}" --repository-format=docker \
  --location="${REGION}" --description="RegWatch images" || true

echo "== Secrets (create empty; add versions below) =="
for s in DATABASE_URL SECRET_KEY ANTHROPIC_API_KEY RESEND_API_KEY RESEND_FROM; do
  gcloud secrets create "$s" --replication-policy=automatic || true
done
cat <<'EOF'
>>> Now add a version to each secret, e.g.:
    printf '%s' 'postgresql://postgres.<ref>:<pw>@aws-0-<region>.pooler.supabase.com:5432/postgres?sslmode=require' \
      | gcloud secrets versions add DATABASE_URL --data-file=-
    printf '%s' "$(python -c 'import secrets;print(secrets.token_urlsafe(50))')" \
      | gcloud secrets versions add SECRET_KEY --data-file=-
    # ...and ANTHROPIC_API_KEY, RESEND_API_KEY, RESEND_FROM likewise.
    Use the Supabase *session pooler* URI (IPv4, port 5432) — NOT db.<ref>.supabase.co (IPv6-only).
EOF
read -r -p "Press Enter once all secret versions are added... " _

echo "== IAM: runtime SA may read secrets + write logs =="
for s in DATABASE_URL SECRET_KEY ANTHROPIC_API_KEY RESEND_API_KEY RESEND_FROM; do
  gcloud secrets add-iam-policy-binding "$s" \
    --member="serviceAccount:${RUNTIME_SA}" --role="roles/secretmanager.secretAccessor"
done
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${RUNTIME_SA}" --role="roles/logging.logWriter"

SECRET_FLAGS="--set-secrets=DATABASE_URL=DATABASE_URL:latest,SECRET_KEY=SECRET_KEY:latest,ANTHROPIC_API_KEY=ANTHROPIC_API_KEY:latest,RESEND_API_KEY=RESEND_API_KEY:latest,RESEND_FROM=RESEND_FROM:latest"

echo "== Cloud Run Jobs (bootstrap image; CI redeploys real images) =="
for job in "regwatch-migrate:migrate" "regwatch-run-daily:run_daily" "regwatch-heartbeat:check_heartbeat"; do
  name="${job%%:*}"; cmd="${job##*:}"
  gcloud run jobs create "${name}" --image="${IMAGE}" --region="${REGION}" \
    --service-account="${RUNTIME_SA}" --args="${cmd}" ${SECRET_FLAGS} --max-retries=1 || \
  gcloud run jobs update "${name}" --image="${IMAGE}" --region="${REGION}" \
    --service-account="${RUNTIME_SA}" --args="${cmd}" ${SECRET_FLAGS} --max-retries=1
done

echo "== Scheduler may run jobs =="
gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
  --member="serviceAccount:${SCHED_SA}" --role="roles/run.developer"

run_uri() { echo "https://${REGION}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${PROJECT_ID}/jobs/$1:run"; }
mk_sched() {  # name schedule job
  gcloud scheduler jobs create http "$1" --location="${REGION}" --schedule="$2" \
    --time-zone="America/Sao_Paulo" --uri="$(run_uri "$3")" --http-method=POST \
    --oauth-service-account-email="${SCHED_SA}" || \
  gcloud scheduler jobs update http "$1" --location="${REGION}" --schedule="$2" \
    --time-zone="America/Sao_Paulo" --uri="$(run_uri "$3")" --http-method=POST \
    --oauth-service-account-email="${SCHED_SA}"
}
echo "== Cloud Scheduler triggers (BRT, Mon-Fri) =="
mk_sched regwatch-morning   "5 8 * * 1-5"  regwatch-run-daily
mk_sched regwatch-midday    "0 13 * * 1-5" regwatch-run-daily
mk_sched regwatch-heartbeat "0 9 * * 1-5"  regwatch-heartbeat

echo "== Alerting: email channel + two policies =="
CHANNEL=$(gcloud beta monitoring channels create --display-name="RegWatch alerts" \
  --type=email --channel-labels="email_address=${ALERT_EMAIL}" --format="value(name)")
gcloud alpha monitoring policies create --policy-from-file=deploy/policy-run-daily-failed.json \
  --notification-channels="${CHANNEL}"
gcloud alpha monitoring policies create --policy-from-file=deploy/policy-heartbeat-failed.json \
  --notification-channels="${CHANNEL}"

echo "Done. Push a v* tag to build/deploy the real image, or run a job manually (see RUNBOOK.md)."
