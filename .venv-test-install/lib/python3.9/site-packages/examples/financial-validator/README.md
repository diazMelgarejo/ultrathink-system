# Example: Financial Data Validator

Demonstrates ultrathink applied to building a production-ready LSEG equity data validator.

## The Task
```
Apply ultrathink system to: Build a financial data validator for LSEG market data
Optimize for: reliability
```

## ultrathink Execution Trace

**Stage 1 — Context Immersion**
- Reviewed LSEG connector integration docs
- Identified constraints: real-time < 15s, after-hours < 24h
- Found existing `api-health-checker` skill to compose with
- Discovered naming convention: `validate_X_data()` returning `PASS/WARNING/FAIL`

**Stage 2 — Visionary Architecture**
- Module 1: DataFreshnessValidator (age_seconds calculation)
- Module 2: RequiredFieldsChecker (price, volume, symbol)
- Module 3: PriceSanityValidator (52w range, > 0)
- Module 4: LiquidityAnalyzer (volume thresholds)
- Interface: `validate_equity_data(data: dict) -> ValidationReport`

**Stage 3 — Ruthless Refinement**
- ✗ Removed: Complex rating normalization (not essential for v1)
- ✗ Removed: Abstract validator classes (overkill for 4 checks)
- ✓ Collapsed to: single `validate_equity_data()` function, < 150 lines
- Elegance score improved from 0.65 → 0.87

**Stage 4 — Masterful Execution**
- TDD: wrote 15 tests before implementation
- All tests pass; tested with MSFT, AAPL, NVDA real data
- Edge cases handled: missing fields, stale data, zero prices

**Stage 5 — Crystallize the Vision**
- Assumptions: market hours 9:30–16:00 ET, real-time threshold 15s
- Simplifications: removed ML anomaly detection (overkill), single function over classes
- Inevitability: 4 checks + structured result = simplest design that works

## Run the Example
```bash
python output/validate_financial_data.py
python output/test_validate_financial_data.py
```
