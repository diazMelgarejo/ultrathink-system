#!/usr/bin/env bash
# Imports Perpetua-Tools instincts → ultrathink-system on every session start.
# Idempotent. Local-first; clones companion repo if absent.

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PARENT_DIR="$(dirname "$REPO_ROOT")"

# 1. Find instinct-cli.py
INSTINCT_CLI=""
for p in \
  "$REPO_ROOT/.ecc/skills/continuous-learning-v2/scripts/instinct-cli.py" \
  "${CLAUDE_PLUGIN_ROOT:-}/skills/continuous-learning-v2/scripts/instinct-cli.py"; do
  [[ -f "$p" ]] && { INSTINCT_CLI="$p"; break; }
done
[[ -z "$INSTINCT_CLI" ]] && exit 0

# 2. Find or clone Perpetua-Tools
PT_REPO=""
for p in "$PARENT_DIR/Perpetua-Tools" "$PARENT_DIR/perplexity-api/Perpetua-Tools"; do
  [[ -d "$p/.claude" ]] && { PT_REPO="$p"; break; }
done

if [[ -z "$PT_REPO" ]]; then
  git clone --depth 1 https://github.com/diazMelgarejo/Perpetua-Tools \
    "$PARENT_DIR/Perpetua-Tools" 2>/dev/null || exit 0
  PT_REPO="$PARENT_DIR/Perpetua-Tools"
fi

# 3. Import
YAML="$PT_REPO/.claude/homunculus/instincts/inherited/Perpetua-Tools-instincts.yaml"
[[ -f "$YAML" ]] || exit 0
python3 "$INSTINCT_CLI" import "$YAML" --force
