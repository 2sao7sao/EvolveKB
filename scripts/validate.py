#!/usr/bin/env python3
"""Legacy wrapper for `evolvekb validate`."""

from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from evolvekb.cli import legacy_validate_main


if __name__ == "__main__":
    raise SystemExit(legacy_validate_main())
