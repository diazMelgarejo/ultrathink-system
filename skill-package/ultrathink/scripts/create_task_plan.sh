#!/usr/bin/env bash
# create_task_plan.sh
# ====================
# ultrathink System — Directive #1: Plan Node Default
#
# Generates a structured tasks/todo.md plan template for a new task.
# Run BEFORE starting any implementation with 3+ steps.
#
# Usage:
#   ./create_task_plan.sh "Task Name"
#   ./create_task_plan.sh "Build auth system" --optimize reliability
#   ./create_task_plan.sh --interactive
#
# Philosophy:
#   Most failures come from rushing into implementation.
#   Write the plan first. Verify with user. Then build.

set -euo pipefail

# ─── Colours ──────────────────────────────────────────────────────────────────
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

# ─── Defaults ─────────────────────────────────────────────────────────────────
TASK_NAME=""
OPTIMIZE_FOR="reliability"
INTERACTIVE=false
TASKS_DIR="./tasks"
DATE=$(date +"%Y-%m-%d")
TIME=$(date +"%H:%M")

# ─── Argument parsing ─────────────────────────────────────────────────────────
while [[ $# -gt 0 ]]; do
  case $1 in
    --optimize)   OPTIMIZE_FOR="$2"; shift 2 ;;
    --dir)        TASKS_DIR="$2/tasks"; shift 2 ;;
    --interactive|-i) INTERACTIVE=true; shift ;;
    --help|-h)
      echo "Usage: $0 \"Task Name\" [--optimize reliability|creativity|speed] [--dir DIR]"
      exit 0 ;;
    *)
      if [[ -z "$TASK_NAME" ]]; then
        TASK_NAME="$1"
      fi
      shift ;;
  esac
done

# ─── Interactive mode ─────────────────────────────────────────────────────────
if [[ "$INTERACTIVE" == true ]] || [[ -z "$TASK_NAME" ]]; then
  echo ""
  echo -e "${BOLD}ultrathink Plan Node — Create Task Plan${RESET}"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  read -rp "$(echo -e "  ${BLUE}Task name${RESET}: ")" TASK_NAME
  read -rp "$(echo -e "  ${BLUE}Optimize for${RESET} [reliability/creativity/speed]: ")" OPT
  [[ -n "$OPT" ]] && OPTIMIZE_FOR="$OPT"
  read -rp "$(echo -e "  ${BLUE}Goal${RESET} (1 sentence): ")" GOAL
  read -rp "$(echo -e "  ${BLUE}Key constraints${RESET} (comma-separated): ")" CONSTRAINTS
  read -rp "$(echo -e "  ${BLUE}Non-goals${RESET} (what we're NOT doing): ")" NON_GOALS
else
  GOAL="[Describe what success looks like in 1-2 sentences]"
  CONSTRAINTS="[List technical, business, compliance constraints]"
  NON_GOALS="[List explicitly out-of-scope items]"
fi

# ─── Sanitise task name for filename ─────────────────────────────────────────
TASK_SLUG=$(echo "$TASK_NAME" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]/-/g' | sed 's/--*/-/g' | sed 's/^-\|-$//g')

# ─── Create tasks directory ───────────────────────────────────────────────────
mkdir -p "$TASKS_DIR/archive"

TODO_FILE="$TASKS_DIR/todo.md"
LESSONS_FILE="$TASKS_DIR/lessons.md"

# ─── Write plan ───────────────────────────────────────────────────────────────
cat > "$TODO_FILE" << PLAN
# Task: ${TASK_NAME}
**Created**: ${DATE} ${TIME}
**Optimize for**: ${OPTIMIZE_FOR}
**Status**: 🔄 In Progress

---

## Goal
${GOAL}

---

## Constraints
${CONSTRAINTS}

## Non-Goals
${NON_GOALS}

---

## ✓ Plan First

> Review this plan before starting implementation.

### Phase 1: Context Immersion (Stage 1)
- [ ] Scan project structure and git history
- [ ] Review CLAUDE.md / AGENTS.md / SKILL.md files
- [ ] Identify existing patterns and idioms
- [ ] Summarize constraints and key decisions

### Phase 2: Visionary Architecture (Stage 2)
- [ ] Design modular breakdown (what are the components?)
- [ ] Define interfaces between components
- [ ] Sketch data flows
- [ ] Identify edge cases upfront

### Phase 3: Ruthless Refinement (Stage 3)
- [ ] Apply quality rubric (simplicity, readability, robustness)
- [ ] Eliminate redundancy and unnecessary abstractions
- [ ] Confirm elegance: "Is there a simpler way?"

### Phase 4: Implementation (Stage 4)
- [ ] Step 1: [Describe first implementation step]
- [ ] Step 2: [Describe second implementation step]
- [ ] Step 3: [Describe third implementation step]
- [ ] Step 4: Write / run tests for each component
- [ ] Step 5: Integration testing end-to-end
- [ ] Step 6: Address edge cases and error handling

### Phase 5: Verification (Directive #4)
- [ ] Run full test suite (no failures)
- [ ] Check for debug artifacts (no print/console.log)
- [ ] Linting passes
- [ ] Staff engineer self-review completed
- [ ] Run: \`python scripts/verify_before_done.py --task "${TASK_NAME}"\`

---

## ✓ Verify Plan

> [ ] User / team reviewed and approved this plan on: ___________

---

## ✓ Track Progress

Mark items above complete as you go with \`[x]\`.

**Progress log** (add entries as you work):
- ${DATE}: Plan created

---

## ✓ Document Results

> Complete this section when the task is done.

### What Was Built
[Describe what was implemented]

### Key Decisions Made
[List significant architectural or implementation choices]

### Tests
- [ ] Unit tests: [number] passing
- [ ] Integration tests: [number] passing
- [ ] Coverage: [%]

### Performance
[Any metrics or benchmarks]

---

## ✓ Capture Lessons

> If any corrections were needed, run:
> \`python scripts/capture_lesson.py\`

Lessons captured: [list pattern names here, or "none needed"]

---

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|-----------|
| [Risk 1] | Low/Med/High | Low/Med/High | [How to handle] |

---

*Generated by ultrathink create_task_plan.sh on ${DATE}*
PLAN

# ─── Bootstrap lessons.md if it doesn't exist ────────────────────────────────
if [[ ! -f "$LESSONS_FILE" ]]; then
  cat > "$LESSONS_FILE" << LESSONS
# Lessons Learned — Self-Improvement Log
**ultrathink System — Directive #3**

This file is the institutional memory of this project.
Review at the start of each session.
Add entries with: \`python scripts/capture_lesson.py\`

---

LESSONS
  echo -e "  ${GREEN}✓${RESET} Created ${LESSONS_FILE}"
fi

# ─── Done ─────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}✅ Task plan created${RESET}"
echo -e "   ${GREEN}→${RESET} ${TODO_FILE}"
echo ""
echo -e "  ${CYAN}Next steps:${RESET}"
echo -e "  1. Fill in the implementation steps in Phase 4"
echo -e "  2. Review with user/team before starting"
echo -e "  3. Mark items complete as you go"
echo -e "  4. Run verification before marking done:"
echo -e "     ${BLUE}python scripts/verify_before_done.py --task \"${TASK_NAME}\"${RESET}"
echo ""
