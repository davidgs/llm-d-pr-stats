## What does this PR do?

<!-- Briefly describe the change and why it's needed. -->

## Type of change

- [ ] New category (`terms/*.json`)
- [ ] Bug fix
- [ ] New feature / CLI flag
- [ ] Documentation only
- [ ] Chart / output format change
- [ ] Other (describe above)

## How was this tested?

<!--
Since pr_keyword_stats.py hits the live GitHub Search API, please show the
actual command + a snippet of output (console log, or a generated CSV/PNG)
rather than just "works on my machine". For a quick check that doesn't
burn through the search rate limit, try a narrow query, e.g.:

  python3 pr_keyword_stats.py --org llm-d --config terms/nvidia.json \
    --out-dir /tmp/test-out --state merged
-->

```
paste relevant command + output here
```

## Checklist

- [ ] I ran the affected script(s) end-to-end at least once (not just a syntax check)
- [ ] I updated `README.md` if this changes CLI flags, output files, or the
      category config schema
- [ ] I updated/added a `terms/*.json` example if this is a new category,
      following the format in `terms/_template.json`
- [ ] No secrets, tokens, or personal GitHub data are included in this diff
      (check any pasted output/CSVs too)

## Related issues

<!-- Closes #123, relates to #456, etc. -->
