# Feature Extraction: Agentic Engineering Patterns

> **Ref:** Andrej Karpathy (March of Nines)

## 1. The Core Mechanic: Deterministic Harnessing
Rather than prompting an agent to "Fix this bug," we define a harness: **"Write a failing test → Fix the bug → Run test again."** This makes a 90%-reliable LLM nearly 100% reliable by wrapping it in deterministic code.

## 2. Best Practices to Mine
- **LLM-Wiki (Project Memory)**: Agents must read \`LESSONS.md\` and \`SKILL.md\` before every implementation task.
- **Probe Nodes**: Every write operation must be preceded by a read operation to verify the target state.
- **Success Criteria**: Every agent spawn must have a "Verification Node" automatically appended to the graph to score the output.

## 3. oramasys v2 Adaptation
We will implement the **"Sentinel Node"** (v2.5) which automates this pattern.

**Reference Implementation Hint:**
\`\`\`python
# A Sentinel Node that enforces the "March of Nines":
def sentinel_check(state: PerpetuaState):
    if not state.metadata.get("test_ran"):
        raise RuntimeError("Sentinel Violation: Agent attempted implementation without a test run.")
    return {"status": "verified"}
\`\`\`
