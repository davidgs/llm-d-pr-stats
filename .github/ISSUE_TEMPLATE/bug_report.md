---
name: Bug report
about: Something isn't working as expected
title: "[Bug] "
labels: bug
assignees: ''
---

## Describe the bug

A clear, concise description of what went wrong.

## Command run

```bash
# e.g.
python3 pr_keyword_stats.py --org llm-d --config terms/nvidia.json --out-dir ./out
```

## Expected behavior

What you expected to happen.

## Actual behavior

What actually happened. Include the full console output/traceback if
possible (redact any tokens/usernames you don't want shared):

```
paste output here
```

## Category config (if relevant)

```json
paste the contents of the terms/*.json file you used, if relevant
```

## Environment

- OS:
- Python version (`python3 --version`):
- `gh` version (`gh --version`):
- `gh auth status` output (redact any sensitive info):

## Additional context

Anything else that might help — e.g. does it happen for every category/org,
or only a specific one? Does `--state merged` avoid it? Etc.
