"""Security Ops Mini-Dashboard.

A small Flask app that visualizes synthetic security-alert data with severity
heatmaps and trend charts, plus an optional "Explain this trend" feature backed
by the Claude API. All aggregation logic lives in this package so it is
testable independently of the web layer.
"""

__version__ = "1.0.0"
