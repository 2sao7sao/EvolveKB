from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Sequence

from evolvekb.assets.registry import AssetRegistry
from evolvekb.gates.engine import print_validation, validate_repo
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
