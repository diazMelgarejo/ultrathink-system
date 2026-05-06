# 10 — V1 Hack Automation & "In Orbit" Management

> **Status:** Active | Added 2026-05-02
> **Goal:** Document all historical "v1 hacks" and define the "Orbit" automation strategy to handle them outside the microkernel.

---

## 1. The V1 Hack Inventory (Historical Debt)

These are the manual interventions required in v1.x to maintain system stability. In v2, these will be automated by "Orbit" processes.

| Hack Category | The "Clunky" V1 Solution | The "Elegant" V2 Orbit Automation |
|---------------|--------------------------|-----------------------------------|
| **Path Resilience** | Manual \`sed\` of absolute paths in \`setup_macos.py\`. | **Sentinel Node**: Dynamic path expansion via \`Path.home()\` at runtime. |
| **Bytecode Health** | Manual \`find . -name "*.pyc" -delete\`. | **GC Worker**: Background process that monitors and purges stale bytecode. |
| **Port Conflicts** | Manual \`lsof -ti:8000 | xargs kill\`. | **Port Manager**: Orchestrator-level port leasing and zombie reaping. |
| **Node Versioning** | Hardcoded shebangs or forced path usage. | **Env Validator**: Runtime check that kills the process if Node < 22 is detected. |
| **IP Discovery** | Redundant logic in \`discover.py\` and \`start.sh\`. | **Gossip Hub**: \`network_autoconfig.py\` emits live truth to \`GossipBus\`. |
| **Pairing/Auth** | Manual \`openclaw devices approve\` terminal calls. | **Auth Handshake**: Automated pairing relay via the L2 manager. |
| **Symlink Drift** | Manual creation/tracking in Git (Mode 120000). | **Link Watcher**: Self-healing symlink repair during pre-flight. **MUST** use the 5-state guard from `11-idempotency-and-guard-patterns.md` §Pattern A (valid+correct → noop; valid+wrong-target → relink; broken → repair; regular-file → warn+skip; empty → create). |

---

## 2. The "In Orbit" Strategy

To maintain a **70-line microkernel**, we will not bake health-checks into the reasoning loop. Instead, we use the **"Satellite" Pattern**:

1.  **Parallel Execution**: Health-checks and garbage collection run in a separate asyncio loop (in orbit).
2.  **Telemetry-Only**: Satellites emit events to the \`GossipBus\`.
3.  **Veto Power**: The Microkernel reads the bus; if a Satellite reports \`PORT_COLLISION\` or \`NODE_VERSION_MISMATCH\`, the kernel refuses to start.

---

## 3. Future Research: The Council of Models

The final shape of the "Orbit" system will be determined by a **Council of Models** convening soon:

*   **Google Gemini 3.1 PRO**: Will perform a comprehensive review of the "Ghost Orchestrator" security primitives.
*   **Codex GPT-5.5**: Will audit the \`MiniGraph\` engine for performance and LangGraph-parity gaps.
*   **Perplexity Deep Research**: Will provide the latest benchmarks for GGUF hardware affinity and cross-platform (Mac/Win) latency.

### Research Mandate:
- No adoption of external libraries without Council approval.
- Every "Hack" must be replaced by a "Self-Healing Skill."
- Maintain the "Nimble Vehicle" (Kernel < 1,000 lines total).

---

## 4. Integration with Merging Plan (09)
The merging of these automations will happen in **Phase 2.5 (Safety & Health Integration)**. We will repurpose the \`Sentinel Node\` (introduced in file 08) to act as the primary interface between the kernel and its orbiting satellites.
