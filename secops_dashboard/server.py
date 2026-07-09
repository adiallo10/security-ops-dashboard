"""Flask backend for the Security Ops Mini-Dashboard.

Serves the single-page dashboard and two JSON endpoints:

* ``GET  /api/alerts``  -> aggregated data for the charts
* ``POST /api/explain`` -> plain-English explanation of a selected trend

The Claude API key (if any) stays server-side — the browser only ever talks to
this Flask app, never to Anthropic directly.
"""

from __future__ import annotations

import os

from flask import Flask, jsonify, render_template, request

from secops_dashboard.data import generate_alerts, summarize
from secops_dashboard.explain import explain_trend

# templates/ and static/ live at the project root, one level above this package.
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(
    __name__,
    template_folder=os.path.join(_ROOT, "templates"),
    static_folder=os.path.join(_ROOT, "static"),
)

# Generate the synthetic dataset once at startup (deterministic).
_ALERTS = generate_alerts()
_SUMMARY = summarize(_ALERTS)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/alerts")
def api_alerts():
    return jsonify(_SUMMARY)


@app.route("/api/explain", methods=["POST"])
def api_explain():
    payload = request.get_json(silent=True) or {}
    provider = "anthropic" if os.environ.get("ANTHROPIC_API_KEY") else "local"

    context = {
        "series": payload.get("series", "all"),
        "labels": payload.get("labels", []),
        "values": payload.get("values", []),
        "total": _SUMMARY["total"],
        "severity_counts": _SUMMARY["severity_counts"],
    }
    explanation = explain_trend(context, provider=provider)
    return jsonify({"explanation": explanation, "provider": provider})


if __name__ == "__main__":
    app.run(debug=False)
