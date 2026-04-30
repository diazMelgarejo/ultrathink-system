# 06 — Open Questions

Items deliberately deferred. Each has a target checkpoint for resolution.

---

## Active open questions

| # | Question | Context | Resolve by |
|---|----------|---------|------------|
| OQ1 | **Pydantic AI as framework** — at v2.1+, evaluate whether `pydantic-ai` (`Agent`, `Tool`, `RunContext`) should supplement or replace `MiniGraph` for the application layer (not kernel). | Pydantic AI is a framework built on Pydantic v2. It's a LangGraph competitor. MiniGraph is our custom engine. The question is whether v2.1's app layer uses one, both, or neither. | v2.1 checkpoint |
| OQ2 | **GGUF hardware spec extension** — a community RFC to add `system_requirements` to the GGUF metadata layer has been pending since Oct 2024 with no timeline. Do we wait for it, or does `agate` serve as the bridge (mapping GGUF model IDs to hardware policy)? | The GGUF format is the de facto standard for local model metadata. Adding hardware requirements to GGUF would let any GGUF loader natively enforce hardware affinity without a separate policy file. | agate v0.1 release |
| OQ3 | **`agate` naming** — Perplexity proposed "agate" as the name for the published hardware policy spec (memorable vs. `model-hardware-policy-spec`). The repo is confirmed as `oramasys/agate`. Should the Python package also be `agate` on PyPI? Check availability. | Name availability determines distribution strategy. | agate repo setup |
| OQ4 | **GitHub org `oramasys` creation** — user confirmed creating a real GitHub org. Steps: go to github.com/organizations/new → choose plan → name `oramasys`. Then transfer or create repos there. | Org creation is a manual step requiring the user to log in at github.com. Once done, run: `gh api orgs/oramasys` to verify, then `git remote set-url origin git@github.com:oramasys/{repo}.git` in each new repo. | Immediate (user action) |
| OQ5 | **Agent identity attestation (MAESTRO Layer 3)** — v2.5 MAESTRO Layer 3 requires agents to attest their identity per dispatch. Options: (a) cryptographic signing per agent process (secure, complex); (b) per-session UUID cached in state (simple, spoofable); (c) `metadata["agent_id"]` in PerpetuaState (already there, honor-system). | Cryptographic attestation may be overkill for a LAN-local system. Honor-system agent IDs may be sufficient until the system is exposed externally. | v2.5 safety planning |
| OQ6 | **Perpetua-Tools repository** — the 2026-04-28 revamp plan (Tasks 0 and 1) requires changes to `Perpetua-Tools` repo (CI blocker fix + Perplexity-Tools → Perpetua-Tools typo). PT is not available locally. Location: `github.com/diazMelgarejo/Perpetua-Tools`. | Need to `gh repo clone diazMelgarejo/Perpetua-Tools` to continue Tasks 0 and 1. | v1.0 RC (immediate) |
| OQ7 | **Python version for new repos** — v1.0 RC runs on Python 3.9 (per test environment). v2 spec requires Python ≥ 3.11 (per revamp policy). New repos (`perpetua-core`, `oramasys`, `agate`) should target 3.11+. Confirm this doesn't block any CI runner. | Python 3.11+ enables `tomllib`, `ExceptionGroup`, and cleaner `match` syntax. Most importantly, `PerpetuaState.model_dump_json()` behavior is more predictable on 3.11+. | perpetua-core setup |
| OQ8 | **`optimize_for` field name** — GPT scaffold uses `optimize_for` (matching policy routing keys: `coding:reliability`). The Grok files use `opt_hint`. Our spec used `opt_hint`. Should standardize on `optimize_for` (GPT scaffold = the reference implementation). | Minor naming question but affects API contract. `optimize_for` is more ergonomic and matches policy file routing key structure. | perpetua-core Phase 1 |
| OQ9 | **`quickstart.py` scope** — DX assessment flags TTHW ≤ 10 min as a target. `quickstart.py` should demonstrate: (a) 3-node graph, (b) hardware routing, (c) HITL pause + resume. Does it live in `perpetua-core/` or `oramasys/`? | Quickstart should live in `oramasys/` (it uses both repos). Ideally runnable with `uvicorn oramasys.orama.api.server:app --reload` + a separate `curl` or Python client. | v2.0 Phase 3 |

---

## Resolved (logged for posterity)

| # | Question | Resolution | Date |
|---|----------|------------|------|
| D1 | Clean-slate vs. evolve-in-place | Clean-slate rewrite | 2026-04-30 |
| D2 | Repo names | `perpetua-core` + `oramasys` | 2026-04-30 |
| D3 | v2 sequencing | v1.0 RC first | 2026-04-30 |
| D4 | Architecture model | Microkernel | 2026-04-30 |
| D5 | Plugin API | Internal v2.0, public v2.1 | 2026-04-30 |
| D6 | Spec layout | Master + per-module | 2026-04-30 |
| D7 | Schema lib | Pydantic v2 (Pydantic AI = framework, not schema lib) | 2026-04-30 |
| D8 | Kernel tier | Tier 3 (~220 lines) | 2026-04-30 |
| D9 | Build approach | GPT Phase 1-4, lift proven pieces | 2026-04-30 |
| D10 | License | MIT | 2026-04-30 |
| D11 | 3rd new repo | `oramasys/agate` (Hardware Policy Specification) | 2026-05-01 |
| D12 | GitHub org | Real GitHub org `oramasys` (user to create at github.com/organizations/new) | 2026-05-01 |
| D13 | TDD policy | Enshrined in `docs/v2/README.md` and `04-build-order.md`. tdd.md is the source of truth. | 2026-05-01 |
