"""Tests for the synthetic data generation and aggregations."""

import unittest

from secops_dashboard.data import (
    CATEGORIES,
    SEVERITIES,
    generate_alerts,
    heatmap_by_hour,
    severity_counts,
    summarize,
    top_categories,
    trend_by_day,
)


class DataTests(unittest.TestCase):
    def setUp(self):
        self.alerts = generate_alerts(count=300, days=14, seed=7)

    def test_generation_is_deterministic(self):
        a = generate_alerts(count=100, seed=1)
        b = generate_alerts(count=100, seed=1)
        self.assertEqual([x.id for x in a], [y.id for y in b])
        self.assertEqual(a[0].timestamp, b[0].timestamp)

    def test_alerts_sorted_by_time(self):
        times = [a.timestamp for a in self.alerts]
        self.assertEqual(times, sorted(times))

    def test_severity_counts_sum_to_total(self):
        counts = severity_counts(self.alerts)
        self.assertEqual(sum(counts.values()), len(self.alerts))
        self.assertEqual(set(counts.keys()), set(SEVERITIES))

    def test_trend_totals_match(self):
        trend = trend_by_day(self.alerts)
        self.assertEqual(sum(trend["total"]), len(self.alerts))
        self.assertEqual(len(trend["labels"]), len(trend["total"]))
        for cat in CATEGORIES:
            self.assertEqual(len(trend["by_category"][cat]), len(trend["labels"]))

    def test_heatmap_covers_full_grid(self):
        grid = heatmap_by_hour(self.alerts)
        self.assertEqual(len(grid), 7 * 24)
        self.assertEqual(sum(cell["count"] for cell in grid), len(self.alerts))

    def test_phishing_spike_is_present(self):
        # The generator injects a phishing spike; it should be the top category.
        top = top_categories(self.alerts)
        self.assertEqual(top[0]["category"], "phishing")

    def test_summarize_bundle(self):
        summary = summarize(self.alerts)
        self.assertEqual(summary["total"], len(self.alerts))
        self.assertIn("severity_counts", summary)
        self.assertIn("trend", summary)
        self.assertIn("heatmap", summary)
        self.assertIn("top_categories", summary)


if __name__ == "__main__":
    unittest.main()
