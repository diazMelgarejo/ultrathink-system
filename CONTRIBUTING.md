# Contributing to orama-system

Thank you for your interest in contributing. This project is built on the orama/ultrathink methodology, so non-trivial contributions must preserve deliberate planning, verification, and auditability. Apply the same standard to contribution work: plan visibly, keep scope narrow, verify before commit, and leave links for the next human or agent who will work on this.

---

## How to Contribute

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Apply ultrathink**: Use the [root skill contract](SKILL.md), the [packaged skill entrypoint](bin/skills/SKILL.md), and the [5-stage methodology](bin/skills/references/ultrathink-5-stages.md) for any non-trivial change
4. **Commit clearly**: Follow Conventional Commit standards
5. **Push and open a PR**: Describe your changes and the problem solved

---

## Agent Reference Map

Use this map to load only the context needed for the current task.

- **Methodology**: Start with [SKILL.md](SKILL.md), [bin/skills/SKILL.md](bin/skills/SKILL.md), [ultrathink-5-stages.md](bin/skills/references/ultrathink-5-stages.md), and [core-operational-directives.md](bin/skills/references/core-operational-directives.md).
- **Skill authoring**: For skill edits, read [content-insertion-framework.md](bin/skills/references/content-insertion-framework.md) and [skill-architecture-guide.md](bin/skills/references/skill-architecture-guide.md) before expanding any `SKILL.md`.
- **Multi-agent coordination**: For parallel work, scope ownership, and handoffs, use [06-multi-agent-collab.md](docs/wiki/06-multi-agent-collab.md) and [08-git-hygiene-and-branching.md](docs/wiki/08-git-hygiene-and-branching.md).
- **Recovery and salvage work**: For history-repair branches, read [history recovery](docs/recovery/2026-04-24-001-orama-history-recovery.md), the [commit salvage matrix](docs/recovery/2026-04-24-002-commit-salvage-matrix.md), and [git safety guardrails](docs/recovery/2026-04-24-003-git-safety-guardrails.md) before running risky Git commands.
- **Verification and lessons**: Before final handoff, consult [LESSONS.md](docs/LESSONS.md), the [wiki index](docs/wiki/README.md), [tests/README.md](tests/README.md), and the [verification checklist template](bin/skills/templates/verification-checklist.md).

---

## Development Guidelines

### Before Submitting

- [ ] Keep `.env`, `.env.local`, and `.paths` untracked; update examples instead
- [ ] Run `./verify-package.sh` — all checks must pass
- [ ] New skills follow the SKILL.md architecture standard (< 200 lines, YAML frontmatter)
- [ ] Old skills should upgrade to SKILL.md architecture standard (< 500 lines, YAML frontmatter, offload to references/ and/or sub-skills/)
- [ ] Scripts include docstrings and error handling
- [ ] Templates include usage comments
- [ ] Add or update tests for any new functionality

### History Recovery Only

- Use salvage branch names such as `yyyy-mm-dd-001-brief-summary`; see [git hygiene and branching](docs/wiki/08-git-hygiene-and-branching.md).
- Confirm Git identity with `bash scripts/git/check_identity.sh` before committing.
- Preserve dirty work before risky Git operations with `git stash push --include-untracked`.
- Prefer manual salvage of reviewed intent over replaying tainted commit ranges; use the [commit salvage matrix](docs/recovery/2026-04-24-002-commit-salvage-matrix.md).

### Commit Message Format

```ascii
type(scope): short description

Longer explanation if needed.

Why:
- rationale and affected component

Risk:
- compatibility or migration concerns

Verification:
- exact commands run

Closes #issue-number
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Code Style

- Python: PEP 8, type hints preferred
- Bash: `set -e`, quote variables, include usage comments
- Markdown: Headers use ATX style (`##`), code blocks specify language

---

## What to Contribute

### High-Value Contributions

- **New reference documents**: Deep dives on methodology aspects
- **Additional agent skills**: Specialized agents for niche domains
- **Example projects**: Real-world usage walkthroughs
- **Lessons learned**: Anonymized patterns from real usage
- **Bug fixes**: Especially in scripts and tooling

### Please Avoid

- Expanding existing `SKILL.md` files beyond 500 lines. New skill entrypoints should stay near 200 lines and offload context to `references/` or sub-skills.
- Hardcoded paths or environment-specific assumptions
- Removing the Apache 2.0 license headers

---

## Code of Conduct

- Be respectful and constructive
- Give credit where credit is due
- Assume good faith in others' contributions
- Follow the Apache 2.0 license terms

---

## Questions?

Open an issue or start a Discussion on GitHub.

*"Elegant contributions only. If it feels hacky, refine it."*
