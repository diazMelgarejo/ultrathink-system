#!/usr/bin/env bash
# verify-package.sh — ultrathink System package integrity check
set -euo pipefail

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; BOLD='\033[1m'; RESET='\033[0m'
errors=0

chk_f() { [ -f "$1" ] && echo -e "  ${GREEN}✓${RESET} $1" || { echo -e "  ${RED}✗${RESET} $1 MISSING"; ((errors++)); }; }
chk_d() { [ -d "$1" ] && echo -e "  ${GREEN}✓${RESET} $1/" || { echo -e "  ${RED}✗${RESET} $1/ MISSING"; ((errors++)); }; }

echo -e "${BOLD}🔍 ultrathink System — Package Integrity Check${RESET}\n"

echo "📄 Root:";    chk_f LICENSE; chk_f README.md; chk_f CONTRIBUTING.md; chk_f CHANGELOG.md
chk_f install-single-agent.sh; chk_f install-multi-agent.sh; chk_f verify-package.sh

echo -e "\n📦 Single-agent:"; chk_f single_agent/SKILL.md; chk_f single_agent/README.md
chk_d single_agent/references; chk_d single_agent/scripts; chk_d single_agent/templates
chk_f single_agent/references/ultrathink-5-stages.md
chk_f single_agent/references/core-operational-directives.md
chk_f single_agent/references/content-insertion-framework.md
chk_f single_agent/references/skill-architecture-guide.md
chk_f single_agent/scripts/verify_before_done.py
chk_f single_agent/scripts/capture_lesson.py
chk_f single_agent/scripts/create_task_plan.sh
chk_f single_agent/templates/task-plan.md
chk_f single_agent/templates/lessons-log.md
chk_f single_agent/templates/verification-checklist.md

echo -e "\n🤖 Multi-agent:"; chk_d multi_agent/agents
for a in orchestrator context architect refiner executor verifier crystallizer; do
  chk_d "multi_agent/agents/$a"
done
chk_f multi_agent/shared/ultrathink_core.py
chk_f multi_agent/shared/state_manager.py
chk_f multi_agent/shared/message_bus.py
chk_f multi_agent/config/agent_registry.json
chk_f multi_agent/config/routing_rules.json
chk_f multi_agent/mcp_servers/ultrathink_orchestration_server.py
chk_f multi_agent/mcp_servers/agent_communication_server.py

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

echo -e "\n🔧 CIDF Package:"
chk_f single_agent/cidf/README.md
chk_f single_agent/cidf/FRAMEWORK.md
chk_f single_agent/cidf/core/content_insertion_framework.py
chk_f single_agent/cidf/core/content_insertion_policy.json
chk_f single_agent/cidf/core/contentInsertionFramework.ts
chk_f single_agent/cidf/linter/policy_linter.py
chk_f single_agent/cidf/linter/policyLinter.ts
chk_f single_agent/cidf/tests/test_conformance.py
chk_f single_agent/cidf/tests/conformance.test.ts
