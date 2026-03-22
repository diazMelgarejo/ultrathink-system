#!/usr/bin/env python3
"""
validate_financial_data.py
Example output from ultrathink Stage 4: Masterful Execution
Built for LSEG equity market data validation.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional
import math


@dataclass
class ValidationCheck:
    name:    str
    status:  str  # PASS | WARNING | FAIL
    message: str
    value:   Optional[float] = None

@dataclass
class ValidationReport:
    symbol:      str
    status:      str  # PASS | WARNING | FAIL (worst of all checks)
    checks:      list[ValidationCheck] = field(default_factory=list)
    timestamp:   str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add(self, check: ValidationCheck):
        self.checks.append(check)
        # Escalate overall status
        if check.status == "FAIL":
            self.status = "FAIL"
        elif check.status == "WARNING" and self.status == "PASS":
            self.status = "WARNING"


def validate_equity_data(data: dict, market_hours: bool = True) -> ValidationReport:
    """
    Validate LSEG equity data. Returns structured PASS/WARNING/FAIL report.

    Args:
        data: Dict with keys: symbol, price, volume, timestamp, high_52w, low_52w
        market_hours: True if current time is within market hours (affects freshness threshold)

    Returns:
        ValidationReport with per-check results

    Assumptions:
        - real-time threshold: 15 seconds (market hours)
        - after-hours threshold: 86400 seconds (24 hours)
        - volume threshold: 100,000 shares
        - price sanity: must be within 52-week range and > 0
    """
    symbol = data.get("symbol", "UNKNOWN")
    report = ValidationReport(symbol=symbol, status="PASS")

    # ── Check 1: Data Freshness ──────────────────────────────────────────────
    ts = data.get("timestamp")
    if ts is None:
        report.add(ValidationCheck("data_freshness", "FAIL", "Missing timestamp"))
    else:
        try:
            data_time = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
            age_seconds = (datetime.now(timezone.utc) - data_time).total_seconds()
            threshold = 15 if market_hours else 86400
            if age_seconds > threshold:
                status = "FAIL" if age_seconds > threshold * 2 else "WARNING"
                report.add(ValidationCheck(
                    "data_freshness", status,
                    f"Data is {age_seconds:.0f}s old (threshold: {threshold}s)",
                    age_seconds
                ))
            else:
                report.add(ValidationCheck("data_freshness", "PASS", f"Fresh ({age_seconds:.1f}s old)", age_seconds))
        except (ValueError, TypeError) as e:
            report.add(ValidationCheck("data_freshness", "FAIL", f"Invalid timestamp: {e}"))

    # ── Check 2: Required Fields ─────────────────────────────────────────────
    required = ["price", "volume", "symbol"]
    missing  = [f for f in required if data.get(f) is None]
    if missing:
        report.add(ValidationCheck("required_fields", "FAIL", f"Missing fields: {', '.join(missing)}"))
    else:
        report.add(ValidationCheck("required_fields", "PASS", "All required fields present"))

    # ── Check 3: Price Sanity ────────────────────────────────────────────────
    price = data.get("price")
    if price is not None:
        if not isinstance(price, (int, float)) or math.isnan(price) or math.isinf(price):
            report.add(ValidationCheck("price_sanity", "FAIL", f"Invalid price type: {price}"))
        elif price <= 0:
            report.add(ValidationCheck("price_sanity", "FAIL", f"Price must be > 0, got {price}", price))
        else:
            high_52w = data.get("high_52w")
            low_52w  = data.get("low_52w")
            if high_52w and price > high_52w * 1.05:
                report.add(ValidationCheck("price_sanity", "WARNING",
                    f"Price {price} exceeds 52w high {high_52w} by >5%", price))
            elif low_52w and price < low_52w * 0.95:
                report.add(ValidationCheck("price_sanity", "WARNING",
                    f"Price {price} below 52w low {low_52w} by >5%", price))
            else:
                report.add(ValidationCheck("price_sanity", "PASS", f"Price {price} within expected range", price))

    # ── Check 4: Volume ──────────────────────────────────────────────────────
    volume = data.get("volume")
    if volume is not None:
        VOLUME_MIN = 100_000
        if not isinstance(volume, (int, float)) or volume < 0:
            report.add(ValidationCheck("volume", "FAIL", f"Invalid volume: {volume}"))
        elif volume < VOLUME_MIN:
            report.add(ValidationCheck("volume", "WARNING",
                f"Low volume {volume:,.0f} (threshold: {VOLUME_MIN:,})", float(volume)))
        else:
            report.add(ValidationCheck("volume", "PASS", f"Volume {volume:,.0f} OK", float(volume)))

    return report


if __name__ == "__main__":
    # Demo with sample data
    sample = {
        "symbol":    "MSFT",
        "price":     415.23,
        "volume":    2_500_000,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "high_52w":  468.35,
        "low_52w":   309.45,
    }
    report = validate_equity_data(sample)
    print(f"\nValidation Report: {report.symbol}")
    print(f"Overall Status:    {report.status}")
    for check in report.checks:
        icon = "✅" if check.status == "PASS" else ("⚠️ " if check.status == "WARNING" else "❌")
        print(f"  {icon} {check.name}: {check.message}")
