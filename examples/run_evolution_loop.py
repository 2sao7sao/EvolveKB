from __future__ import annotations

from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from evolvekb.demo import format_demo_report, run_flagship_demo  # noqa: E402


def main() -> None:
    report = run_flagship_demo(ROOT)
    print(format_demo_report(report), end="")
    if not report.passed:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
