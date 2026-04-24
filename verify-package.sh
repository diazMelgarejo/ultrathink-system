#!/usr/bin/env bash
# verify-package.sh — The ὅραμα System package integrity check
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; RESET='\033[0m'
errors=0

chk_f() { [ -f "$1" ] && echo -e "  ${GREEN}✓${RESET} $1" || { echo -e "  ${RED}✗${RESET} $1 MISSING"; ((errors++)); }; }
chk_d() { [ -d "$1" ] && echo -e "  ${GREEN}✓${RESET} $1/" || { echo -e "  ${RED}✗${RESET} $1/ MISSING"; ((errors++)); }; }

echo -e "${BOLD}🔍 The ὅραμα System — Package Integrity Check${RESET}\n"

echo "📄 Root:";    chk_f LICENSE; chk_f README.md; chk_f CONTRIBUTING.md; chk_f CHANGELOG.md
chk_f install.sh; chk_f install-multi-agent.sh; chk_f verify-package.sh

echo -e "\n📦 Skills (bin/orama-system):"; chk_f bin/orama-system/SKILL.md; chk_f bin/orama-system/README.md
chk_d bin/orama-system/references; chk_d bin/orama-system/scripts; chk_d bin/orama-system/templates
chk_f bin/orama-system/references/ultrathink-5-stages.md
chk_f bin/orama-system/references/core-operational-directives.md
chk_f bin/orama-system/references/content-insertion-framework.md
chk_f bin/orama-system/references/skill-architecture-guide.md
chk_f bin/orama-system/scripts/verify_before_done.py
chk_f bin/orama-system/scripts/capture_lesson.py
chk_f bin/orama-system/scripts/create_task_plan.sh
chk_f bin/orama-system/templates/task-plan.md
chk_f bin/orama-system/templates/lessons-log.md
chk_f bin/orama-system/templates/verification-checklist.md

echo -e "\n🤖 Agents (bin/agents):"; chk_d bin/agents
for a in orchestrator context architect refiner executor verifier crystallizer; do
  chk_d "bin/agents/$a"
done
chk_f bin/shared/ultrathink_core.py
chk_f bin/shared/state_manager.py
chk_f bin/shared/message_bus.py
chk_f bin/config/agent_registry.json
chk_f bin/config/routing_rules.json
chk_f bin/mcp_servers/ultrathink_orchestration_server.py
chk_f bin/mcp_servers/agent_communication_server.py

echo -e "\n🔧 CIDF Package:"
chk_f bin/orama-system/cidf/README.md
chk_f bin/orama-system/cidf/FRAMEWORK.md
chk_f bin/orama-system/cidf/core/content_insertion_framework.py
chk_f bin/orama-system/cidf/core/content_insertion_policy.json
chk_f bin/orama-system/cidf/core/contentInsertionFramework.ts
chk_f bin/orama-system/cidf/linter/policy_linter.py
chk_f bin/orama-system/cidf/linter/policyLinter.ts
chk_f bin/orama-system/cidf/tests/test_conformance.py
chk_f bin/orama-system/cidf/tests/conformance.test.ts

echo -e "\n🔌 AFRP + API:"
chk_f bin/orama-system/afrp/SKILL.md
chk_f bin/orama-system/cidf/SKILL.md
chk_f api_server.py

echo -e "\n📚 Examples:"; chk_d examples/financial-validator; chk_d examples/api-integration; chk_d examples/architecture-refactor
echo -e "\n📖 Docs:";    chk_f docs/installation.md; chk_f docs/quick-start.md; chk_f docs/faq.md; chk_f docs/troubleshooting.md; chk_f docs/api-reference.md
echo -e "\n🧪 Tests:";   chk_f tests/test_single_agent.py; chk_f tests/test_multi_agent.py; chk_f tests/test_orchestrator.py

echo ""
if [ "$errors" -eq 0 ]; then
    echo -e "${GREEN}${BOLD}✅ Package integrity: VERIFIED — all files present${RESET}"
    exit 0
else
    echo -e "${RED}${BOLD}❌ Package integrity: FAILED — $errors file(s) missing${RESET}"
    exit 1
fi
