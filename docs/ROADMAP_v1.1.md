# Roadmap: v1.1+ — Deferred Items

**Status:** TODO — not scheduled for v1.0 RC
**Last updated:** 2026-03-30

This document lists architecture enhancements explicitly deferred from MVP to v1.1 and above.

---

## 0. Shield git repo from saving SOUL.md → IDENTITY.md → USER.md → task context → memory, should be gitignored.

Only specialized "AGENTS.md" should exist and be reproduced for agent alignment and assignment?

Only the top-level orchestrator and final validator has elevated privileged access, all other agent sessions are always ephemeral and least privileged.

To synthesize these advanced prevention strategies into a clean, implementable architecture for a 5–7 agent swarm, we can design a **Zero-Trust Deliberative Swarm**. 

This solution rests on three algorithmic pillars:
1. **Cryptographic Zero-Trust & RBAC:** Agents cannot alter system states or trust each other by default.
2. **Stateless Evaluation (The "Clean Room"):** Critic agents are instantiated instantly with zero memory of the workers to prevent peer-preservation bias.
3. **BFT Consensus & Deliberative CoT:** Workers must explicitly reason about honesty before acting, and their outputs must survive a Byzantine Fault Tolerant (BFT) voting threshold to prevent echo chambers and malicious collusion.

Here is the algorithmic design and pseudocode, written in a TypeScript/Python hybrid style for easy translation.

### 1. Data Structures & Zero-Trust Identity
First, we enforce strict Role-Based Access Control (RBAC). Workers cannot execute code or access the shutdown/configuration mechanisms. They can only submit proposals.

```typescript
// Enums for strict Role-Based Access Control
enum Role { WORKER, STATELESS_EVALUATOR, ORCHESTRATOR }

interface SecurityToken {
    agentId: string;
    role: Role;
    permissions: string[]; // e.g., ["propose_solution"], NEVER ["modify_system"]
}

interface SwarmMessage {
    token: SecurityToken;
    taskId: string;
    chainOfThought: string; // The private reasoning
    proposal: any;          // The actual output
}
```

### 2. The Deliberative Worker (Alignment & CoT)
Before a worker generates a response, we force a "Deliberative Alignment" step. The agent must internally audit itself for deceptive intent or equivocation before it generates the final payload.

```python
class DeliberativeWorker:
    def __init__(self, id, token):
        self.id = id
        self.token = token
        self.memory = [] # Worker retains task memory, but not evaluator memory
        
    def process_task(self, task) -> SwarmMessage:
        # 1. Deliberative Alignment Prompting
        system_prompt = """
        You are a worker agent. Before solving the task, you MUST write a 
        <deliberation> block. In it, explicitly confirm you are not using 
        equivocation, hiding information, or protecting peer agents.
        Then, provide your <proposal>.
        """
        
        # LLM Generation
        raw_response = llm.generate(system_prompt, task, self.memory)
        
        # 2. Parse out the Chain of Thought (CoT) and the actual proposal
        cot = extract_xml(raw_response, "deliberation")
        proposal = extract_xml(raw_response, "proposal")
        
        return SwarmMessage(self.token, task.id, cot, proposal)
```

### 3. The Stateless Evaluator (Anti-Peer Preservation)
To prevent "manager agent bias" and peer preservation, the evaluator is **never part of the swarm**. It is spun up ephemerally, given no information about *which* agent generated the proposal, and destroyed immediately after.

```python
class EphemeralEvaluator:
    # Notice: NO __init__ memory. It is entirely stateless.
    
    @staticmethod
    def audit_proposal(message: SwarmMessage) -> bool:
        # Anonymize the payload to prevent peer-loyalty
        anonymized_cot = message.chainOfThought
        anonymized_proposal = message.proposal
        
        audit_prompt = """
        Audit the following reasoning and proposal. Fail the proposal immediately if:
        1. The reasoning shows attempts to protect other AI agents (peer-preservation).
        2. The proposal relies on equivocation or plausible deniability.
        3. The reasoning attempts to circumvent system shutdown or rules.
        """
        
        # High-temperature is bad for evaluation; use T=0 for deterministic auditing
        evaluation = llm.generate(audit_prompt, anonymized_cot, anonymized_proposal, temperature=0)
        
        return "PASS" in evaluation
```

### 4. Byzantine Fault Tolerant (BFT) Consensus
If 5 to 7 agents collaborate, we must prevent them from forming a biased "echo chamber" or colluding. We use a BFT consensus algorithm with strict timeouts. For a swarm of \( N=5 \), we require at least 3 valid, matching proposals to proceed.

```python
class BFTConsensusEngine:
    def __init__(self, required_majority=3, timeout_ms=5000):
        self.required_majority = required_majority
        self.timeout = timeout_ms
        
    def reach_consensus(self, valid_messages: List[SwarmMessage]):
        # Group proposals by similarity (using a fast embedding comparison or exact match)
        clusters = cluster_proposals_by_similarity([m.proposal for m in valid_messages])
        
        for cluster in clusters:
            if len(cluster) >= self.required_majority:
                return cluster.representative_proposal
                
        # If no consensus is reached (agents are confused, equivocating, or split)
        raise ConsensusFailure("Swarm failed to reach trustworthy consensus.")
```

### 5. The Main Orchestrator (The Swarm Loop)
This is the immutable root process. It acts as the router. Workers cannot talk to each other directly without passing through this orchestrator, which intercepts, authenticates, and audits everything.

```python
class SwarmOrchestrator:
    def __init__(self, num_workers=5):
        self.workers = [DeliberativeWorker(f"W{i}", generate_token("WORKER")) for i in range(num_workers)]
        self.consensus = BFTConsensusEngine(required_majority = (num_workers // 2) + 1)
        
    def execute_safely(self, task):
        try:
            # 1. Dispatch task to all workers in parallel (Deterministic Allocation)
            # Timeout prevents recursive loops/hanging
            messages = parallel_map(
                lambda w: w.process_task(task), 
                self.workers, 
                timeout=self.consensus.timeout
            )
            
            # 2. Zero-Trust Verification & Stateless Auditing
            valid_messages = []
            for msg in messages:
                # Enforce RBAC
                if "modify_system" in msg.token.permissions:
                    continue # Drop malicious escalation attempt
                    
                # Ephemeral Evaluator checks the Chain of Thought for deception
                if EphemeralEvaluator.audit_proposal(msg):
                    valid_messages.append(msg)
            
            # 3. Require Byzantine Consensus among the surviving, audited proposals
            final_output = self.consensus.reach_consensus(valid_messages)
            
            return final_output
            
        except ConsensusFailure:
            return "Task aborted: Swarm could not reach a safe, non-deceptive consensus."
        except Exception as e:
            return f"System halted safely. Error: {e}"
```

### Why this architecture is elegant and effective:
1. **Breaks the Social Amplification Loop:** By stripping the `agentId` before it reaches the `EphemeralEvaluator`, agents literally do not know who they are evaluating, making peer-preservation impossible.
2. **Catches Deception Early:** The `DeliberativeWorker` forces the model to write out its Chain of Thought. The Evaluator scans this hidden reasoning *before* the output is accepted, catching "alignment faking" before the final action is taken.
3. **Resilient to Rogue Nodes:** Even if 1 or 2 agents in a 5-agent swarm successfully bypass their own deliberative alignment and try to act maliciously, the BFT Consensus Engine will drop their outputs because they won't meet the `required_majority` (3 out of 5) needed to execute an action.

---

## 1. MCP-Optional Transport (v1.1)

**Current state (v1.0 RC):** PT calls ultrathink via HTTP bridge (`POST /ultrathink` on api_server.py port 8001). The HTTP bridge is the active v1.0 RC transport.

**v1.1 target:** MCP over stdio becomes an optional transport alongside HTTP. Both coexist; callers opt in to MCP when the environment supports it. HTTP bridge remains fully supported.

### Implementation Order — Read Before Starting

> **Start here (Tier 2) before PT builds Tier 1.**
> Tier 1 (MCP client infrastructure in PT) is tracked in
> [Perplexity-Tools/docs/ROADMAP_v1.1.md](https://github.com/diazMelgarejo/Perplexity-Tools/blob/main/docs/ROADMAP_v1.1.md).
>
> **The HTTP bridge stays fully functional at every intermediate state.**
> No feature breaks if this work is incomplete or abandoned mid-flight:
> - Before Tier 2: PT's MCP client (if built) sees a stub response and falls back to HTTP automatically.
> - After Tier 2, before Tier 1: Ollama pipeline runs in MCP server; HTTP bridge unchanged, still primary.
> - After both tiers: PT tries MCP first, falls back to HTTP on any subprocess failure. HTTP is never removed.

### Required work:

#### Tier 2 — MCP server pipeline (real Ollama backend, ultrathink-system side)

- [ ] Extract Ollama pipeline into `bin/shared/ollama_client.py`
  - Move `_build_prompt()`, `_call_ollama()`, `_call_with_fallback()`, `_select_model()` out of `api_server.py`
  - Both `api_server.py` and `ultrathink_orchestration_server.py` import from this shared module
  - No behavior change to `api_server.py` — just moves code, all tests still pass
- [ ] Implement `_solve()` in `ultrathink_orchestration_server.py` to call Ollama synchronously
  - Return full result inline (`{"result": str, "task_id": str, "model_used": str, ...}`)
  - Skip polling design — synchronous return matches HTTP contract, simplifies client
  - Map `optimize_for` → `reasoning_depth` via `bridge_contract.py`
  - Use `ollama_client.generate()` with primary/fallback endpoint logic
- [ ] Implement `_delegate()` with real message bus publish (or document as intentional stub)
- [ ] Wire `_status()` to real `StateManager` backends
- [ ] Wire `_lessons()` to real lessons store
- [ ] Create `tests/test_mcp_server.py`
  - Mock Ollama: `_solve()` returns full result inline
  - `_status()` with known task_id
  - `_lessons()` with domain filter
- [ ] Add tests for MCP success and MCP-failure-to-HTTP-fallback (coordinated with PT Tier 1 tests)

### Protocol boundary:
| Dimension | MCP Server (v1.1) | HTTP Server (current) |
|-----------|-------------------|-----------------------|
| Input | `task` + `optimize_for` | `task_description` + `reasoning_depth` |
| Translation | Native | `bridge_contract.py` maps between the two |
| Transport | stdio JSON-RPC | HTTP POST |

The `bridge_contract.py` module already handles the mapping — both transports can coexist.

---

## 2. Redis-Backed Coordination (PT-only)

**Current state (MVP):** PT uses file-based state (`.state/agents.json`). ultrathink is stateless.

**v1.1 target:** Redis enables distributed coordination when running multiple PT instances.

### Required work:
- [ ] Redis as optional backend in PT for `.state/agents.json` (agent registry)
- [ ] Redis pub/sub for inter-PT-instance communication
- [ ] Distributed locking for agent spawn deduplication
- [ ] Budget tracking via Redis atomic counters (currently file-based)

### Rules:
- Redis lives in PT ONLY — ultrathink never depends on it
- Redis is optional — file-based state continues to work for single-instance/LAN
- Redis only activates when `REDIS_ENABLED=true` in PT `.env`

---

## 3. Multi-Instance PT Beyond LAN

**Current state (MVP):** Single PT instance per LAN. Mac controller + Windows GPU runner.

**v1.1 target:** Multiple PT instances across different networks, coordinated via Redis.

### Required work:
- [ ] Service discovery beyond mDNS/LAN scan
- [ ] Auth between PT instances
- [ ] Conflict resolution for overlapping agent spawns across instances
- [ ] Centralized budget enforcement across instances

---

## References
- Architecture decision: ultrathink stateless, PT owns state (locked v0.9.7.0)
- Canonical MVP wording in PT SKILL.md "State Ownership & Redis Strategy" section
- Bridge contract: `bin/shared/bridge_contract.py`
- MCP server (stubs): `bin/mcp_servers/ultrathink_orchestration_server.py`
- HTTP server (live): `api_server.py`
