"""Plain-English explanations of a trend in the alert data.

Provider-agnostic, matching the other projects: a deterministic ``"local"``
explainer works offline with zero setup, and an optional ``"anthropic"``
provider produces a richer summary when ``ANTHROPIC_API_KEY`` is configured.
"""

from __future__ import annotations

import os


def explain_trend(context: dict, provider: str = "local") -> str:
    """Explain a selected trend.

    ``context`` is a small dict describing what the user is looking at, e.g.::

        {
            "series": "phishing",
            "labels": ["2026-06-28", ...],
            "values": [3, 5, 41, ...],
            "total": 680,
            "severity_counts": {"low": 340, ...},
        }
    """
    if provider == "anthropic":
        text = _explain_with_anthropic(context)
        if text is not None:
            return text
    return _explain_local(context)


def _explain_local(context: dict) -> str:
    series = context.get("series", "all alerts")
    values = context.get("values", []) or []
    labels = context.get("labels", []) or []

    if not values:
        return f"No data points for {series} in the selected window."

    total = sum(values)
    peak = max(values)
    peak_idx = values.index(peak)
    peak_day = labels[peak_idx] if peak_idx < len(labels) else "the peak day"
    avg = total / len(values)

    if peak >= 2 * max(avg, 1):
        shape = (
            f"There is a clear spike on {peak_day} ({peak} alerts vs. an average "
            f"of {avg:.0f}/day)."
        )
        action = (
            "Investigate what changed around that date — a phishing campaign, a "
            "new detection rule, or a misconfiguration can all cause a surge. "
            "Confirm whether the spike is real activity or alert noise, and "
            "check whether any high/critical items need escalation."
        )
    elif values[-1] > avg:
        shape = f"{series.title()} activity is trending upward, ending above its {avg:.0f}/day average."
        action = "Keep an eye on it; if the climb continues, dig into the top sources and entities."
    else:
        shape = f"{series.title()} activity is steady, averaging about {avg:.0f} alerts/day with no major spikes."
        action = "No urgent action — continue routine monitoring."

    return f"{shape} {action}"


def _explain_with_anthropic(context: dict) -> str | None:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None
    try:
        import anthropic  # optional dependency
    except ImportError:
        return None

    series = context.get("series", "all alerts")
    pairs = list(zip(context.get("labels", []), context.get("values", [])))
    series_text = ", ".join(f"{d}={v}" for d, v in pairs)
    prompt = (
        "You are a SOC analyst assistant. In 2-3 plain-English sentences, "
        "explain this security-alert trend to a non-technical manager and "
        "suggest what to check next. Do not invent details.\n\n"
        f"Metric: {series} alerts per day\n"
        f"Series: {series_text}\n"
        f"Total alerts in window: {context.get('total', 'n/a')}\n"
        f"Severity breakdown: {context.get('severity_counts', {})}\n"
    )
    try:
        client = anthropic.Anthropic(api_key=api_key)
        message = client.messages.create(
            model="claude-3-5-haiku-latest",
            max_tokens=250,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception:  # network/auth errors -> graceful fallback
        return None
