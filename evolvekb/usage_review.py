from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from evolvekb.assets.frontmatter import parse_frontmatter
from evolvekb.wiki import append_kb_log


def load_usage(path: Path) -> dict[str, Any]:
    doc = parse_frontmatter(path.read_text(encoding="utf-8"))
    return doc.frontmatter


def generate_usage_review(repo: Path, now: datetime | None = None) -> Path:
    usage_dir = repo / "kb" / "usage"
    report_dir = repo / "outputs" / "reviews"
    report_dir.mkdir(parents=True, exist_ok=True)

    now = now or datetime.now(timezone.utc)
    since = now - timedelta(days=7)
    tbd: list[str] = []
    recent: list[str] = []
    counts: dict[str, int] = {}

    events = repo / "outputs" / "usage" / "events.log"
    if events.exists():
        for line in events.read_text(encoding="utf-8").splitlines():
            try:
                date_s, intent, _mode = line.split("\t")
                dt = datetime.strptime(date_s, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if dt >= since:
                    counts[intent] = counts.get(intent, 0) + 1
            except Exception:
                continue

    if usage_dir.exists():
        for path in sorted(usage_dir.glob("*.md")):
            if path.name == "index.md":
                continue
            fm = load_usage(path)
            if fm.get("pattern") == "TBD":
                tbd.append(path.stem)
            updated = fm.get("updated_at")
            if isinstance(updated, str):
                try:
                    dt = datetime.strptime(updated, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                    if dt >= since:
                        recent.append(path.stem)
                except Exception:
                    pass

            intent = fm.get("intent")
            if fm.get("pattern") == "TBD" and intent in counts and counts[intent] >= 3:
                text = path.read_text(encoding="utf-8")
                path.write_text(text.replace("pattern: TBD", "pattern: required"), encoding="utf-8")

    ts = now.strftime("%Y%m%dT%H%M%SZ")
    out = report_dir / f"usage_review_{ts}.md"
    lines = ["# Weekly Usage Review", "", f"Generated: {now.date()} UTC", ""]
    lines.append("## TBD patterns")
    lines.extend([f"- {item}" for item in tbd] if tbd else ["- none"])
    lines.append("\n## Updated this week")
    lines.extend([f"- {item}" for item in recent] if recent else ["- none"])
    lines.append("\n## Usage frequency (7d)")
    if counts:
        for key, value in sorted(counts.items(), key=lambda x: -x[1]):
            lines.append(f"- {key}: {value}")
    else:
        lines.append("- none")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    append_kb_log(repo, "review", f"Generated usage review {out.name}")
    return out


def main() -> int:
    out = generate_usage_review(Path.cwd())
    print(f"[review] {out}")
    return 0
