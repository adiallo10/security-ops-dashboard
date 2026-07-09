"""Tests for the trend explainer (local provider)."""

import unittest

from secops_dashboard.explain import explain_trend


class ExplainTests(unittest.TestCase):
    def test_detects_spike(self):
        ctx = {
            "series": "phishing",
            "labels": ["d1", "d2", "d3", "d4", "d5"],
            "values": [3, 4, 41, 5, 3],
        }
        text = explain_trend(ctx, provider="local")
        self.assertIn("spike", text.lower())
        self.assertIn("d3", text)

    def test_steady_trend(self):
        ctx = {
            "series": "network",
            "labels": ["d1", "d2", "d3"],
            "values": [10, 11, 9],
        }
        text = explain_trend(ctx, provider="local")
        self.assertIn("steady", text.lower())

    def test_empty_series(self):
        ctx = {"series": "malware", "labels": [], "values": []}
        text = explain_trend(ctx, provider="local")
        self.assertIn("no data", text.lower())

    def test_unknown_provider_falls_back_to_local(self):
        # Without a key/SDK, anthropic provider must fall back gracefully.
        ctx = {"series": "all", "labels": ["d1", "d2"], "values": [5, 6]}
        text = explain_trend(ctx, provider="anthropic")
        self.assertTrue(text)


if __name__ == "__main__":
    unittest.main()
