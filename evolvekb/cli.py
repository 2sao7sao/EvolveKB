from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evolvekb.assets.registry import AssetRegistry
from evolvekb.demo import (
    DEFAULT_DEMO_DOC,
    DEFAULT_DEMO_SETTINGS,
    format_demo_report,
    run_flagship_demo,
)
from evolvekb.evals.runner import run_evals
from evolvekb.evolution.proposal import apply_proposal, create_write_file_proposal, list_proposals, rollback_proposal
from evolvekb.gates.engine import print_validation, validate_repo
from evolvekb.ingestion.compiler import compile_markdown
from evolvekb.retrieval.keyword import evidence_pack
from evolvekb.skills.registry import SkillRegistry
from evolvekb.skills.runtime import PlaybookRuntime
from evolvekb.wiki import append_kb_log, lint_kb, rebuild_kb_index


def _repo() -> Path:
    return Path.cwd()


def cmd_validate(args: argparse.Namespace) -> int:
    try:
        return print_validation(validate_repo(_repo(), args.settings))
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}")
        return 1


def cmd_run(args: argparse.Namespace) -> int:
    try:
        result = PlaybookRuntime(_repo()).run(
            intent=args.intent,
            question=args.question,
            doc=args.doc,
            settings_arg=args.settings,
            write_side_effects=not args.no_side_effects,
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print(
        f"[settings] knowledge_mode={result.settings.knowledge_mode} "
        f"gate_level={result.settings.gate_level} auto_evolve={result.settings.auto_evolve}"
    )
    if result.proposal_path:
        print(f"[proposal] {result.proposal_path}")
    print(result.rendered)
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    try:
        result = compile_markdown(_repo(), args.doc, write=True, proposal=args.proposal)
    except Exception as exc:
        print(str(exc))
        return 1
    print(f"[source] {result.source.id}")
    print(f"[chunks] {len(result.chunks)}")
    print(f"[claims] {len(result.claims)}")
    print(f"[concepts] {len(result.concepts)}")
    if result.knowledge_path:
        print(f"[knowledge] {result.knowledge_path}")
    if result.proposal_path:
        print(f"[proposal] {result.proposal_path}")
    return 0


def cmd_query(args: argparse.Namespace) -> int:
    pack = evidence_pack(_repo(), args.query, limit=args.limit)
    if args.json:
        print(json.dumps(pack, ensure_ascii=False, indent=2))
        return 0
    print(f"# Evidence for: {args.query}\n")
    if not pack["evidence"]:
        print("- no evidence found")
        return 1 if args.require_evidence else 0
    for item in pack["evidence"]:
        print(f"- ({item['score']:.2f}) `{item['name']}` from {item['source_ref']}: {item['text']}")
    return 0


def cmd_skills_list(args: argparse.Namespace) -> int:
    registry = SkillRegistry.load(_repo())
    for skill in registry.list():
        print(f"{skill.name}\t{skill.kind}\t{skill.intent or '-'}\t{skill.version}")
    return 0


def cmd_skills_inspect(args: argparse.Namespace) -> int:
    try:
        skill = SkillRegistry.load(_repo()).inspect(args.name)
    except KeyError as exc:
        print(str(exc))
        return 1
    payload = {
        "name": skill.name,
        "description": skill.description,
        "kind": skill.kind,
        "intent": skill.intent,
        "version": skill.version,
        "allowed_tools": skill.allowed_tools,
        "inputs_schema": skill.inputs_schema,
        "outputs_schema": skill.outputs_schema,
        "steps": skill.steps,
        "preconditions": skill.preconditions,
        "postconditions": skill.postconditions,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_kb_index(args: argparse.Namespace) -> int:
    path = rebuild_kb_index(_repo())
    print(f"[index] {path}")
    return 0


def cmd_kb_lint(args: argparse.Namespace) -> int:
    issues = lint_kb(_repo(), gate_level=args.gate_level)
    if not issues:
        print("KB LINT PASSED")
        append_kb_log(_repo(), "lint", "KB lint passed")
        return 0
    print("KB LINT FAILED:")
    for issue in issues:
        print(f"- [{issue.code}] {issue.path}: {issue.message}")
    append_kb_log(_repo(), "lint", f"KB lint found {len(issues)} issue(s)")
    return 1


def cmd_kb_log(args: argparse.Namespace) -> int:
    path = append_kb_log(_repo(), args.event_type, args.message)
    print(f"[log] {path}")
    return 0


def cmd_kb_validate(args: argparse.Namespace) -> int:
    registry = AssetRegistry.load(_repo())
    failed = [r for r in registry.validation_results(gate_level=args.gate_level) if not r.passed]
    kb_failed = [r for r in failed if r.gate_id in {"asset_load", "asset_unique_id", "usage_reference_resolution", "usage_playbook_resolution"}]
    if kb_failed:
        print("KB VALIDATION FAILED:")
        for result in kb_failed:
            print(f"- {result.message}")
        return 1
    print("KB VALIDATION PASSED")
    return 0


def cmd_skill_validate(args: argparse.Namespace) -> int:
    registry = AssetRegistry.load(_repo())
    failed = [r for r in registry.validation_results(gate_level=args.gate_level) if not r.passed]
    skill_failed = [r for r in failed if r.gate_id in {"asset_load", "playbook_orchestration", "procedure_contract"}]
    if skill_failed:
        print("VALIDATION FAILED:")
        for result in skill_failed:
            print(f"- {result.message}")
        return 1
    print(f"VALIDATION PASSED: {len(registry.skills)} skills")
    return 0


def cmd_proposal_list(args: argparse.Namespace) -> int:
    rows = list_proposals(_repo())
    if not rows:
        print("No proposals found")
        return 0
    for row in rows:
        print(f"{row['id']}\t{row['status']}\t{row['path']}\t{row['title']}")
    return 0


def cmd_proposal_create(args: argparse.Namespace) -> int:
    content = Path(args.content_file).read_text(encoding="utf-8")
    path = create_write_file_proposal(
        repo=_repo(),
        title=args.title,
        proposal_type=args.type,
        path=args.path,
        content=content,
        rationale=args.rationale,
        evidence_ids=args.evidence_id or [],
    )
    print(f"[proposal] {path}")
    return 0


def cmd_proposal_apply(args: argparse.Namespace) -> int:
    try:
        manifest = apply_proposal(_repo(), args.proposal)
    except Exception as exc:
        print(str(exc))
        return 1
    print(f"[applied] {manifest}")
    return 0


def cmd_proposal_rollback(args: argparse.Namespace) -> int:
    try:
        rollback_proposal(_repo(), args.proposal_id)
    except Exception as exc:
        print(str(exc))
        return 1
    print(f"[rolled_back] {args.proposal_id}")
    return 0


def cmd_eval_run(args: argparse.Namespace) -> int:
    results = run_evals(_repo(), args.patterns)
    failed = [result for result in results if not result.passed]
    for result in results:
        status = "PASS" if result.passed else "FAIL"
        print(f"{status}\t{result.id}\t{result.category}\t{result.message}")
    return 1 if failed else 0


def cmd_evolve_doc(args: argparse.Namespace) -> int:
    try:
        result = compile_markdown(_repo(), args.doc, write=True, proposal=True)
        validation_results = validate_repo(_repo(), args.settings)
        failed = [item for item in validation_results if not item.passed]
        eval_results = run_evals(_repo(), args.eval) if args.eval else []
    except Exception as exc:
        print(str(exc))
        return 1
    print(f"[proposal] {result.proposal_path}")
    print(f"[gates] {'passed' if not failed else 'failed'}")
    for item in failed:
        print(f"- [{item.gate_id}] {item.message}")
    for item in eval_results:
        status = "PASS" if item.passed else "FAIL"
        print(f"[eval] {status} {item.id}: {item.message}")
    return 1 if failed or any(not item.passed for item in eval_results) else 0


def cmd_demo(args: argparse.Namespace) -> int:
    try:
        report = run_flagship_demo(
            _repo(),
            doc=args.doc,
            settings=args.settings,
            eval_patterns=args.eval_patterns,
        )
    except Exception as exc:
        print(str(exc))
        return 1
    print(format_demo_report(report), end="")
    return 0 if report.passed else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="evolvekb")
    sub = parser.add_subparsers(dest="command", required=True)

    validate = sub.add_parser("validate")
    validate.add_argument("--settings", default=None)
    validate.set_defaults(func=cmd_validate)

    run = sub.add_parser("run")
    run.add_argument("--intent", required=True)
    run.add_argument("--question", default="")
    run.add_argument("--doc", default=None)
    run.add_argument("--settings", default=None)
    run.add_argument("--no-side-effects", action="store_true")
    run.set_defaults(func=cmd_run)

    ingest = sub.add_parser("ingest")
    ingest.add_argument("doc")
    ingest.add_argument("--proposal", action="store_true")
    ingest.set_defaults(func=cmd_ingest)

    query = sub.add_parser("query")
    query.add_argument("query")
    query.add_argument("--limit", type=int, default=5)
    query.add_argument("--json", action="store_true")
    query.add_argument("--require-evidence", action="store_true")
    query.set_defaults(func=cmd_query)

    skills = sub.add_parser("skills")
    skills_sub = skills.add_subparsers(dest="skills_command", required=True)
    skills_list = skills_sub.add_parser("list")
    skills_list.set_defaults(func=cmd_skills_list)
    skills_inspect = skills_sub.add_parser("inspect")
    skills_inspect.add_argument("name")
    skills_inspect.set_defaults(func=cmd_skills_inspect)

    kb = sub.add_parser("kb")
    kb_sub = kb.add_subparsers(dest="kb_command", required=True)
    kb_index = kb_sub.add_parser("index")
    kb_index.set_defaults(func=cmd_kb_index)
    kb_lint = kb_sub.add_parser("lint")
    kb_lint.add_argument("--gate-level", type=int, default=2)
    kb_lint.set_defaults(func=cmd_kb_lint)
    kb_log = kb_sub.add_parser("log")
    kb_log.add_argument("event_type")
    kb_log.add_argument("message")
    kb_log.set_defaults(func=cmd_kb_log)

    proposal = sub.add_parser("proposal")
    proposal_sub = proposal.add_subparsers(dest="proposal_command", required=True)
    proposal_list = proposal_sub.add_parser("list")
    proposal_list.set_defaults(func=cmd_proposal_list)
    proposal_create = proposal_sub.add_parser("create")
    proposal_create.add_argument("--title", required=True)
    proposal_create.add_argument("--type", default="knowledge_update")
    proposal_create.add_argument("--path", required=True)
    proposal_create.add_argument("--content-file", required=True)
    proposal_create.add_argument("--rationale", required=True)
    proposal_create.add_argument("--evidence-id", action="append")
    proposal_create.set_defaults(func=cmd_proposal_create)
    proposal_apply = proposal_sub.add_parser("apply")
    proposal_apply.add_argument("proposal")
    proposal_apply.set_defaults(func=cmd_proposal_apply)
    proposal_rollback = proposal_sub.add_parser("rollback")
    proposal_rollback.add_argument("proposal_id")
    proposal_rollback.set_defaults(func=cmd_proposal_rollback)

    eval_parser = sub.add_parser("eval")
    eval_sub = eval_parser.add_subparsers(dest="eval_command", required=True)
    eval_run = eval_sub.add_parser("run")
    eval_run.add_argument("patterns", nargs="+")
    eval_run.set_defaults(func=cmd_eval_run)

    evolve = sub.add_parser("evolve")
    evolve_sub = evolve.add_subparsers(dest="evolve_command", required=True)
    evolve_doc = evolve_sub.add_parser("doc")
    evolve_doc.add_argument("doc")
    evolve_doc.add_argument("--settings", default=None)
    evolve_doc.add_argument("--eval", action="append")
    evolve_doc.set_defaults(func=cmd_evolve_doc)

    demo = sub.add_parser("demo")
    demo.add_argument("--doc", default=DEFAULT_DEMO_DOC)
    demo.add_argument("--settings", default=DEFAULT_DEMO_SETTINGS)
    demo.add_argument("--eval", dest="eval_patterns", action="append")
    demo.set_defaults(func=cmd_demo)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


def legacy_run_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--intent", required=True)
    parser.add_argument("--question", default="")
    parser.add_argument("--doc", default=None)
    parser.add_argument("--settings", default=None)
    parser.add_argument("--no-side-effects", action="store_true")
    return cmd_run(parser.parse_args(argv))


def legacy_validate_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--settings", default=None)
    return cmd_validate(parser.parse_args(argv))


def legacy_skill_validate_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-level", type=int, default=1)
    return cmd_skill_validate(parser.parse_args(argv))


def legacy_kb_validate_main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gate-level", type=int, default=1)
    return cmd_kb_validate(parser.parse_args(argv))


if __name__ == "__main__":
    raise SystemExit(main())
