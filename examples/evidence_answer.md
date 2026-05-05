# Evidence-backed answer demo

```bash
evolvekb run --intent answer_with_evidence --question "What is execution-first knowledge?"
```

Expected behavior:

- Route to `answer-with-evidence`.
- Retrieve evidence from `kb/knowledge` and `kb/claims`.
- Render evidence references before the final answer section.
