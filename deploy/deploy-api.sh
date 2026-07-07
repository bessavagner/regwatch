#!/usr/bin/env bash
# Deploy the RegWatch API as an always-on Cloud Run Service from the SAME
# image the batch Jobs use, overriding the container command to run gunicorn.
# The run_daily / check_heartbeat / migrate Jobs are untouched.
set -euo pipefail

PROJECT="${PROJECT:?set PROJECT}"
REGION="${REGION:-us-east4}"
IMAGE="${IMAGE:?set IMAGE to the pushed Artifact Registry image ref}"
RUNTIME_SA="${RUNTIME_SA:?set RUNTIME_SA (least-privilege runtime service account)}"
# A Cloud Run service is reachable on more than one host (the canonical
# <svc>-<hash>-<regioncode>.a.run.app and the <svc>-<projectnumber>.<region>.run.app
# URL), so ALLOWED_HOSTS / CSRF_ORIGINS may be comma-separated lists of hosts.
ALLOWED_HOSTS="${ALLOWED_HOSTS:?set ALLOWED_HOSTS e.g. host1.a.run.app,host2.run.app}"
CSRF_ORIGINS="${CSRF_ORIGINS:?set CSRF_ORIGINS e.g. https://host1.a.run.app,https://host2.run.app}"

# `^@^` makes gcloud use "@" as the env-var separator so the commas inside a
# multi-host ALLOWED_HOSTS / CSRF_ORIGINS list are not misread as new env vars.
gcloud run deploy regwatch-api \
  --project="$PROJECT" --region="$REGION" \
  --image="$IMAGE" \
  --service-account="$RUNTIME_SA" \
  --command="/app/.venv/bin/gunicorn" \
  --args="config.wsgi,--bind,0.0.0.0:8080,--workers,2,--timeout,60" \
  --port=8080 \
  --no-allow-unauthenticated \
  --set-env-vars="^@^DJANGO_ALLOWED_HOSTS=${ALLOWED_HOSTS}@DJANGO_CSRF_TRUSTED_ORIGINS=${CSRF_ORIGINS}" \
  --set-secrets="SECRET_KEY=SECRET_KEY:latest,DATABASE_URL=DATABASE_URL:latest"

echo "Deployed. Run the 'migrate' Job once (creates django_session) before first use."
