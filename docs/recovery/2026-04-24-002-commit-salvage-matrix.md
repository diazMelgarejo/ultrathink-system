# Commit Salvage Matrix

Range reviewed: `f66976b..1e93f07`

Policy: do not replay these commits. Manual-port approved behavior only after
reviewing the diff and excluding private config, generated paths, broken symlink
assumptions, and non-canonical commit metadata.

| Commit | Original intent | Disposition | Clean-lineage action |
| --- | --- | --- | --- |
| `f66976b` | Python 3.9 compatibility and PT home default update | `manual-port` | Keep `from __future__ import annotations` if needed. Do not copy `.env`. Keep PT path naming aligned with the active companion repo path until a separate rename is complete. |
| `e13dd45` | Document default `SETUP_PASSWORD` | `manual-port` | Document only in `.env.example` with an explicit non-production warning. Do not add private values to `.env`. |
| `36da29c` | Pass `SETUP_PASSWORD` into fallback bootstrap | `manual-port` | Pass a safe environment value to the subprocess if the inline fallback still starts AlphaClaw. |
| `f3aeb50` | Make `.paths` os-agnostic | `drop` | `.paths` is generated runtime-local state. Preserve semantics in `.paths.example` and docs only. |
| `bce6b75` | Use relative `PT_HOME` in `.env` | `drop` | `.env` must be private and ignored. Do not port tracked `.env` edits. |
| `e431bed` | Add venv self-repair | `manual-port` | Port only after validating shell behavior. Keep repair script explicit and non-destructive. |
| `a676adc` | Document os-agnostic path policy | `manual-port` | Preserve as recovery guidance and `.paths.example` comments. |
| `b751c1d` | Link shared agentic stack from PT | `drop` | Do not track sibling-repo symlinks. If needed later, generate locally during startup with validation. |
| `e73b138` | Enforce upstream-compatible ghost orchestration policy | `manual-port` | Documentation-only, after checking it does not reference stale names as current behavior. |
| `48e2272` | Move IP autodetect earlier and clean pyc files | `manual-port` | Port only the safe ordering/cleanup intent if startup tests prove it. Do not obscure startup diagnostics. |
| `e04686a` | Sync IP detection to shared net utilities and fix setup errors | `manual-port` | Port fixes only. Do not replace `network_autoconfig.py` with a symlink to PT. |
| `15aecb0` | Add symlink validation and convert `network_autoconfig.py` to symlink | `drop` | Keep symlink validation as a local bootstrap idea only. Do not track source-file symlinks. |
| `1e93f07` | Automate symlink creation from live discovered paths | `manual-port` | Preserve only as future local setup design. Do not auto-create repo-tracked symlinks as part of normal startup. |

## Notes

The polluted tail also contains broad rename churn between historical names,
Perplexity/Perpetua naming, and active `orama-system` naming. Rename cleanup must
be done as explicit edits in the clean branch, not by replaying the tail.
