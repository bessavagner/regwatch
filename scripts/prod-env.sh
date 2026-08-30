# Source this FROM THE REPO ROOT to load .env for a management command that
# should talk to production:
#
#   source scripts/prod-env.sh && uv run python manage.py <command>
#
# Set REGWATCH_ENV_FILE to point somewhere else.
#
# Parsed line by line rather than `source`d: the file holds real credentials,
# and at least one value contains a space, which the shell would try to run as
# a command. Nothing here is echoed.
while IFS='=' read -r _k _v; do
  case "$_k" in
    ''|\#*) continue ;;
  esac
  case "$_k" in
    [A-Z_]*) ;;
    *) continue ;;
  esac
  _v="${_v%\"}"; _v="${_v#\"}"
  _v="${_v%\'}"; _v="${_v#\'}"
  export "$_k=$_v"
done < "${REGWATCH_ENV_FILE:-.env}"
unset _k _v

# Fail loudly rather than falling back to the local database: a management
# command aimed at production that quietly hits localhost is worse than one
# that refuses to start.
if [ -z "${SUPABASE_DB_URL:-}${DATABASE_URL:-}" ]; then
  echo "error: no SUPABASE_DB_URL loaded — run this from the repo root, or set REGWATCH_ENV_FILE" >&2
  return 1 2>/dev/null || exit 1
fi

# manage.py defaults to config.settings, which needs a key even for a batch
# command that serves no HTTP. Never used to sign anything here.
export DJANGO_SETTINGS_MODULE="${DJANGO_SETTINGS_MODULE:-config.settings}"
export SECRET_KEY="${SECRET_KEY:-local-batch-only-not-a-signing-key}"
