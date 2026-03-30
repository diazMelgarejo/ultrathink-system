# API Reference

## Scripts

### verify_before_done.py
```
python verify_before_done.py [OPTIONS]

Options:
  --task NAME       Task name for the report (default: "Unnamed Task")
  --dir PATH        Project directory to verify (default: ".")
  --no-interact     Skip interactive staff engineer check
  --check TYPE      Run specific check: all|tests|lint|debug|plan|se

Exit codes: 0 = PASS, 1 = FAIL
Output: tasks/verification-report.json
```

### capture_lesson.py
```
python capture_lesson.py [OPTIONS]

Options:
  --pattern NAME    Mistake pattern name (skips category selection)
  --quick           Minimal prompts
  --review          Show all existing lessons
  --stats           Show mistake category statistics
  --dir PATH        Project directory (default: ".")
```

### create_task_plan.sh
```
./create_task_plan.sh [TASK_NAME] [OPTIONS]

Options:
  --optimize TYPE   reliability|creativity|speed (default: reliability)
  --dir PATH        Project directory (default: ".")
  --interactive     Guided prompt mode

Creates: tasks/todo.md, tasks/lessons.md (if not exists)
```

## MCP Tools (Multi-Agent)

### ultrathink_solve
```json
{
  "task": "string (required)",
  "optimize_for": "reliability|creativity|speed",
  "context": {}
}
→ { "task_id": "uuid", "status": "started" }
```

### ultrathink_delegate
```json
{
  "stage": "context|architecture|refinement|execution|verification|crystallization",
  "task_id": "uuid",
  "input": {}
}
→ { "delegated_to": "agent-id", "status": "queued" }
```

### ultrathink_status
```json
{ "task_id": "uuid" }
→ TaskState object
```

### ultrathink_lessons
```json
{ "domain": "optional filter", "limit": 10 }
→ { "lessons": [...], "total": N }
```

## HTTP Backup Bridge

### POST /ultrathink
```json
{
  "task_description": "string (required)",
  "reasoning_depth": "standard|deep|ultra (optional)",
  "optimize_for": "reliability|creativity|speed (optional)",
  "task_type": "planning|analysis|code|research",
  "context": "optional background context",
  "max_tokens": 4000,
  "temperature": 0.7,
  "model_hint": "optional model override"
}
```

If neither `reasoning_depth` nor `optimize_for` is provided, the legacy HTTP
default remains `reasoning_depth="standard"` for compatibility with direct HTTP
callers.

Response:

```json
{
  "status": "success|error",
  "result": "string",
  "reasoning_depth": "standard|deep|ultra",
  "model_used": "string",
  "execution_time_ms": 12,
  "metadata": {
    "prompt_chars": 1234,
    "bridge_mode": "http_backup",
    "primary_contract": "mcp",
    "mapped_optimize_for": "reliability",
    "mapping_source": "reasoning_depth|optimize_for|default",
    "model_hint_used": false,
    "endpoint_used": "redacted"
  }
}
```

### GET /health
```json
{
  "status": "ok",
  "version": "0.9.9.0",
  "ollama_primary_reachable": true,
  "ollama_fallback_reachable": true,
  "models": {
    "default": "qwen3.5:35b-a3b-q4_K_M",
    "fast": "qwen3:8b-instruct",
    "code": "qwen3-coder:14b"
  },
  "bridge_mode": "http_backup",
  "primary_contract": "mcp",
  "http_endpoint": "/ultrathink",
  "mapping": {
    "reliability": "ultra",
    "creativity": "deep",
    "speed": "standard"
  }
}
```

### Contract Mapping

| MCP `optimize_for` | HTTP `reasoning_depth` |
|---|---|
| `reliability` | `ultra` |
| `creativity` | `deep` |
| `speed` | `standard` |

## Data Types

### TaskState
```typescript
{
  task_id: string
  task_description: string
  optimize_for: "reliability" | "creativity" | "speed"
  current_stage: "context_immersion" | "architecture" | "refinement" | "execution" | "verification" | "crystallization" | "done"
  iteration_count: number
  elegance_score: number (0.0–1.0)
  stage_outputs: Record<string, any>
  lessons_learned: Lesson[]
}
```

### ValidationReport
```typescript
{
  symbol: string
  status: "PASS" | "WARNING" | "FAIL"
  checks: ValidationCheck[]
  timestamp: string
}
```
