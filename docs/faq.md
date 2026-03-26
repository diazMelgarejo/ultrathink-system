# Frequently Asked Questions

## General

**Q: What's the difference between this and other agent skill packages?**
A: ultrathink is methodology-first, not tool-first. It encodes a complete problem-solving philosophy (5 stages + 6 directives) rather than just API wrappers. It's designed to compound improvement over time via the self-improvement loop.

**Q: Does this work with ECC Tools / everything-claude-code?**
A: Yes. Drop `single_agent/` into your ECC Tools skills directory. It follows the SKILL.md standard and works alongside the 65+ skills in the ECC catalog.

**Q: How is this different from just using Claude normally?**
A: Normal Claude is reactive. ultrathink makes Claude systematic: always plans first, always verifies programmatically, always captures lessons, always demands elegance. The "amplifier principle" — AI amplifies intent, and ultrathink gives that intent structure.

---

## Installation

**Q: Skill isn't activating. What's wrong?**
1. Check SKILL.md is in the correct directory
2. Validate YAML frontmatter syntax (no tab characters, consistent indentation)
3. For Team/Enterprise Claude: verify Skills are enabled org-wide
4. Try manual trigger: "Apply ultrathink system to: [task]"

**Q: Do I need Redis for the multi_agent system?**
A: No. The default in-memory backend works for development and single-machine setups. Redis is recommended for production distributed deployments.

---

## Usage

**Q: When should I use the single_agent vs multi_agent version?**
A: Single-agent for most tasks — it's faster and simpler. Multi-agent for large parallel tasks (refactoring many files, researching multiple approaches simultaneously, or when context window is a bottleneck).

**Q: How do I add my own lessons?**
A: From the repository root, run `python single_agent/scripts/capture_lesson.py`. From the installed skill directory, run `python scripts/capture_lesson.py`. Or open `tasks/lessons.md` directly and add an entry following the template in `templates/lessons-log.md`.

**Q: Can I customize the skill for my project?**
A: Yes! Add a `## Project-Specific Rules` section to `single_agent/SKILL.md`. Specify your stack, patterns, and constraints. The skill architecture standard supports this in its "Degrees of Freedom" section.

---

## Philosophy

**Q: Is this based on real research?**
A: Yes. The methodology draws from the "Amplifier Principle" (AI amplifies intent, not replaces judgment), DORA research on delivery performance, and the architectural optimization standard for SKILL.md files. See `docs/api-reference.md` for citations.

**Q: What does "self-improving" actually mean?**
A: After each mistake or correction, you run `capture_lesson.py`. Over time, `tasks/lessons.md` becomes a repository of prevention rules. At session start, reviewing it primes the agent (and you) to avoid known failure patterns. The mistake rate measurably declines.
