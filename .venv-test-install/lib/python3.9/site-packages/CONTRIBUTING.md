# Contributing to ultrathink System

Thank you for your interest in contributing! This project is built on the ultrathink methodology—so naturally, we apply it to contributions too.

---

## How to Contribute

1. **Fork** the repository
2. **Create a branch**: `git checkout -b feature/your-feature-name`
3. **Apply ultrathink**: Use the 5-stage methodology for any non-trivial change
4. **Commit clearly**: Follow Conventional Commit standards
5. **Push and open a PR**: Describe your changes and the problem solved

---

## Development Guidelines

### Before Submitting
- [ ] Run `./verify-package.sh` — all checks must pass
- [ ] New skills follow the SKILL.md architecture standard (< 500 lines, YAML frontmatter)
- [ ] Scripts include docstrings and error handling
- [ ] Templates include usage comments
- [ ] Add or update tests for any new functionality

### Commit Message Format
```
type(scope): short description

Longer explanation if needed.

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
- Expanding SKILL.md beyond 500 lines (use references/ instead)
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
