from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from evolvekb.assets.frontmatter import parse_frontmatter
from evolvekb.assets.hashing import file_hash, stable_hash
from evolvekb.wiki import append_kb_log, rebuild_kb_index


def create_write_file_proposal(
    repo: Path,
    title: str,
    proposal_type: str,
    path: str,
    content: str,
    rationale: str,
    evidence_ids: list[str] | None = None,
) -> Path:
    now = datetime.now(timezone.utc)
    proposal_id = f"prop_{now.strftime('%Y%m%dT%H%M%SZ')}_{stable_hash({'title': title, 'path': path})[:8]}"
    target = repo / path
    before_hash = file_hash(target) if target.exists() else ""
    fm = {
        "schema_version": 2,
        "id": proposal_id,
        "title": title,
        "proposal_type": proposal_type,
        "status": "pending_review",
        "rationale": rationale,
        "impacted_assets": [path],
        "before_hashes": {path: before_hash},
        "after_patches": [{"op": "write_file", "path": path, "content": content}],
        "evidence_ids": evidence_ids or [],
        "eval_results": {},
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
    body = [
        f"# Proposal: {title}",
        "",
        "## Rationale",
        rationale,
        "",
        "## Proposed Changes",
        f"- Write `{path}`",
        "",
        "## Rollback Plan",
        "- Restore the pre-apply backup stored under `kb/proposals/applied/`.",
    ]
    out = repo / "kb" / "proposals" / f"{proposal_id}.md"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        "---\n"
        + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
        + "\n---\n\n"
        + "\n".join(body)
        + "\n",
        encoding="utf-8",
    )
    append_kb_log(repo, "proposal", f"Created {proposal_id}")
    return out


def apply_proposal(repo: Path, proposal_id_or_path: str) -> Path:
    path = _resolve_proposal(repo, proposal_id_or_path)
    doc = parse_frontmatter(path.read_text(encoding="utf-8"))
    fm = dict(doc.frontmatter)
    if fm.get("status") not in {"pending_review", "approved"}:
        raise ValueError(f"Proposal {fm.get('id')} is not applyable: {fm.get('status')}")

    backup_dir = repo / "kb" / "proposals" / "applied" / str(fm["id"])
    backup_dir.mkdir(parents=True, exist_ok=True)
    manifest: dict[str, Any] = {"proposal": path.name, "files": []}
    for patch in fm.get("after_patches") or []:
        if patch.get("op") != "write_file":
            raise ValueError(f"Unsupported patch op: {patch.get('op')}")
        rel = Path(str(patch["path"]))
        target = repo / rel
        backup_path = backup_dir / rel
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        existed = target.exists()
        if existed:
            backup_path.write_bytes(target.read_bytes())
        manifest["files"].append({"path": str(rel), "backup": str(backup_path.relative_to(repo)), "existed": existed})
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(patch.get("content", "")), encoding="utf-8")

    (backup_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    _update_proposal_status(path, "applied")
    rebuild_kb_index(repo)
    append_kb_log(repo, "proposal", f"Applied {fm['id']}")
    return backup_dir / "manifest.json"


def rollback_proposal(repo: Path, proposal_id: str) -> None:
    backup_dir = repo / "kb" / "proposals" / "applied" / proposal_id
    manifest_path = backup_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"No applied manifest for proposal: {proposal_id}")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest.get("files") or []:
        target = repo / item["path"]
        backup = repo / item["backup"]
        if item.get("existed"):
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(backup.read_bytes())
        elif target.exists():
            target.unlink()
    proposal_path = _resolve_proposal(repo, proposal_id)
    _update_proposal_status(proposal_path, "rolled_back")
    rebuild_kb_index(repo)
    append_kb_log(repo, "proposal", f"Rolled back {proposal_id}")


def list_proposals(repo: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for path in sorted((repo / "kb" / "proposals").glob("*.md")):
        doc = parse_frontmatter(path.read_text(encoding="utf-8"))
        fm = doc.frontmatter
        rows.append(
            {
                "id": fm.get("id"),
                "title": fm.get("title"),
                "status": fm.get("status"),
                "path": str(path.relative_to(repo)),
            }
        )
    return rows


def _resolve_proposal(repo: Path, proposal_id_or_path: str) -> Path:
    raw = Path(proposal_id_or_path)
    candidates = [
        raw if raw.is_absolute() else repo / raw,
        repo / "kb" / "proposals" / f"{proposal_id_or_path}.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(f"Proposal not found: {proposal_id_or_path}")


def _update_proposal_status(path: Path, status: str) -> None:
    doc = parse_frontmatter(path.read_text(encoding="utf-8"))
    fm = dict(doc.frontmatter)
    fm["status"] = status
    if status == "applied":
        fm["reviewed_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    path.write_text(
        "---\n"
        + yaml.safe_dump(fm, sort_keys=False, allow_unicode=True).strip()
        + "\n---\n"
        + doc.body,
        encoding="utf-8",
    )
