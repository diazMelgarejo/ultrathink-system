# Tests

## Run All Tests
```bash
pytest tests/ -v
```

## Run Specific Suites
```bash
pytest tests/test_single_agent.py -v   # Package integrity + content quality
pytest tests/test_multi_agent.py -v    # Multi-agent structure + config
pytest tests/test_orchestrator.py -v   # Core types + orchestrator logic
```

## Requirements
```bash
pip install . pytest
```
No external services are required, but the full suite imports the HTTP bridge modules,
so install the package runtime dependencies before running all tests.

## CI
See `.github/workflows/test.yml` for automated test runs on every push.
