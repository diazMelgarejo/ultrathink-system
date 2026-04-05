# Task: REST API Integration with Retry & Circuit Breaking
**Optimize for**: reliability

## Goal
Build a resilient API client for OpenWeatherMap that handles all failure modes gracefully.

## Constraints
- Must handle: 429 (rate limit), 401 (auth), 5xx (server error), timeout, network failure
- Retry with exponential backoff
- Circuit breaker: open after 5 failures in 60s
- No external dependencies beyond `requests`

## Implementation Steps
- [x] Context: reviewed existing HTTP client patterns in codebase
- [x] Architecture: WeatherClient + CircuitBreaker + RetryPolicy
- [x] Refinement: collapsed to 2 classes (CircuitBreaker + WeatherClient with retry built in)
- [x] Execution: TDD, 20 tests with mock server
- [x] Verified: all tests pass, circuit breaker opens/closes correctly
