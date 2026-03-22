# Perplexity-Tools Bridge for UltraThink System

## Version 0.9.4.0

### Overview

This document describes the integration between **ultrathink-system** (deep reasoning engine) and **Perplexity-Tools** (top-level orchestrator with cloud routing).

**Architecture:**
- Perplexity-Tools serves as the entry point and orchestrator
- ultrathink-system provides deep reasoning capabilities via local Qwen3 models
- Integration uses HTTP REST API with JSON payloads

### Integration Endpoint

**ultrathink-system exposes:**

```
POST /ultrathink
Content-Type: application/json

{
  "task_description": "string",
  "reasoning_depth": "standard|deep|ultra",
  "task_type": "analysis|code|research|planning",
  "context": "string (optional)",
  "constraints": {
    "max_tokens": 4000,
    "temperature": 0.7
  }
}
```

**Response:**

```json
{
  "status": "success|error",
  "result": "string",
  "reasoning_steps": 150,
  "model_used": "qwen3:30b-a3b-instruct-q4_K_M",
  "execution_time_ms": 2450,
  "metadata": {
    "agents_used": ["analyst", "critic", "synthesizer"],
    "iterations": 3
  }
}
```

### Configuration

**In Perplexity-Tools `.env`:**

```bash
# UltraThink Integration
ULTRATHINK_ENDPOINT=http://localhost:8001/ultrathink
ULTRATHINK_TIMEOUT=120
ULTRATHINK_ENABLED=true
```

**In ultrathink-system `.env`:**

```bash
# API Server
API_PORT=8001
API_HOST=0.0.0.0

# Model Configuration
DEFAULT_MODEL=qwen3:30b-a3b-instruct-q4_K_M
FAST_MODEL=qwen3:8b-instruct
CODE_MODEL=qwen3-coder:14b

# Ollama Endpoints
OLLAMA_MAC_ENDPOINT=http://192.168.1.100:11434
OLLAMA_WINDOWS_ENDPOINT=http://192.168.1.101:11434
```

### Routing Logic from Perplexity-Tools

**When to call ultrathink-system:**

1. **Deep reasoning required:**
   - `reasoning_steps > 200`
   - Complex multi-step analysis
   - Strategic planning

2. **Privacy-critical tasks:**
   - Sensitive business logic
   - Internal data processing
   - No external API calls allowed

3. **Code generation:**
   - Large codebases
   - Architectural decisions
   - Refactoring tasks

**When NOT to call ultrathink:**

- Real-time finance/news (use Perplexity Grok 4.1)
- Quick Q&A (use local Qwen3:8b directly)
- Simple formatting tasks

### Task Flow Example

```python
# In Perplexity-Tools orchestrator.py

if task.requires_deep_reasoning and task.privacy_critical:
    # Route to ultrathink-system
    response = await aiohttp.ClientSession().post(
        f"{ULTRATHINK_ENDPOINT}",
        json={
            "task_description": task.description,
            "reasoning_depth": "ultra",
            "task_type": task.type,
            "constraints": {
                "max_tokens": 8000,
                "temperature": 0.7
            }
        },
        timeout=aiohttp.ClientTimeout(total=120)
    )
    result = await response.json()
    return result["result"]
```

### Fallback Behavior

**If ultrathink-system unavailable:**

1. Perplexity-Tools detects timeout/connection error
2. Logs warning: "UltraThink unavailable, using local Qwen3-30B fallback"
3. Routes task directly to `qwen3:30b-a3b-instruct-q4_K_M` on Dell
4. Continues execution without interruption

### Model Selection Matrix

| Task Type | Perplexity-Tools Action | ultrathink-system Model |
|-----------|------------------------|------------------------|
| Strategic orchestration | Perplexity Claude Sonnet 4.5 → UltraThink | qwen3:30b (Dell) |
| Deep code analysis | UltraThink | qwen3-coder:14b (Dell) |
| Fast reasoning | Local Qwen3:8b | N/A |
| Finance/Real-time | Perplexity Grok 4.1 | N/A |
| Critic review | Local Qwen3:30b | qwen3:30b (critic mode) |

### Idempotent Orchestration

**Perplexity-Tools checks Redis before spawning ultrathink tasks:**

```python
# Check for existing ultrathink task
task_key = f"ultrathink:task:{task_id}"
existing = await redis.get(task_key)

if existing:
    # Reuse existing result
    return json.loads(existing)
else:
    # Create new task
    result = await call_ultrathink(task)
    await redis.setex(task_key, 3600, json.dumps(result))
    return result
```

### Runtime Modes

**Supported configurations:**

1. **LAN Full (default):**
   - Mac M2 + Dell RTX 3080 on same network
   - ultrathink runs on Dell:8001
   - Perplexity-Tools on Mac:8000

2. **Mac Only:**
   - ultrathink and Perplexity-Tools both on Mac
   - Uses Qwen3:8b for ultrathink tasks
   - Dell unavailable

3. **Dell Only:**
   - All components on Windows Dell
   - Full Qwen3:30b capability

4. **MLX/LM Studio:**
   - Alternative to Ollama
   - Same API contract
   - Configure endpoints accordingly

### Error Handling

**Perplexity-Tools must handle:**

```python
try:
    result = await call_ultrathink(task, timeout=120)
except asyncio.TimeoutError:
    logger.warning("UltraThink timeout, using local fallback")
    result = await local_qwen30b_fallback(task)
except aiohttp.ClientError as e:
    logger.error(f"UltraThink connection error: {e}")
    result = await local_qwen30b_fallback(task)
```

### Performance Expectations

**Typical response times:**

- Standard reasoning (50-100 steps): 2-5 seconds
- Deep reasoning (200-500 steps): 10-30 seconds
- Ultra reasoning (1000+ steps): 60-120 seconds

**Resource usage:**

- Dell RTX 3080: 8-9GB VRAM for Qwen3:30b-Q4
- Mac M2: 6-7GB RAM for Qwen3:8b
- Network bandwidth: < 1MB per request

### Testing the Integration

**1. Start ultrathink-system:**

```bash
cd ultrathink-system
python -m uvicorn api_server:app --host 0.0.0.0 --port 8001
```

**2. Test endpoint:**

```bash
curl -X POST http://localhost:8001/ultrathink \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Analyze the trade-offs between microservices and monolithic architecture",
    "reasoning_depth": "deep",
    "task_type": "analysis"
  }'
```

**3. Start Perplexity-Tools:**

```bash
cd Perplexity-Tools
python orchestrator.py
```

**4. Test orchestration:**

```bash
curl -X POST http://localhost:8000/orchestrate \
  -H "Content-Type: application/json" \
  -d '{
    "task_description": "Design a scalable backend architecture",
    "privacy_critical": true
  }'
```

### Security Considerations

**Network security:**

- Use firewall rules to restrict ultrathink endpoint to LAN only
- Consider VPN for remote access
- No authentication required on local network (trusted environment)

**Data privacy:**

- All sensitive tasks routed through ultrathink (local-only)
- No PII or confidential data sent to Perplexity Cloud
- Redis stores task cache locally only

### Monitoring

**Health checks:**

```bash
# UltraThink health
curl http://localhost:8001/health

# Perplexity-Tools health
curl http://localhost:8000/health
```

**Metrics to track:**

- ultrathink response times
- Fallback trigger rate
- Model selection distribution
- Error rates by endpoint

### Version Compatibility

**This integration requires:**

- ultrathink-system >= v0.9.4.0
- Perplexity-Tools >= v0.9.0.0
- Ollama >= 0.1.20 (with Qwen3 support)
- Redis >= 6.0
- Python >= 3.10

### Changelog v0.9.4.0

**Added:**
- `/ultrathink` endpoint specification
- Integration with Perplexity-Tools SKILL.md routing
- Fallback behavior documentation
- Runtime mode descriptions
- Performance benchmarks

**Changed:**
- Aligned model naming with Qwen3:30b-Q4 as default
- Updated configuration examples for dual-machine setup

**Fixed:**
- Clarified idempotent task handling via Redis

---

### Support

For issues with integration:

1. Check both services are running: `curl http://localhost:8001/health`
2. Verify network connectivity between Mac and Dell
3. Review logs in `logs/ultrathink.log` and `logs/orchestrator.log`
4. Confirm Ollama models are pulled: `ollama list`

### Related Documentation

- Perplexity-Tools: `SKILL.md`, `README_v0.9.0.md`
- UltraThink: `docs/ARCHITECTURE.md`, `README.md`
- ECC-tools: (external sub-agent model selection)
