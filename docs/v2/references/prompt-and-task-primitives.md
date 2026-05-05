# Feature Extraction: Prompt & Task Primitives

> **Goal:** Repurpose the "Declarative Task" model from CrewAI and the "Explicit Template" model from LangChain for our L3 orchestration.

---

## 1. The "V1 Hack" Baseline

In v0.9.9.8, prompts were often hardcoded in the node logic or kept in separate \`SOUL.md\` files:

```python
# v1 style

system_prompt = open("SOUL.md").read()
response = await llm.chat(system_prompt + user_input)
```

**Problem**: Logic was coupled to the persona. If you wanted to change the prompt, you had to edit the code or the file. No centralized management.

## 2. Framework "Magic" (Technical Analysis)

### A. CrewAI (Task-Persona Model)

- **Personas**: Agents are defined by \`role\`, \`goal\`, and \`backstory\`.
- **Tasks**: Defined by \`description\` and \`expected_output\`.
- **Automation**: The framework concatenates these into a single "Master Prompt" at runtime.

### B. LangChain (PromptTemplates)

- **Modularity**: Prompts are treated as logic-less templates (\`"Analyze this: {text}"\`).
- **Composition**: Multiple templates can be piped together.

## 3. oramasys v2: The "Ghost" Primitive Implementation

We will adopt a **Hybrid Declarative** approach.

### Key Structure (Planned for oramasys/bin/config/agent_registry.json)

```json
{
  "agents": {
    "researcher": {
      "persona": {
        "role": "Deep Search Specialist",
        "backstory": "Expert in verifying claims and cross-referencing sources."
      },
      "default_task": {
        "instructions": "Extract 3 key facts about {topic}.",
        "expected_format": "Markdown bullet points"
      }
    }
  }
}
```

### Runtime Injection (Planned for nodes.py)

```python

# The "Ghost" Prompt Builder

def build_agent_prompt(agent_id: str, state: PerpetuaState) -> str:
    agent_cfg = registry.get(agent_id)
    template = agent_cfg["default_task"]["instructions"]

    # LangChain-style injection from shared state
    instructions = template.format(**state.scratchpad)
    
    return f"""
    Role: {agent_cfg['persona']['role']}
    Backstory: {agent_cfg['persona']['backstory']}
    Task: {instructions}
    Output Format: {agent_cfg['default_task']['expected_format']}
    """
```

## 4. Integration with Primitives

- **State-Driven**: Because prompts pull from \`state.scratchpad\`, the same agent can behave differently depending on the previous node's output (Ghost Orchestration).
- **Auditability**: The final generated prompt is emitted to the \`GossipBus\` as a \`dispatch\` event, ensuring 100% observability.
- **Independence**: The microkernel remains dumb (D4); it just calls the \`build_agent_prompt\` utility provided by the \`oramasys\` layer.
