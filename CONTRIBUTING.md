# Contributing to llm-d-pr-stats

Thanks for considering a contribution! This is a small, single-purpose
tool, so the bar is low and the process is simple.

## Ways to contribute

- **Add a category** — copy [`terms/_template.json`](terms/_template.json)
  to `terms/<name>.json` and open a PR. No code changes needed.
- **Report a bug** — open an issue with the command you ran, the error/output
  you saw, and your `gh --version` / `python3 --version`.
- **Improve the code** — see "Ideas for improvement" below for some known
  gaps that would make good first contributions.

## Development setup

```bash
git clone <this repo>
cd llm-d-pr-stats
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
gh auth login   # if you haven't already
```

Run against a small org/category first to sanity-check changes before a
full run (full runs against `llm-d` take a couple of minutes because of the
GitHub Search API rate limit):

```bash
./venv/bin/python pr_keyword_stats.py --org llm-d --config terms/nvidia.json --out-dir /tmp/test-out --state merged
```

## Code style

- Plain Python 3, stdlib only in `pr_keyword_stats.py` (keep it
  dependency-free so it runs anywhere `gh` and Python exist).
  `make_charts.py` is allowed to depend on `matplotlib`.
- No formatter/linter is enforced yet — just keep it readable and consistent
  with the existing style (PEP 8-ish, descriptive names, docstrings on
  public functions).
- Prefer small, focused functions over adding branches to existing ones.

## Ideas for improvement

Contributions on any of these are very welcome:

- **GraphQL query batching** — replace the REST `search/issues` calls with
  a batched GraphQL query (multiple aliased `search(...)` fields per HTTP
  request) to reduce wall-clock time. Worth confirming current GitHub rate
  limit semantics for aliased search fields before/while implementing.
- **Incremental fetch / caching** — persist the last run's data and only
  query PRs `created:>` or `updated:>` the last run's timestamp, merging
  with cached results instead of re-fetching full history every time.
- **Config validation** — validate `terms/*.json` against a schema (e.g.
  required `label`/`terms` fields, term syntax) and give a friendlier error
  than a raw `KeyError`/`JSONDecodeError`.
- **Tests** — there are currently no automated tests. A good starting point
  would be unit tests for the pure functions (`slugify`, `month_of`,
  `repo_from_url`, the CSV writers) using fixture JSON payloads, so they
  don't require live `gh` calls or network access.
- **Additional output formats** — e.g. a Markdown summary table, or JSON
  output alongside CSV, for easier downstream consumption.

## Pull requests

- Keep PRs focused on one change.
- Include example output (a snippet of console output or a generated CSV/
  chart) when the change affects behavior, so reviewers can see the effect
  without re-running it themselves.
- Update `README.md` if you change CLI flags, output file names/formats, or
  the category config schema.

## Reporting security issues

This tool only performs read-only GitHub API calls using your own
credentials; it has no server component. If you find a security concern
regardless, please open an issue.

## License

By contributing, you agree that your contributions will be licensed under
the project's [MIT License](LICENSE).
