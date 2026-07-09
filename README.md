# Security Ops Mini-Dashboard

A lightweight Flask dashboard that turns synthetic security-alert data into
**severity heatmaps, trend charts, and plain-English explanations**. Click
"Explain this trend" and the backend summarizes what a spike or pattern likely
means and what to check next — making the data readable for stakeholders, not
just analysts.

Everything runs offline with synthetic data. The AI explanation is optional:
with no API key it uses a deterministic local explainer; with a Claude
(Anthropic) key it produces a richer natural-language summary.

## Why I built it

Dashboards show *what* happened but rarely *what it means*. This one adds a
thin AI layer that turns a chart into a short, human takeaway — useful when
briefing a non-technical team or a manager who just wants the bottom line.

## Features

- **Synthetic data generator** — deterministic, realistic-looking alerts across
  five SIEM/EDR sources and six categories, with an injected phishing spike so
  there's a real trend to explain.
- **Severity summary tiles** — total plus low/medium/high/critical counts.
- **Trend chart** — alerts per day, switchable between "all alerts" and any
  single category (Chart.js line chart).
- **Top-categories bar chart**.
- **Activity heatmap** — weekday × hour grid showing when alerts fire.
- **"Explain this trend"** — `POST /api/explain` returns a plain-English
  summary + suggested next step. Local by default; Claude if configured.
- **Key stays server-side** — the browser only talks to Flask, never to
  Anthropic directly.

## Architecture

```
Browser (Chart.js)  ──GET /api/alerts──►  Flask  ──►  secops_dashboard.data
        │                                   │
        └──POST /api/explain───────────────►└──►  secops_dashboard.explain ──► (optional) Claude API
```

All aggregation logic lives in `secops_dashboard/` and is unit-tested
independently of the web layer.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e .            # core (Flask)
pip install -e ".[ai]"      # optional Claude explanations

# optional: use the Claude API for explanations
export ANTHROPIC_API_KEY="sk-ant-..."   # never commit this

flask --app secops_dashboard.server run
# open http://127.0.0.1:5000
```

Generate a standalone JSON dataset (for demos or other tools):

```bash
python -m scripts.generate_data sample_data/alerts.json
```

## Testing

```bash
python -m unittest discover -s tests -v
```

Tests cover deterministic generation, that every aggregation sums back to the
total, the injected spike, and the trend explainer's spike/steady/empty paths.

## Project layout

```
secops_dashboard/
  data.py      # synthetic data + aggregations (severity, trend, heatmap)
  explain.py   # local + optional Claude trend explanations
  server.py    # Flask app: /, /api/alerts, /api/explain
templates/
  index.html   # dashboard page
static/
  app.js       # Chart.js rendering + explain button
  style.css    # dark, responsive UI
scripts/
  generate_data.py
tests/
```

## Notes on safety

- All data is **synthetic/mock** — no real alerts or PII.
- The Claude API key stays server-side via the Flask proxy; it is never sent to
  the browser.

## License

MIT — see [LICENSE](LICENSE).
