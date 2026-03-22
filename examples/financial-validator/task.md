# Task: Build Financial Data Validator
**Optimize for**: reliability
**Date**: 2026-03-20

## Goal
Build a production-ready validator for LSEG equity market data that catches 95% of data quality issues.

## Constraints
- Technical: Real-time data must be < 15 seconds old; after-hours < 24h old
- Business: Must integrate with existing api-health-checker skill
- Compliance: No PII in error messages; logs are retained 90 days

## Non-Goals
- ML-based anomaly detection (future v2)
- Options or futures data (equities only)
- Historical data backtesting

## Implementation Plan
- [x] Review existing LSEG connector docs
- [x] Design validator modules
- [x] Refine to single function
- [x] Write 15 unit tests (TDD)
- [x] Implement validate_equity_data()
- [x] Test with MSFT, AAPL, NVDA data
- [x] Document assumptions and simplifications
