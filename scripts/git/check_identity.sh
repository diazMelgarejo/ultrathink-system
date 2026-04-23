#!/usr/bin/env bash
set -euo pipefail

EXPECTED_NAME="cyre"
EXPECTED_EMAIL="Lawrence@cyre.me"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

actual_name="$(git -C "$REPO_ROOT" config user.name || true)"
actual_email="$(git -C "$REPO_ROOT" config user.email || true)"

echo "git user.name=${actual_name:-<unset>}"
echo "git user.email=${actual_email:-<unset>}"

if [[ "$actual_name" != "$EXPECTED_NAME" || "$actual_email" != "$EXPECTED_EMAIL" ]]; then
  echo "ERROR: git identity must be exactly: ${EXPECTED_NAME} <${EXPECTED_EMAIL}>" >&2
  exit 1
fi

echo "OK: canonical git identity"
