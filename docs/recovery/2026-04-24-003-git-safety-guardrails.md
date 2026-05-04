# Git Safety Guardrails

## Identity

All clean-lineage commits must use:

```text
cyre <Lawrence@cyre.me> or Codex <codex@openai.com>
```

Before committing:

```bash
bash scripts/git/check_identity.sh
```

## Branch Naming

Use dated, monotonic branch names:

```text
yyyy-mm-dd-001-brief-summary
```

Example:

```text
2026-04-24-001-orama-salvage
```

## Before Risky Git Work

Always capture state before branch surgery, rebases, cleanups, or cross-repo sync:

```bash
git status --short --branch
git stash push --include-untracked -m "preserve work before <operation>"
git rev-parse --is-shallow-repository
git config user.name
git config user.email
```

Never run destructive cleanup commands until the stash/snapshot has been verified.

## Private And Generated Config

- `.env` is private and ignored.
- `.env.local` is private and ignored.
- `.env.example` is the only tracked environment template.
- `.paths` is generated runtime-local state and ignored.
- `.paths.example` is the only tracked path template.

## GitHub Actions Permissions

Workflow permissions must be minimal and explicit.

- Release jobs need `contents: write`.
- PR automation needs `pull-requests: write`.
- Read-only CI should use default read behavior or an explicit read-only block.
- Avoid broad top-level write permissions.

## Commit Bodies

Use detailed conventional commits for salvage work:

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
