# 08. Git Hygiene and Branching — Orama Recovery Guardrails

**TL;DR:** Prevent future identity drift, broken config commits, and orphan branches by following dated branch names, stash-first discipline, explicit credential confirmation, and minimal workflow permissions.

---

## Branch Naming

All feature, fix, and recovery branches must use the dated monotonic format:

```text
yyyy-mm-dd-NNN-brief-summary
```

Examples:
- `2026-04-24-001-orama-salvage`
- `2026-04-25-001-fix-gateway-discovery`

Rules:
- Use the date the branch was created, not the anticipated merge date.
- Start at `001` and increment for same-day branches.
- Keep the summary lowercase and hyphenated.
- Never create a branch from a detached HEAD or another agent-created branch.

---

## Identity Confirmation

The only approved author identity for commits in the clean lineage is:

```text
cyre <Lawrence@cyre.me> or Codex <codex@openai.com>
```

Forbidden identity:

```text
Lawrence Melgarejo <Lawrence@bettermind.ph>
```

Before committing, run:

```bash
bash scripts/git/check_identity.sh
```

If this fails, do not commit. Correct your Git identity first:

```bash
git config user.name "cyre"
git config user.email "codex@openai.com"  # or Lawrence@cyre.me
```

---

## Stash-First Discipline

Before any risky Git operation (rebase, history inspection, branch surgery, cross-repo sync), capture state including untracked files:

```bash
git status --short --branch
git stash push --include-untracked -m "preserve work before <operation>"
git rev-parse --is-shallow-repository
git config user.name
git config user.email
```

Never run destructive cleanup until the stash has been verified.

---

## Commit Message Quality

Use detailed conventional commits. Every non-trivial commit must include:

```text
type(scope): short summary

Why:
- what was broken or risky

What changed:
- concrete files/components touched

Risk:
- known compatibility or migration concern

Verification:
- exact commands run
```

Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, `recovery`

---

## Private and Generated Config

- `.env` is private and ignored.
- `.env.local` is private and ignored.
- `.env.example` is the only tracked environment template.
- `.paths` is generated runtime-local state and ignored.
- `.paths.example` is the only tracked path template.
- Do not commit shell-substitution-only values as the sole configuration representation.

---

## GitHub Actions Permissions

Workflow permissions must be minimal and explicit.

- Release jobs need `contents: write`.
- PR automation needs `pull-requests: write`.
- Read-only CI should use default read behavior or an explicit read-only block.
- Avoid broad top-level write permissions.

---

## Related

- [Git Safety Guardrails](../recovery/2026-04-24-003-git-safety-guardrails.md)
- [Multi-Agent Collaboration](06-multi-agent-collab.md)
- [Commit Salvage Matrix](../recovery/2026-04-24-002-commit-salvage-matrix.md)
