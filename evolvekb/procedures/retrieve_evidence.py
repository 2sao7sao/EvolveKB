from __future__ import annotations

from pathlib import Path
from typing import Any

from evolvekb.core.models import SkillAsset
from evolvekb.retrieval.registry import get_retriever


def run(
    *,
    repo: Path,
    skill: SkillAsset,
    env: dict[str, Any],
    args: dict[str, Any],
) -> dict[str, Any]:
    query = str(args.get("query") or "")
    limit = int(args.get("limit") or 5)
    settings = env.get("settings") if isinstance(env.get("settings"), dict) else {}
    retrieval_settings = settings.get("retrieval") if isinstance(settings.get("retrieval"), dict) else {}
    retriever_name = str(args.get("retriever") or retrieval_settings.get("default_mode") or "keyword")
    pack = get_retriever(retriever_name).retrieve(repo, query, limit=limit)
    data = pack.model_dump(mode="json")
    data["evidence"] = data["items"]
    return data
