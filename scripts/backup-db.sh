#!/usr/bin/env bash
# Take a local logical backup of the RegWatch production database.
#
# Why this exists: the Supabase project is on the Free plan, which has neither
# Point-in-Time Recovery nor automated daily backups. Until that changes, a
# dump on this machine is the only copy of anything that cannot be regenerated
# — above all the human triage labels on matching_match.state.
#
# This is NOT equivalent to PITR. It captures the database as of the moment it
# runs, so the most you can ever lose is everything since the last run. Run it
# before anything destructive, and on any day you spend time triaging.
#
# Usage:
#   scripts/backup-db.sh            # dump to .backups/, keep the last 10
#   KEEP=30 scripts/backup-db.sh    # keep the last 30 instead
set -euo pipefail

cd "$(dirname "$0")/.."
KEEP="${KEEP:-10}"
OUT_DIR=".backups"

# Read the one key we need rather than sourcing .env: the file holds real
# credentials, some containing characters the shell would try to execute.
env_value() {
  [[ -f .env ]] || return 0
  sed -n "s/^$1=//p" .env | head -1 | sed -e 's/^"\(.*\)"$/\1/' -e "s/^'\(.*\)'\$/\1/"
}

DB_URL="${DATABASE_URL:-${SUPABASE_DB_URL:-}}"
[[ -n "$DB_URL" ]] || DB_URL="$(env_value DATABASE_URL)"
[[ -n "$DB_URL" ]] || DB_URL="$(env_value SUPABASE_DB_URL)"
if [[ -z "$DB_URL" ]]; then
  echo "error: neither DATABASE_URL nor SUPABASE_DB_URL is set (looked in .env)" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"
STAMP="$(date +%Y-%m-%dT%H-%M-%S)"
FILE="$OUT_DIR/regwatch-$STAMP.sql.gz"

# The URL in .env carries a password with characters libpq will not accept
# unencoded (a space, among others). Split it into parts here and hand the
# password over as PGPASSWORD, so the credential never has to survive a round
# trip through URL escaping — and never appears in a command line, where it
# would be visible to `ps` and to any error message pg_dump prints.
eval "$(
  DB_URL="$DB_URL" python3 - <<'PYEOF'
import os, shlex
from urllib.parse import urlsplit, unquote
u = urlsplit(os.environ["DB_URL"])
parts = {
    "PGHOST": u.hostname or "",
    "PGPORT": str(u.port or 5432),
    "PGUSER": unquote(u.username or ""),
    "PGPASSWORD": unquote(u.password or ""),
    "PGDATABASE": (u.path or "/postgres").lstrip("/") or "postgres",
}
for k, v in parts.items():
    print(f"export {k}={shlex.quote(v)}")
PYEOF
)"

# The host's pg_dump is version 16 and cannot read the Postgres 17 server that
# Supabase runs, so the dump goes through a matching container instead.
echo "dumping to $FILE ..."
docker run --rm -i \
  -e PGHOST -e PGPORT -e PGUSER -e PGPASSWORD -e PGDATABASE \
  postgres:17 \
  pg_dump --no-owner --no-privileges --clean --if-exists \
  | gzip > "$FILE"

if [[ ! -s "$FILE" ]]; then
  echo "error: dump is empty — removing $FILE" >&2
  rm -f "$FILE"
  exit 1
fi

# A dump that restores nothing is worse than no dump, because it is trusted.
# Prove the tables that carry irreplaceable data are actually in the file.
echo "verifying ..."
# grep -c, not grep -q: under `set -o pipefail` a short-circuiting grep leaves
# gunzip killed by SIGPIPE, and the whole pipeline reports failure for a table
# that is actually present.
for table in matching_match watches_watch watches_client digests_digest; do
  found=$(gunzip -c "$FILE" | grep -c "^COPY public\.$table " || true)
  if [[ "$found" -eq 0 ]]; then
    echo "error: $table missing from the dump — removing $FILE" >&2
    rm -f "$FILE"
    exit 1
  fi
done

ROWS=$(gunzip -c "$FILE" | awk '/^COPY public\.matching_match /{f=1;next} f&&/^\\[.]$/{f=0} f' | wc -l)
echo "ok: $(du -h "$FILE" | cut -f1), $ROWS rows in matching_match"

# Keep the newest $KEEP, drop the rest.
ls -1t "$OUT_DIR"/regwatch-*.sql.gz 2>/dev/null | tail -n "+$((KEEP + 1))" | while read -r old; do
  echo "pruning $old"
  rm -f "$old"
done
