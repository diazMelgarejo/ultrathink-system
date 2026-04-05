#!/usr/bin/env bash
# install-single-agent.sh
# ultrathink System — Single-Agent + ECC/Codex Harness Installer
# Installs to ALL correct runtime paths so every harness finds the skill.
set -euo pipefail

GREEN='\033[0;32m'; YELLOW='\033[1;33m'; BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'
ok()   { echo -e "  ${GREEN}✓${RESET} $1"; }
warn() { echo -e "  ${YELLOW}⚠${RESET}  $1"; }
info() { echo -e "  ${BLUE}→${RESET} $1"; }

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_SRC="$REPO_ROOT/single_agent"

echo -e "${BOLD}🚀 ultrathink System — Harness Install${RESET}"
echo "============================================"
echo ""

# ── 1. ~/.claude/skills/  (Claude Code global — all projects) ─────────────────
GLOBAL="$HOME/.claude/skills/ultrathink-system-skill"
mkdir -p "$GLOBAL"
cp    "$SKILL_SRC/SKILL.md"       "$GLOBAL/"
cp -r "$SKILL_SRC/cidf"           "$GLOBAL/"
cp -r "$SKILL_SRC/references"     "$GLOBAL/"
cp -r "$SKILL_SRC/scripts"        "$GLOBAL/"
cp -r "$SKILL_SRC/templates"      "$GLOBAL/"
chmod +x "$GLOBAL/scripts/"*.py "$GLOBAL/scripts/"*.sh 2>/dev/null || true
ok "~/.claude/skills/ultrathink-system-skill/    (Claude Code global)"

# ── 2. .claude/skills/ already committed in repo (project-level auto-load) ────
ok ".claude/skills/ultrathink-system-skill/         (committed, project-level)"

# ── 3. .agents/skills/ already committed in repo (Codex/OpenCode auto-load) ───
ok ".agents/skills/ultrathink-system-skill/          (committed, Codex/OpenCode)"

# ── 4. ECC harness — .ecc/skills/ if clone exists ─────────────────────────────
for ECC_CANDIDATE in "$REPO_ROOT/.ecc" "$HOME/.ecc" ".ecc"; do
  if [ -d "$ECC_CANDIDATE" ]; then
    ECC_SKILLS="$ECC_CANDIDATE/skills/ultrathink-system-skill"
    mkdir -p "$ECC_SKILLS"
    cp    "$SKILL_SRC/SKILL.md"   "$ECC_SKILLS/"
    cp -r "$SKILL_SRC/cidf"       "$ECC_SKILLS/"
    cp -r "$SKILL_SRC/references" "$ECC_SKILLS/"
    ok ".ecc/skills/ultrathink-system-skill/             (ECC harness)"
    break
  fi
done
if [ ! -d "${REPO_ROOT}/.ecc" ] && [ ! -d "$HOME/.ecc" ] && [ ! -d ".ecc" ]; then
  warn ".ecc/ not found — skip ECC install. Run after:"
  echo "        git clone https://github.com/affaan-m/everything-claude-code .ecc"
fi

# ── 5. ~/.ultrathink/tasks/ template bootstrap ────────────────────────────────
mkdir -p "$HOME/.ultrathink/tasks"
cp "$SKILL_SRC/templates/"* "$HOME/.ultrathink/tasks/" 2>/dev/null || true
ok "~/.ultrathink/tasks/                             (plan + lessons templates)"

echo ""
echo -e "${BOLD}✅ Installed.${RESET}  Runtime path summary:"
echo ""
echo "  Harness           Path"
echo "  ─────────────     ──────────────────────────────────────────────────"
echo "  Claude Code       ~/.claude/skills/ultrathink-system-skill/SKILL.md"
echo "  Claude Code       .claude/skills/ultrathink-system-skill/SKILL.md  (this repo)"
echo "  Codex / OpenCode  .agents/skills/ultrathink-system-skill/SKILL.md  (this repo)"
echo "  ECC / .ecc        .ecc/skills/ultrathink-system-skill/SKILL.md"
echo "  Multi-agent       .claude/agents/ultrathink-*.md                   (this repo)"
echo ""
echo -e "  ${BLUE}Trigger:${RESET} 'ultrathink this' | 'Apply ultrathink system to: [task]'"
