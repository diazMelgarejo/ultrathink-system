# agate — Why It's Bigger Than Documentation

> Status: active | Added 2026-04-30 | Feeds into: v2.1 public Plugin API, v2.5 MAESTRO

---

## The Scenario B framing was wrong

The original framing: "agate = companion documentation for `model_hardware_policy.yml` published alongside `perpetua-core`."

That is like calling TCP/IP "companion documentation for BSD sockets." **agate is a protocol, not docs.**

---

## CEO framing — what actually matters at the community level

### The problem we're solving at industry scale

Every team building local-first AI tooling today — every open-source LangChain project, every CrewAI setup, every custom agent pipeline — has to answer the same question:

> "Which model do I dispatch to, on which hardware, given the task at hand?"

Today they answer it with:
- `if platform.system() == "Darwin":` hardcodes
- Magic environment variables (`OLLAMA_HOST`, `LM_STUDIO_URL`)
- Proprietary JSON blobs that live in one repo and never leave
- Tribal knowledge ("don't run 27B on the Mac, it OOMs")

There is **no shared language** for expressing hardware intent. No standard format that a LangGraph agent, a CrewAI crew, an AutoGen orchestrator, and a custom Rust runner can all read and honor. Every team reinvents this wheel. And when hardware changes (new GPU, new Mac, new team member), the config breaks silently.

### What agate changes

agate introduces a **universal hardware affinity contract** — a versioned YAML/JSON format with three semantically precise verdicts (`PREFER`, `ALLOW`, `NEVER`) that any language runtime can validate and act on.

**This is the missing infrastructure layer for local AI.** Cloud AI solved routing with API keys and region selectors. Local AI has no equivalent. agate is that equivalent.

### Why this matters for community adoption

1. **LLM-agnostic**: agate doesn't care which models you run. It describes affinity rules. New model? Add a row. New hardware tier? Add a column.

2. **Language-agnostic**: One JSON Schema. Python reads it with `pyyaml`. Node.js reads it with `js-yaml`. Rust reads it with `serde_yaml`. Any agent system in any language can validate against `model_hardware_policy.schema.json` and make correct routing decisions without knowing perpetua-core exists.

3. **Framework-agnostic**: LangGraph users, CrewAI users, AutoGen users — all blocked from using perpetua-core because our hardware gate is a Python implementation detail. But if you publish the *policy schema* separately as agate, any framework can implement the validator and plug into the ecosystem. perpetua-core becomes the reference implementation, not the only implementation.

4. **Network effects**: Once 10 teams publish their `model_hardware_policy.yml` files openly, the community has a corpus of real-world hardware constraints. Once 100 teams do, it's a dataset for tooling (auto-validation, drift detection, policy diff). Once 1000 do, it's an industry standard.

### Business trajectory (bold, optimistic)

- **v1 (now)**: One team's YAML format. Useful for us.
- **v1.1**: Published to PyPI as `agate-validator`. Any Python project can `pip install agate-validator` and validate a policy file in 3 lines.
- **v1.2**: `npm install agate` for Node.js teams. `cargo add agate` for Rust.
- **v2**: Multi-provider: cloud tiers added alongside `mac`/`windows`/`shared`. AWS GPU instances, Modal, RunPod become first-class tier targets. Now the spec bridges local and cloud.
- **v3**: agate Registry — a public index of model hardware profiles contributed by the community. Hardware vendors (Apple, NVIDIA, AMD) maintain official profiles for their silicon. Model publishers (Mistral, Qwen, Meta) publish official affinity recommendations alongside their model weights.
- **Long-term**: Hardware-aware routing becomes a checkbox in HuggingFace model cards. The agate schema is the format.

---

## Technical scenarios — all possible directions

### Scenario 1: Reference Implementation (current, v2.0)

`perpetua-core` is the Python reference implementation of the agate spec. `HardwarePolicyResolver.from_file(path)` reads a policy.yml, validates it, and exposes `check_affinity()` and `resolve()`. This is what ships in v2.0.

**Impact**: Our own system gets hardware-aware routing. Zero community reach yet.

---

### Scenario 2: PyPI Package — `agate-validator` (v2.1 target)

Extract the schema + validator into a standalone `agate-validator` Python package:

```python
pip install agate-validator

from agate import PolicyValidator
v = PolicyValidator("model_hardware_policy.yml")
v.validate()          # raises on schema violations
decision = v.resolve(task_type="coding", optimize_for="reliability")
```

**Impact**: Any Python project — LangGraph, CrewAI, AutoGen, custom — can install `agate-validator` and get hardware-aware routing without adopting perpetua-core. Zero lock-in. The spec grows independent of the runtime.

---

### Scenario 3: Multi-Language SDKs (v2.2+)

The JSON Schema is language-agnostic. Publish thin validator libraries:

- `npm install @oramasys/agate` — for TypeScript/Node.js agent frameworks
- `cargo add agate` — for Rust-based inference servers and CLI tools
- `pip install agate` — the Python SDK (superset of agate-validator)

Each SDK does three things: (1) load a policy.yml, (2) validate against the JSON Schema, (3) resolve a task+hardware tuple to a routing decision. That's the entire contract. 50–100 lines per language.

**Impact**: LangChain.js users, Rust inference server operators, TypeScript-based agent builders all get the same routing contract without a Python dependency.

---

### Scenario 4: OpenAPI Companion for Plugin API (v2.1 Plugin API)

When the Plugin API goes public in v2.1, `POST /v1/route` returns a routing decision. The agate schema is the input/output contract for that endpoint:

```http
POST /v1/route
Content-Type: application/json

{
  "task_type": "coding",
  "optimize_for": "reliability",
  "available_tiers": ["mac", "shared"]
}

→ 200 OK
{
  "model": "Qwen3.5-27B-...",
  "hardware_tier": "windows",
  "verdict": "PREFER",
  "reason": "policy:coding:reliability"
}
```

agate defines the vocabulary. The Plugin API implements it over HTTP. External agents call it without loading any Python.

**Impact**: LangGraph, CrewAI, AutoGen agents call perpetua-core as a hardware routing *service* — a black box they POST to. They get hardware-aware dispatch without touching our stack.

---

### Scenario 5: Model Card Integration (v3+)

HuggingFace model cards currently list quantization details, context windows, and benchmarks. They don't express hardware affinity in a machine-readable way.

agate could become the format for hardware affinity in model cards:

```yaml
# HuggingFace model card extras (proposed)
hardware_affinity:
  agate_version: 1
  mac: ALLOW      # works with MLX quantization
  windows: PREFER # reference hardware for this model
  shared: ALLOW   # CPU-only possible but slow
```

A model publisher adds this to their card. Any agate-compatible tool reads it automatically. No manual policy authoring required — the model tells you where it runs best.

**Impact**: Eliminates the "which models work on my hardware?" discovery problem. Hardware affinity becomes self-describing at the model level.

---

### Scenario 6: Hardware Vendor Official Profiles (v3+)

Apple, NVIDIA, AMD have a stake in developers knowing their hardware's capabilities:

- Apple publishes official agate profiles: "M3 Max 48GB supports these models at PREFER tier"
- NVIDIA publishes: "RTX 4090 24GB PREFER list" vs "RTX 3080 10GB PREFER list"
- AMD publishes ROCm-compatible model profiles

Developers pull from a vendor-maintained registry instead of guessing or benchmarking blind.

**Impact**: Hardware selection becomes data-driven for local AI builders. agate becomes the interface between hardware specifications and model deployment decisions.

---

### Scenario 7: Enterprise Policy Enforcement (v2.5+)

Organizations with compliance requirements (HIPAA, GDPR, ITAR) need to ensure sensitive tasks never leave approved hardware:

```yaml
models:
  sensitive-reasoning-model:
    mac: PREFER   # approved on-prem hardware
    windows: PREFER
    shared: NEVER  # shared = cloud = compliance violation
    cloud: NEVER
```

The `NEVER` verdict becomes a *compliance gate*, not just a hardware hint. Security teams author policy files. The runtime enforces them. MAESTRO's hardware attestation layer (v2.5) plugs into this — NEVER verdicts trigger human review gates via HITL interrupts.

**Impact**: Local AI becomes viable in regulated industries where today you can't use cloud LLMs without legal review.

---

### Scenario 8: Multi-Site LAN Federation (Redis Coordination module)

Multiple sites, each with their own LAN topology, share a federated agate policy:

```yaml
metadata:
  sites:
    site-a:
      mac_endpoint: "http://10.0.1.110:1234/v1"
      windows_endpoint: "http://10.0.1.108:1234/v1"
    site-b:
      mac_endpoint: "http://10.0.2.110:1234/v1"
```

The routing engine picks the nearest available tier across sites. agate policy defines *what*, the federation layer handles *where*.

**Impact**: Multi-site research labs, distributed engineering teams, and on-prem enterprise deployments all get hardware-aware routing across their full infrastructure.

---

### Scenario 9: Auto-Discovery and Drift Detection

Build tooling that reads running hardware and validates the policy against it:

```bash
agate check --policy model_hardware_policy.yml --discover

Checking policy against discovered hardware...
✅ mac tier: Apple M2 Pro 16GB — matches PREFER for Qwen3.5-9B-MLX-4bit
❌ windows tier: Not reachable at 192.168.1.108:1234 — policy expects PREFER
⚠️  shared tier: GPU unavailable — downgrading PREFER to ALLOW for affected models
```

Policy drift detection: your policy says a model should PREFER Windows, but the Windows machine is offline. Alert instead of silent fallback.

**Impact**: Eliminates silent routing failures — today, a downed machine means requests silently fall back or timeout. agate tooling makes the failure visible and policy-auditable.

---

### Scenario 10: GGUF Extension RFC (open question OQ2)

GGUF is the file format for quantized local models (llama.cpp, Ollama, LM Studio). Currently it stores quantization metadata but not hardware affinity.

Proposal: a GGUF metadata extension that embeds agate verdicts directly in the model file:

```
[GGUF metadata block]
agate.version = 1
agate.mac = "ALLOW"
agate.windows = "PREFER"
agate.context = 16384
```

Model runners (Ollama, LM Studio, koboldcpp) can read this metadata at load time and enforce affinity automatically — before the user even writes a policy file.

**Impact**: Hardware affinity becomes *model-native*. agate verdicts travel with the model file instead of living in a separate config that can drift.

---

## Summary table

| Scenario | When | Reach | Effort | Impact |
|----------|------|-------|--------|--------|
| 1. Reference impl (current) | v2.0 | Our system only | Done | Kernel stability |
| 2. PyPI `agate-validator` | v2.1 | All Python agent builders | Low | Ecosystem entry point |
| 3. Multi-language SDKs | v2.2+ | JS, Rust, Go communities | Medium | Language-agnostic adoption |
| 4. OpenAPI Plugin API companion | v2.1 | All REST-capable frameworks | Low | LangGraph/CrewAI/AutoGen unlock |
| 5. Model card integration | v3+ | HuggingFace ecosystem | High (partnership) | Self-describing models |
| 6. Vendor official profiles | v3+ | Hardware buyers everywhere | High (partnership) | Hardware selection data |
| 7. Enterprise compliance gate | v2.5 | Regulated industries | Medium | HIPAA/GDPR/ITAR deployments |
| 8. Multi-site federation | Redis module | Distributed orgs | Medium | Enterprise scale |
| 9. Drift detection tooling | v2.2+ | Ops teams | Low | Observability + reliability |
| 10. GGUF extension RFC | v3+ | Model packaging ecosystem | High (community RFC) | Model-native affinity |

---

## Why now, not later

The local LLM ecosystem is consolidating fast. LM Studio, Ollama, and llama.cpp have already won the local-first runtime war. The next layer — routing, orchestration, hardware awareness — is still fragmented. There is no dominant standard for hardware affinity policy.

That gap closes in the next 12–18 months, either because someone publishes a standard (agate) or because a vendor (Ollama, LM Studio, HuggingFace) bakes their own proprietary format in and the ecosystem fractures.

**Publishing agate now costs almost nothing** (we already wrote the schema to make perpetua-core work). The upside is a seat at the table when the routing layer of the local LLM stack gets standardized.

---

## Next actions

1. **Immediately**: `oramasys/agate` on GitHub — the repo is already initialized locally. Create the org, push.
2. **v2.1**: Extract `agate-validator` as a standalone PyPI package. Publish.
3. **v2.1**: `POST /v1/route` on the Plugin API returns an agate-schema-compliant response.
4. **v2.2**: Write the GGUF extension RFC as an `agate/docs/gguf-rfc.md`. Post to r/LocalLLaMA, llama.cpp discussions, Ollama GitHub. Gauge community interest.
5. **v3**: Reach out to HuggingFace about model card integration. They have a `library_name` field precedent for tool-specific metadata.
