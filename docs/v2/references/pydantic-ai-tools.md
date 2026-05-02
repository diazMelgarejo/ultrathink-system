# Feature Extraction: Pydantic AI Tool Ergonomics

> **Goal:** Repurpose the \`@tool\` decorator to auto-derive JSON schemas from Python type hints without the \`pydantic-ai\` runtime.

## 1. The Core Mechanic
Pydantic AI uses Python's \`inspect\` module to read function signatures and then dynamically creates a Pydantic Model (using \`create_model\`) to represent the tool's input.

## 2. Best Practices to Mine
- **Docstring Parsing**: Automatically extract the "description" field for tool parameters from the function's docstring.
- **Dependency Injection**: Use a \`RunContext\` object as the first argument, allowing tools to access the current \`PerpetuaState\` without being explicitly passed it by the LLM.
- **Strict Validation**: Reject model outputs that don't match the schema before they ever hit the tool logic.

## 3. oramasys v2 Adaptation
Our \`graph/tool.py\` plugin will implement a "Slim Tool" decorator.

**Reference Implementation Hint:**
\`\`\`python
import inspect
from pydantic import create_model

def tool(fn):
    sig = inspect.signature(fn)
    # Filter out RunContext/State from the schema sent to LLM
    # Generate Pydantic v2 model from the remaining args
    fn._json_schema = InputModel.model_json_schema()
    return fn
\`\`\`
