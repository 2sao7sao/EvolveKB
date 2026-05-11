from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def run(command: list[str], cwd: Path) -> None:
    print("\n$ " + " ".join(command))
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout.strip())
    if result.stderr:
        print(result.stderr.strip(), file=sys.stderr)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


def main() -> None:
    with tempfile.TemporaryDirectory(prefix="evolvekb-demo-") as temp_dir:
        workspace = Path(temp_dir) / "EvolveKB"
        shutil.copytree(
            ROOT,
            workspace,
            ignore=shutil.ignore_patterns(
                ".git",
                ".pytest_cache",
                "__pycache__",
                "*.egg-info",
                "dist",
                "build",
            ),
        )

        print(f"Demo workspace: {workspace}")
        run(
            [
                sys.executable,
                "-m",
                "evolvekb.cli",
                "evolve",
                "doc",
                "examples/refund_policy.md",
                "--settings",
                "settings/evolve.yaml",
                "--eval",
                "evals/*.yaml",
            ],
            workspace,
        )
        run([sys.executable, "-m", "evolvekb.cli", "proposal", "list"], workspace)


if __name__ == "__main__":
    main()
