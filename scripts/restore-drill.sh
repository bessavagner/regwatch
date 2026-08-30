#!/usr/bin/env bash
# Restore a local backup into a throwaway Postgres and prove it came back whole.
#
# The point is not to repair anything — it is to find out, on a quiet day,
# whether the file in .backups/ is actually a database. A dump nobody has ever
# restored is a guess, and it is the most expensive kind of guess to be wrong
# about.
#
# Usage:
#   scripts/restore-drill.sh                       # newest backup
#   scripts/restore-drill.sh .backups/regwatch-....sql.gz
set -euo pipefail

cd "$(dirname "$0")/.."

FILE="${1:-$(ls -1t .backups/regwatch-*.sql.gz 2>/dev/null | head -1)}"
if [[ -z "$FILE" || ! -f "$FILE" ]]; then
  echo "error: no backup found — run scripts/backup-db.sh first" >&2
  exit 1
fi

TABLES="matching_match watches_watch watches_client digests_digest gazette_act gazette_edition pipeline_runlog"
NAME="regwatch-restore-drill-$$"
PORT_GUESS=55432

cleanup() { docker rm -f "$NAME" >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "starting scratch postgres ..."
docker run --rm -d --name "$NAME" \
  -e POSTGRES_PASSWORD=throwaway -e POSTGRES_DB=regwatch \
  -p "$PORT_GUESS:5432" postgres:17 >/dev/null

for _ in $(seq 1 60); do
  if docker exec "$NAME" pg_isready -q -U postgres 2>/dev/null; then break; fi
  sleep 1
done
docker exec "$NAME" pg_isready -q -U postgres

echo "restoring $FILE ..."
# Errors about supabase_vault / auth / storage are expected: those schemas are
# Supabase's managed extras and do not exist in a plain postgres image. They
# have nothing to do with the application's own tables.
gunzip -c "$FILE" \
  | docker exec -i -e PGPASSWORD=throwaway "$NAME" \
      psql -q -U postgres -d regwatch -v ON_ERROR_STOP=0 >/dev/null 2>/tmp/restore-drill.err || true

echo
printf '%-22s %10s %10s   %s\n' TABLE DUMP RESTORED RESULT
failed=0
for t in $TABLES; do
  in_dump=$(gunzip -c "$FILE" \
    | awk -v t="^COPY public[.]$t " '$0 ~ t {f=1;next} f&&/^\\[.]$/{f=0} f' | wc -l)
  restored=$(docker exec -e PGPASSWORD=throwaway "$NAME" \
    psql -Atq -U postgres -d regwatch -c "select count(*) from public.$t" 2>/dev/null || echo ERR)
  if [[ "$in_dump" == "$restored" ]]; then
    printf '%-22s %10s %10s   ok\n' "$t" "$in_dump" "$restored"
  else
    printf '%-22s %10s %10s   MISMATCH\n' "$t" "$in_dump" "$restored"
    failed=1
  fi
done

echo
if [[ "$failed" -eq 0 ]]; then
  echo "restore drill PASSED — every table came back with the row count the dump carried"
else
  echo "restore drill FAILED — see the mismatches above; stderr in /tmp/restore-drill.err" >&2
  exit 1
fi
