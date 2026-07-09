"""Synthetic alert data generation and aggregation.

Everything here is deterministic given a seed, so the dashboard and the tests
see the same numbers. No real or sensitive data is ever used.
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from datetime import datetime, timedelta

SEVERITIES = ["low", "medium", "high", "critical"]

SOURCES = [
    "Microsoft Sentinel",
    "CrowdStrike Falcon",
    "Microsoft 365 Defender",
    "Rapid7 InsightIDR",
    "AWS GuardDuty",
]

CATEGORIES = [
    "phishing",
    "malware",
    "identity",
    "network",
    "data-exfiltration",
    "policy-violation",
]

# Rough relative frequency so the data looks realistic (most alerts are low).
_SEVERITY_WEIGHTS = [0.5, 0.3, 0.15, 0.05]


@dataclass
class Alert:
    id: str
    timestamp: datetime
    severity: str
    source: str
    category: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "source": self.source,
            "category": self.category,
        }


def generate_alerts(
    count: int = 600,
    days: int = 14,
    seed: int = 42,
    end: datetime | None = None,
) -> list[Alert]:
    """Generate ``count`` synthetic alerts spread over the past ``days`` days.

    A mid-window spike in ``phishing`` alerts is injected so the "explain this
    trend" feature has something interesting to describe.
    """
    rng = random.Random(seed)
    end = end or datetime(2026, 7, 6, 12, 0, 0)
    start = end - timedelta(days=days)
    span_seconds = int((end - start).total_seconds())

    alerts: list[Alert] = []
    for i in range(count):
        ts = start + timedelta(seconds=rng.randint(0, span_seconds))
        severity = rng.choices(SEVERITIES, weights=_SEVERITY_WEIGHTS, k=1)[0]
        category = rng.choice(CATEGORIES)
        source = rng.choice(SOURCES)
        alerts.append(
            Alert(
                id=f"ALT-{i:05d}",
                timestamp=ts,
                severity=severity,
                source=source,
                category=category,
            )
        )

    # Inject a phishing spike around day 9-10 to create a visible trend.
    spike_day = start + timedelta(days=9)
    for j in range(80):
        ts = spike_day + timedelta(hours=rng.randint(0, 47), minutes=rng.randint(0, 59))
        severity = rng.choices(["medium", "high", "critical"], weights=[0.4, 0.4, 0.2], k=1)[0]
        alerts.append(
            Alert(
                id=f"ALT-9{j:04d}",
                timestamp=ts,
                severity=severity,
                source=rng.choice(SOURCES),
                category="phishing",
            )
        )

    alerts.sort(key=lambda a: a.timestamp)
    return alerts


def load_alerts(path: str) -> list[Alert]:
    """Load alerts from a JSON file produced by :func:`save_alerts`."""
    with open(path, "r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return [
        Alert(
            id=item["id"],
            timestamp=datetime.fromisoformat(item["timestamp"]),
            severity=item["severity"],
            source=item["source"],
            category=item["category"],
        )
        for item in raw
    ]


def save_alerts(alerts: list[Alert], path: str) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        json.dump([a.to_dict() for a in alerts], handle, indent=2)


# --------------------------------------------------------------------------- #
# Aggregations consumed by the dashboard front-end.
# --------------------------------------------------------------------------- #


def severity_counts(alerts: list[Alert]) -> dict[str, int]:
    """Total alerts per severity level."""
    counts = {level: 0 for level in SEVERITIES}
    for alert in alerts:
        counts[alert.severity] = counts.get(alert.severity, 0) + 1
    return counts


def trend_by_day(alerts: list[Alert]) -> dict[str, list]:
    """Alerts per calendar day, split into a total and a per-category series."""
    days: dict[str, dict[str, int]] = {}
    for alert in alerts:
        key = alert.timestamp.date().isoformat()
        bucket = days.setdefault(key, {"total": 0})
        bucket["total"] += 1
        bucket[alert.category] = bucket.get(alert.category, 0) + 1

    labels = sorted(days.keys())
    return {
        "labels": labels,
        "total": [days[d]["total"] for d in labels],
        "by_category": {
            cat: [days[d].get(cat, 0) for d in labels] for cat in CATEGORIES
        },
    }


def heatmap_by_hour(alerts: list[Alert]) -> list[dict]:
    """Counts bucketed by weekday (0=Mon) and hour of day, for a heatmap grid."""
    grid: dict[tuple[int, int], int] = {}
    for alert in alerts:
        key = (alert.timestamp.weekday(), alert.timestamp.hour)
        grid[key] = grid.get(key, 0) + 1
    return [
        {"weekday": wd, "hour": hr, "count": grid.get((wd, hr), 0)}
        for wd in range(7)
        for hr in range(24)
    ]


def top_categories(alerts: list[Alert], limit: int = 6) -> list[dict]:
    """Categories ranked by alert volume."""
    counts: dict[str, int] = {}
    for alert in alerts:
        counts[alert.category] = counts.get(alert.category, 0) + 1
    ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)
    return [{"category": c, "count": n} for c, n in ranked[:limit]]


def summarize(alerts: list[Alert]) -> dict:
    """Bundle every aggregation the front-end needs into one payload."""
    return {
        "total": len(alerts),
        "severity_counts": severity_counts(alerts),
        "trend": trend_by_day(alerts),
        "heatmap": heatmap_by_hour(alerts),
        "top_categories": top_categories(alerts),
    }
