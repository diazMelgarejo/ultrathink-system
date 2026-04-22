# API Reference

## Scripts

### verify_before_done.py

```bash
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

```bash
python capture_lesson.py [OPTIONS]

Options:
  --pattern NAME    Mistake pattern name (skips category selection)
  --quick           Minimal prompts
  --review          Show all existing lessons
  --stats           Show mistake category statistics
  --dir PATH        Project directory (default: ".")
```

### create_task_plan.sh

```bash
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

---

## REST API (`api_server.py`)

The ultrathink system exposes a stateless HTTP API.

```bash
# Start (requires: pip install fastapi uvicorn pydantic)
python api_server.py

# POST /ultrathink
curl -X POST http://localhost:8001/ultrathink \
  -H "Content-Type: application/json" \
  -d '{"task_description": "Build auth system", "optimize_for": "reliability"}'

# GET /health
curl http://localhost:8001/health
```

### Request Body

```json
{
  "task_description": "string (required, max 10000 chars)",
  "optimize_for": "reliability | creativity | speed",
  "model_hint": "haiku | sonnet | opus | fast | balanced | powerful (optional)",
  "context": {},
  "request_id": "uuid (optional)"
}
```

### Response
```json
{
  "request_id": "uuid",
  "status": "accepted",
  "task_id": "uuid",
  "message": "Task accepted for mode2 execution.",
  "mode": "mode1 | mode2 | mode3",
  "elapsed_ms": 0.5
}
```

**Stateless**: no Redis dependency. Durable state owned by Perpetua-Tools (Repo #1).
