# llm-d-pr-stats

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Extract and aggregate **pull request statistics, by keyword category, across
every repo in a GitHub organization** — with month-to-month trends, per-repo
breakdowns, and cross-category comparisons.

Originally built to answer "how many `llm-d` PRs relate to NVIDIA
components, and how has that evolved over time?", but it's fully generic:
the keywords for each category live in small JSON files under [`terms/`](terms/)
instead of being hardcoded, so you can point it at any org and any topic —
vendors (NVIDIA, AMD, Intel), components (observability, security), or
anything else you can express as a set of search terms.

## How it works

For each category config, the script queries the [GitHub Search
API](https://docs.github.com/en/rest/search/search) (via the [`gh`
CLI](https://cli.github.com/)) once per term:

```
org:<org> is:pr <term>
```

across the **entire organization in one query** (no need to loop over
repos). Results for all terms *within a category* are de-duplicated by PR
id, then aggregated into monthly opened/merged counts, per-repo totals, and
per-term match counts. If you pass more than one category, it also writes a
cross-category comparison CSV.

## Requirements

- [GitHub CLI](https://cli.github.com/) (`gh`), authenticated:
  ```
  gh auth login
  ```
  Any account with public read access works (a PAT with `public_repo` scope
  is enough for public orgs).
- Python 3.8+. `pr_keyword_stats.py` itself has **no third-party
  dependencies** — only the optional `make_charts.py` needs `matplotlib`
  (see [`requirements.txt`](requirements.txt)).

## Quick start

```bash
# (optional) isolate chart dependencies
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# fetch stats for the default category (terms/nvidia.json)
python3 pr_keyword_stats.py --org llm-d --out-dir ./out

# render charts from the CSVs
./venv/bin/python make_charts.py --out-dir ./out
```

Compare multiple categories in one run:

```bash
python3 pr_keyword_stats.py --org llm-d --config terms/nvidia.json terms/amd.json --out-dir ./out
./venv/bin/python make_charts.py --out-dir ./out
```

## Defining a category

Each category is a small JSON file (see [`terms/nvidia.json`](terms/nvidia.json),
[`terms/amd.json`](terms/amd.json), and the [`terms/_template.json`](terms/_template.json)
starter):

```json
{
  "label": "NVIDIA",
  "description": "PRs related to NVIDIA hardware and software components (GPUs, CUDA, NIXL, TensorRT-LLM, Dynamo, etc.)",
  "terms": [
    "NVIDIA",
    "NIXL",
    "CUDA",
    "\"NVIDIA Dynamo\""
  ]
}
```

- `label` — human-readable name, used in chart titles and console output.
- `terms` — search terms (GitHub full-text search syntax; wrap phrases in
  escaped quotes, e.g. `"\"NVIDIA Dynamo\""`).
- `description` — informational only.

Copy `terms/_template.json` to `terms/<yourcategory>.json` to add a new one
— no code changes required.

## CLI reference

```
python3 pr_keyword_stats.py [--org ORG] [--out-dir DIR] [--config FILE [FILE ...]] [--state {all,open,closed,merged}]
```

| Flag | Default | Description |
|---|---|---|
| `--org` | `llm-d` | GitHub org to scan |
| `--out-dir` | `./out` | Directory to write CSV output into |
| `--config` | `terms/nvidia.json` | One or more category JSON files. Pass multiple for a cross-category comparison CSV. |
| `--state` | `all` | Restrict to `open`, `closed`, or `merged` PRs |

```
python3 make_charts.py [--out-dir DIR]
```

`make_charts.py` auto-discovers every category present in `--out-dir` by
scanning for `<slug>_monthly_summary.csv` files, so it needs no per-category
configuration.

## Output files

For each category (slug derived from its `label`, e.g. `NVIDIA` → `nvidia`):

| File | Contents |
|---|---|
| `<slug>_prs.csv` | Every matched PR: repo, number, title, url, author, state, merged flag, dates, matched terms |
| `<slug>_monthly_summary.csv` | Month, opened count, merged count, cumulative opened |
| `<slug>_repo_summary.csv` | Per-repo total and merged counts |
| `<slug>_term_summary.csv` | Per-term search hit count and unique-PR contribution |
| `<slug>_pr_monthly_trend.png` | Opened-vs-merged bar chart + cumulative line chart |
| `<slug>_pr_by_repo.png` | Horizontal bar chart of matched PRs by repo |

When more than one category is run:

| File | Contents |
|---|---|
| `comparison_monthly.csv` | Month-by-month opened/merged counts, one column pair per category |
| `comparison_monthly_trend.png` | Overlaid monthly "opened" trend lines per category |

## Caveats / limitations

- **Heuristic matching.** This is keyword text search against PR
  title/body/comments, not semantic classification — tune each category's
  `terms` to reduce false positives/negatives.
- **1000-result cap.** The GitHub Search API caps any single query at 1000
  results (10 pages of 100). The script warns if a term hits this; narrow
  it (e.g. split by `created:YYYY-MM-DD..YYYY-MM-DD` ranges) if needed.
- **Search API rate limit.** GitHub's Search API is limited to ~30
  requests/minute, separate from the general API quota. The script sleeps
  between calls to stay under this — expect roughly 2+ seconds per search
  term, so large term lists take a while. See
  [CONTRIBUTING.md](CONTRIBUTING.md) for ideas on speeding this up (e.g.
  GraphQL query batching).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Bug reports and feature requests
have templates under [`.github/ISSUE_TEMPLATE/`](.github/ISSUE_TEMPLATE/);
PRs use the template at [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md).

## Security

See [SECURITY.md](SECURITY.md) for how to report vulnerabilities.

## License

[MIT](LICENSE)
