# Troubleshooting

## Skill Not Activating

**Symptom**: "ultrathink this" does nothing different.
**Solutions**:
1. Verify installation: `ls ~/.claude/skills/ultrathink-system-skill/SKILL.md`
2. Check YAML frontmatter: no tabs, no trailing spaces on `---` lines
3. Use explicit trigger: "Apply the ultrathink system to: [your task]"
4. Check Claude version supports Skills (Claude Code, Cowork, or compatible platform)

---

## verify_before_done.py Fails to Find Tests

**Symptom**: "No test runner detected"
**Solutions**:
1. Create `pytest.ini` or add `[tool.pytest.ini_options]` to `pyproject.toml`
2. Install pytest: `pip install pytest`
3. From the repository root, use `python single_agent/scripts/verify_before_done.py --no-interact`
4. From the installed skill directory, use `python scripts/verify_before_done.py --no-interact`

---

## Context Window Overflow

**Symptom**: Claude loses track of earlier context.
**Solutions**:
1. Use Directive #2 (Subagent Strategy) — offload research to subagents
2. For multi_agent mode: use the orchestration server to distribute work
3. Break large tasks into smaller sub-tasks, each with their own `todo.md`

---

## Multi-Agent MCP Server Won't Start

**Symptom**: `python ultrathink_orchestration_server.py` errors on import
**Solutions**:
1. Ensure you're running from `multi_agent/mcp_servers/` directory (or set PYTHONPATH)
2. Check Python 3.8+: `python --version`
3. Install optional deps: `pip install redis` (only needed for Redis backend)
4. Fallback: the server runs with in-memory backend automatically

---

## Lessons File Not Found

**Symptom**: `capture_lesson.py` can't find `tasks/lessons.md`
**Solutions**:
1. From the repository root, run `./single_agent/scripts/create_task_plan.sh "Task"` first
2. Or: `mkdir -p tasks && touch tasks/lessons.md`
3. From the installed skill directory, run `./scripts/create_task_plan.sh "Task"`
4. Use `--dir /path/to/project` flag to specify project directory
