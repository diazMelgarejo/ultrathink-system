# Orama History Recovery

Date: 2026-04-24
Branch: `2026-04-24-001-orama-salvage`
Clean anchor: `86a6300dcbfd10a8626f65dc7c996428fd5a02ea`

## Objective

Create a clean future lineage for `orama-system` without replaying polluted tail commits.
The tail range `f66976b..1e93f07` contains useful intent, but all commits were authored
with non-canonical identity metadata and several commits touch private or generated
configuration. Those commits are audit input only.

## Recovery Rules

- New commits must use `cyre <Lawrence@cyre.me>`.
- Do not cherry-pick or merge the polluted tail directly.
- Manual-port only reviewed intent into new commits with precise conventional subjects.
- Treat `.env` as private and ignored.
- Treat `.paths` as generated runtime-local state, not source-controlled truth.
- Keep `.env.example` and `.paths.example` as the documented templates.
- Do not replace real source files with symlinks to sibling repos.
- Preserve `perplexity-api/ultrathink-system` only as a shallow backup/reference checkout.

## Snapshot Evidence

Pre-branch snapshots are stored at:

`../recovery-snapshots/2026-04-24-001-orama-salvage/`

The snapshot captures branch, HEAD, shallow status, dirty state, untracked state,
`.ecc` state, tracked config state, and repo-local Git identity for both active
recovery inputs.

## `.ecc` Handling

At recovery start, Git expected `.ecc` to be a gitlink-like entry while the working
tree contained a symlink to a sibling `ecc-tools` checkout. That mismatch blocked
normal Git inspection. The symlink was moved into the snapshot directory before
branch creation so Git status could run cleanly.

Future work must not rely on tracked symlink assumptions for `.ecc`. If an ECC
tooling checkout is needed, document it as local setup or restore it through a
validated bootstrap step.

## Exit Criteria

- `git status --short --branch` works on the salvage branch.
- `scripts/review/repo_hygiene.py` reports no hard failures.
- `scripts/git/check_identity.sh` confirms canonical identity.
- `.env` and `.paths` are untracked and ignored.
- The commit salvage matrix explains every dropped or manually ported tail commit.
