# Deep Dive: Pydantic AI "Slim" Tool Extraction

> **Goal**: Extract the high-end ergonomics of Pydantic AI's \`@tool\` decorator without the \`pydantic-ai\` runtime or the \`griffe\` dependency.

## 1. The "V1 Hack" Baseline
In v0.9.9.8, tool schemas were defined manually in JSON or required heavy boilerplate:
\`\`\`python
# v1 style
tools = [
    {
        "name": "get_weather",
        "description": "Get weather for city",
        "parameters": { ... large manual json ... }
    }
]
\`\`\`
**Result**: High friction for developers; prone to schema-code drift.

## 2. Pydantic AI "Magic" (Technical Analysis)
Pydantic AI uses three components to automate this:
1.  **\`inspect.signature\`**: Reads the Python function's arguments and types.
2.  **\`griffe\`**: A library used to parse docstrings into structured metadata.
3.  **\`pydantic.create_model\`**: Combines the above into a dynamic validator.

## 3. oramasys v2: The "Slim" Implementation
We will adopt the **"Shadow Model"** pattern but replace \`griffe\` with a simple regex-based docstring parser (Google-style support only) to keep dependencies minimal.

### Key Logic (Planned for graph/tool.py):
\`\`\`python
import inspect
from pydantic import create_model, Field

def tool(fn):
    # 1. Inspect signature
    sig = inspect.signature(fn)
    
    # 2. Extract descriptions from docstring (Simple Regex)
    # (We parse ":param name: description" or "name (type): description")
    doc = fn.__doc__ or ""
    arg_descriptions = _parse_google_docstring(doc)
    
    # 3. Build the Shadow Model
    fields = {}
    for name, param in sig.parameters.items():
        if name in ("ctx", "state"): continue # The "Ghost" skip
        
        fields[name] = (
            param.annotation, 
            Field(
                default=... if param.default == inspect.Parameter.empty else param.default,
                description=arg_descriptions.get(name, "")
            )
        )
    
    fn._shadow_model = create_model(f"{fn.__name__}Args", **fields)
    fn._mcp_schema = fn._shadow_model.model_json_schema()
    return fn
\`\`\`

## 4. Integration with Primitives
- **MCP Compatibility**: The \`_mcp_schema\` generated here is directly consumable by the v2 \`MCP-Optional\` transport module.
- **Sentinel Guard**: The \`Sentinel\` node can use the \`_shadow_model\` to validate LLM tool calls before they are executed, satisfying the "March of Nines."
- **Ghost Orchestration**: This allows tools to be "airdropped" into an existing environment; as long as the function is typed, the schema follows it automatically.
