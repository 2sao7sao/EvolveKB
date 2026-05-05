#!/usr/bin/env python3
"""Legacy wrapper for packaging skills into a .kb zip."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evolvekb.package_kb import main, package_kb

__all__ = ["package_kb"]


if __name__ == "__main__":
    raise SystemExit(main())
