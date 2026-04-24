# Example: REST API Integration

Demonstrates ultrathink applied to integrating a third-party REST API with retry logic, circuit breaking, and comprehensive error handling.

## The Task
```
Apply The ὅραμα System to: Integrate the OpenWeatherMap API with retry, circuit breaking, and full error handling
Optimize for: reliability
```

## Key Decisions (Stage 5 — Crystallize)
- **Chose**: Exponential backoff over fixed retry (handles rate limiting gracefully)
- **Chose**: Circuit breaker threshold of 5 failures in 60s (industry standard)
- **Removed**: Custom HTTP client (requests library handles this cleanly)
- **Removed**: Complex caching layer (not needed for weather data; changes frequently)

## Inevitability
Any production API client must handle: rate limiting (429), auth failure (401),
server errors (5xx), timeouts, and network failures. This implementation addresses
all five with the minimum code needed — 127 lines.
