# Tests

## Run All Tests
```bash
pytest tests/ -v
```

## Run Specific Suites
```bash
pytest tests/test_bin.skills.py -v   # Package integrity + content quality
pytest tests/test_multi_agent.py -v    # Multi-agent structure + config
pytest tests/test_orchestrator.py -v   # Core types + orchestrator logic
```

## Requirements
```bash
pip install pytest
```
No external services needed — all tests use file system and Python stdlib only.

## CI
See `.github/workflows/test.yml` for automated test runs on every push.
