from __future__ import annotations

from pathlib import Path
import shutil
import sys
import tempfile

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from evolvekb.gates.engine import validate_repo  # noqa: E402
from evolvekb.ingestion.compiler import compile_markdown  # noqa: E402
from evolvekb.skills.runtime import PlaybookRuntime  # noqa: E402


QUESTION = (
    "The customer opened the item and asks for a refund after 45 days. "
    "What should we do?"
)
POLICY_DOC = "examples/customer_support_refund_policy.md"


def main() -> int:
    repo = REPO
    with tempfile.TemporaryDirectory(prefix="evolvekb-refund-agent-") as temp_dir:
        workspace = Path(temp_dir) / "EvolveKB"
        _copy_repo(repo, workspace)
        print("# Customer Support Refund Agent Demo\n")

        print("1. Load policy document")
        print(f"- source: {POLICY_DOC}")

        print("\n2. Compile grounded claims")
        ingest = compile_markdown(workspace, POLICY_DOC, write=True, proposal=False)
        proposal = compile_markdown(workspace, POLICY_DOC, write=True, proposal=True)
        print(f"- claims: {len(ingest.claims)}")
        print(f"- knowledge_path: {ingest.knowledge_path.relative_to(workspace) if ingest.knowledge_path else 'none'}")
        print(f"- proposal_path: {proposal.proposal_path.relative_to(workspace) if proposal.proposal_path else 'none'}")

        print("\n3. Build / load refund decision playbook")
        runtime = PlaybookRuntime(workspace)
        print("- playbook: refund-decision")

        print("\n4. Retrieve evidence for customer question")
        print(f"- question: {QUESTION}")

        print("\n5. Run playbook steps")
        result = runtime.run(
            intent="refund_decision",
            question=QUESTION,
            settings_arg="settings/reference.yaml",
            write_side_effects=False,
        )
        print(f"- trace_id: {result.trace.id}")
        print(f"- retrieved_knowledge_ids: {', '.join(result.trace.retrieved_knowledge_ids) or 'none'}")

        print("\n6. Produce evidence-backed answer")
        print(result.rendered.rstrip())

        print("\n7. Run gates and evals")
        failed = [item for item in validate_repo(workspace, "settings/evolve.yaml") if not item.passed]
        print(f"- gates: {'PASS' if not failed else 'FAIL'}")

        print("\n8. Show trace id and proposal path")
        print(f"- trace_id: {result.trace.id}")
        print(f"- proposal_path: {proposal.proposal_path.relative_to(workspace) if proposal.proposal_path else 'none'}")
    return 0


def _copy_repo(source: Path, target: Path) -> None:
    shutil.copytree(
        source,
        target,
        ignore=shutil.ignore_patterns(
            ".git",
            ".mypy_cache",
            ".pytest_cache",
            ".ruff_cache",
            "__pycache__",
            "*.egg-info",
            ".venv",
            "build",
            "dist",
            "node_modules",
            "venv",
        ),
    )


if __name__ == "__main__":
    raise SystemExit(main())
