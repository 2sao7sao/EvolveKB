# New-knowledge base (Python)

This repo adapts useful OpenClaw patterns:
- `skills/<name>/SKILL.md` with YAML frontmatter and strict validation
- progressive disclosure (metadata → body → resources)
- safe packaging (reject symlinks)

## Quickstart
```bash
python -m pip install -r requirements.txt
python scripts/validate.py
python scripts/run.py --intent compare_frameworks --question "对比 GraphRAG 和 md-knowledge 的差异"
```

## Skill layout
```
skills/
  compare-frameworks/
    SKILL.md   # kind=playbook, steps=[...]
  normalize-question/
    SKILL.md   # kind=procedure
```

## What you should change next
- Replace deterministic placeholder procedures with your LLM/tool execution.
- Split large skills into references/ scripts/ to keep SKILL.md lean.
