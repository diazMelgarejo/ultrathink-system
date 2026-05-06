#!/usr/bin/env bash
set -euo pipefail

# Accepted commit identities for this repo:
#   cyre  <Lawrence@cyre.me>     — human owner
#   Codex <codex@openai.com>     — Codex automated agent
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

actual_name="$(git -C "$REPO_ROOT" config user.name || true)"
actual_email="$(git -C "$REPO_ROOT" config user.email || true)"

echo "git user.name=${actual_name:-<unset>}"
echo "git user.email=${actual_email:-<unset>}"

# Check against all accepted identities
if [[ "$actual_name" == "cyre" && "$actual_email" == "Lawrence@cyre.me" ]]; then
  echo "OK: canonical git identity (cyre)"
elif [[ "$actual_name" == "Codex" && "$actual_email" == "codex@openai.com" ]]; then
  echo "OK: canonical git identity (Codex agent)"
else
  echo "ERROR: git identity must be one of:" >&2
  echo "  cyre  <Lawrence@cyre.me>" >&2
  echo "  Codex <codex@openai.com>" >&2
  echo "Got: ${actual_name:-<unset>} <${actual_email:-<unset>}>" >&2
  exit 1
fi
