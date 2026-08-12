# Shared helpers for reading deploy/secrets.list.
# Source this, don't execute it:  . "$(dirname "$0")/secrets-lib.sh"

# Absolute path to the list, resolved relative to this file so callers can be
# run from any working directory (CI runs from the repo root, provision.sh is
# often run from deploy/).
SECRETS_LIST="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/secrets.list"

# secret_names — one name per line, comments and blank lines stripped.
secret_names() {
  sed -e 's/#.*//' -e 's/[[:space:]]//g' "$SECRETS_LIST" | grep -v '^$'
}

# secret_flags — the NAME=NAME:latest,... value for --set-secrets.
secret_flags() {
  secret_names | sed 's/.*/&=&:latest/' | paste -sd, -
}
