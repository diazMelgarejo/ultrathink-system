#!/usr/bin/env bash
#
# apply-openrouter-free-defaults.sh
#
# Idempotently applies the OpenRouter free-model policy from
# deployments/macbook-pro-head/openclaw/openclaw.model-policy.jsonc to
# OpenClaw configs:
#   --apply-live    → patch ~/.openclaw/openclaw.json
#   --repo-only     → patch repo template files only
#   --config-only   → skip the OPENROUTER_API_KEY check
#
# Preserves: gateway, WhatsApp bindings, wrapper exec, sandbox, cron, tool profiles.
# Patches only: env.OPENROUTER_API_KEY, agents.defaults.model, agents.defaults.models,
#               and per-agent model overrides.
#
# Source spec: OpenClaw/v1/OpenRouter.md §8
# Adopted into: orama-system/bin/orama-system/mcp-orchestration/SKILL.md §2 Rule 1

set -euo pipefail

# ─── Defaults ─────────────────────────────────────────────────────────────────
REPO_ROOT="${REPO_ROOT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
LIVE_CONFIG="${HOME}/.openclaw/openclaw.json"
POLICY_FILE="${REPO_ROOT}/deployments/macbook-pro-head/openclaw/openclaw.model-policy.jsonc"
APPLY_LIVE=0
REPO_ONLY=0
CONFIG_ONLY=0
NO_AGENT_OVERRIDES=0
DRY_RUN=0

# Repo templates to patch (always present in orama-system tree)
REPO_TEMPLATES=()

# Companion repo templates (only patch if found)
COMPANION_TEMPLATES=(
  "${HOME}/Documents/Terminal xCode/claude/OpenClaw/alphaclaw-observability/config/openclaw.json"
  "${HOME}/Documents/Terminal xCode/claude/OpenClaw/AlphaClaw/lib/onboarding/defaults/openclaw.json.template"
)

# ─── Arg parsing ──────────────────────────────────────────────────────────────
FORCE_PRIMARY=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --apply-live)          APPLY_LIVE=1; shift ;;
    --repo-only)           REPO_ONLY=1; shift ;;
    --config-only)         CONFIG_ONLY=1; shift ;;
    --no-agent-overrides)  NO_AGENT_OVERRIDES=1; shift ;;
    --dry-run)             DRY_RUN=1; shift ;;
    --force-primary)       FORCE_PRIMARY=1; shift ;;
    --live-config)         LIVE_CONFIG="$2"; shift 2 ;;
    --policy)              POLICY_FILE="$2"; shift 2 ;;
    -h|--help)
      sed -n '2,18p' "$0"
      exit 0
      ;;
    *)
      echo "ERROR: unknown arg: $1" >&2
      exit 2
      ;;
  esac
done
export FORCE_PRIMARY

# ─── Preflight ────────────────────────────────────────────────────────────────
if [[ "$CONFIG_ONLY" -eq 0 ]]; then
  if [[ -z "${OPENROUTER_API_KEY:-}" ]]; then
    echo "ERROR: OPENROUTER_API_KEY is not set in env." >&2
    echo "       Either export it or pass --config-only to skip the check." >&2
    exit 2
  fi
fi

if [[ ! -f "$POLICY_FILE" ]]; then
  echo "ERROR: policy file not found: $POLICY_FILE" >&2
  exit 2
fi

if ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required. Install: brew install jq" >&2
  exit 2
fi

# ─── Helpers ──────────────────────────────────────────────────────────────────
strip_jsonc() {
  # Strip // line comments from a JSONC file to make it valid JSON for jq.
  # - Full-line comments (whitespace + //...) → removed entirely
  # - Inline comments (// after data) → stripped, but URL schemes like
  #   `https://` are preserved (the `[^:]` lookbehind prevents stripping
  #   `//` that follows a colon).
  sed -E 's|([^:])//[^\n]*$|\1|; s|^[[:space:]]*//.*$||' "$1"
}

backup_file() {
  local f="$1"
  if [[ -f "$f" ]]; then
    local ts; ts="$(date -u +%Y%m%dT%H%M%SZ)"
    cp -p "$f" "${f}.bak.${ts}"
    echo "  backup → ${f}.bak.${ts}"
  fi
}

merge_policy_into() {
  local target="$1"
  local policy_json; policy_json="$(strip_jsonc "$POLICY_FILE")"

  if [[ ! -f "$target" ]]; then
    echo "  SKIP: $target (does not exist; not creating)"
    return 0
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "  DRY-RUN: would patch $target"
    return 0
  fi

  backup_file "$target"

  # Smart merge (fallback-only by default — preserves existing primary):
  #   .env.OPENROUTER_API_KEY                  ← set from env if not already set
  #   .agents.defaults.model.primary           ← PRESERVED (unless --force-primary)
  #   .agents.defaults.model.fallbacks         ← APPEND policy fallbacks_to_merge (dedup)
  #   .agents.defaults.models                  ← MERGE in policy models_to_merge
  #
  # CLAUDE.md hard requirement: Mac primary is ollama/qwen3.5:9b-nvfp4,
  # Win primary is lmstudio-win/<distilled>. This script preserves whatever
  # the host already chose. To force a specific primary, pass --force-primary
  # (and set the policy's primary explicitly).
  local tmp tmp2
  tmp="$(mktemp)"
  tmp2=""
  trap 'rm -f "${tmp:-}" "${tmp2:-}"' EXIT
  jq -n \
    --slurpfile target "$target" \
    --argjson policy "$policy_json" \
    --arg apiKey "${OPENROUTER_API_KEY:-}" \
    --arg forcePrimary "${FORCE_PRIMARY:-0}" \
    --arg noOverrides "$NO_AGENT_OVERRIDES" '
      .target = $target[0] | .policy = $policy |
      .target
      # 1. env.OPENROUTER_API_KEY — set only if not already present (literal value)
      | (.env //= {})
      | if (.env.OPENROUTER_API_KEY // "") == "" and $apiKey != ""
          then .env.OPENROUTER_API_KEY = $apiKey
          else . end
      # 2. agents.defaults.model — preserve primary, merge fallbacks
      # Strategy: REMOVE any Gemini entries from existing fallbacks (they go to end
      # per Gemini-Analyzer use-case routing), then concat policy fallbacks (which
      # already has Gemini at the end), then dedup preserving first-occurrence order.
      | (.agents //= {}) | (.agents.defaults //= {}) | (.agents.defaults.model //= {})
      | .agents.defaults.model.fallbacks = (
          (
            ((.agents.defaults.model.fallbacks // [])
             | map(select(. as $m | ($m | startswith("google/gemini") | not))))
            + ($policy.agents.defaults.model.fallbacks_to_merge // [])
          )
          | reduce .[] as $item ([]; if any(.[]; . == $item) then . else . + [$item] end)
        )
      # If --force-primary AND policy has a primary, replace it
      | if $forcePrimary == "1" and ($policy.agents.defaults.model.primary // "") != ""
          then .agents.defaults.model.primary = $policy.agents.defaults.model.primary
          else . end
      # 3. agents.defaults.models — merge allowlist
      | (.agents.defaults.models //= {})
      | .agents.defaults.models =
          (.agents.defaults.models * ($policy.agents.defaults.models_to_merge // {}))
    ' > "$tmp"

  # Secret-leak guard: if the target is a tracked template (not the live
  # config under ~/.openclaw/), re-write the OPENROUTER_API_KEY field back
  # to the literal placeholder so we never commit a resolved key to a repo.
  case "$target" in
    *"/.openclaw/openclaw.json")
      : # live config — keep the resolved key
      ;;
    *)
      tmp2="$(mktemp)"
      jq --arg ph '${OPENROUTER_API_KEY}' \
        '.env.OPENROUTER_API_KEY = $ph' "$tmp" > "$tmp2" && mv "$tmp2" "$tmp"
      tmp2=""
      ;;
  esac

  # Validate result parses
  if ! jq empty "$tmp" 2>/dev/null; then
    echo "  ERROR: produced invalid JSON; restoring backup." >&2
    rm -f "$tmp"
    exit 3
  fi

  mv "$tmp" "$target"
  echo "  patched ✓ (primary preserved, OpenRouter fallbacks merged)"
}

# ─── Main ─────────────────────────────────────────────────────────────────────
echo "== apply-openrouter-free-defaults =="
echo "Policy: $POLICY_FILE"
echo "Mode:   $([[ $APPLY_LIVE -eq 1 ]] && echo live)$([[ $REPO_ONLY -eq 1 ]] && echo repo-only)$([[ $DRY_RUN -eq 1 ]] && echo " (dry-run)")"
echo ""

# Companion templates (always attempted, idempotent)
for f in "${COMPANION_TEMPLATES[@]}"; do
  echo "→ companion template: $f"
  merge_policy_into "$f"
done

# Live config
if [[ "$APPLY_LIVE" -eq 1 && "$REPO_ONLY" -eq 0 ]]; then
  echo ""
  echo "→ live config: $LIVE_CONFIG"
  merge_policy_into "$LIVE_CONFIG"
fi

# Post-apply: openclaw models status
if command -v openclaw >/dev/null 2>&1; then
  echo ""
  echo "== openclaw models status =="
  openclaw models status || true
fi

echo ""
echo "Done."
echo "Next: scripts/verify-openrouter-models.sh"
