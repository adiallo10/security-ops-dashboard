"""Generate a synthetic alerts JSON file for offline/demo use.

Usage:
    python -m scripts.generate_data            # writes sample_data/alerts.json
    python -m scripts.generate_data out.json
"""

from __future__ import annotations

import sys

from secops_dashboard.data import generate_alerts, save_alerts


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    out = argv[0] if argv else "sample_data/alerts.json"
    alerts = generate_alerts()
    save_alerts(alerts, out)
    print(f"Wrote {len(alerts)} synthetic alerts to {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
