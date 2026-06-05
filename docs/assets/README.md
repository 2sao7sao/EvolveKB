# README Asset Provenance

## `evolvekb-demo-terminal.svg`

This image is a static terminal-style SVG used in the README first viewport. It
represents the current shape of:

```bash
python -m evolvekb.cli demo
```

The source of truth is the CLI output, not the SVG text. Refresh the image when
the demo headings, metric names, or metric values change.

## Refresh Checklist

1. Run `python -m evolvekb.cli demo`.
2. Confirm the output still passes and prints metric numerator/denominator pairs.
3. Update `docs/assets/evolvekb-demo-terminal.svg` to match the visible output.
4. Keep the image static and credential-free.
5. Re-run `python -m pytest -q` and `python -m evolvekb.cli validate --settings settings/evolve.yaml`.

Do not include private paths, API keys, customer traces, or proprietary document
content in README imagery.
