#!/usr/bin/env python3
"""
Extract and aggregate PR statistics for one or more keyword categories
across every repo in a GitHub organization (default: https://github.com/llm-d),
with month-to-month evolution.

Generic by design: the keywords for each category live in small JSON files
under `terms/` (e.g. `terms/nvidia.json`, `terms/amd.json`) instead of being
hardcoded in this script. Point --config at any JSON file(s) to analyze any
topic, not just NVIDIA -- vendors (AMD, Intel), components (Kubernetes,
observability), whatever text pattern you care about.

How it works
------------
For each category config, this runs the GitHub Search API (via `gh api`) as:

    org:<org> is:pr <term>

for every term in that category's "terms" list, across the whole org in one
shot (no need to loop per-repo). Results for all terms *within a category*
are de-duplicated by PR id. If you pass more than one category, a comparison
CSV is also written across categories.

Category config format (JSON)
------------------------------
    {
      "label": "NVIDIA",
      "description": "optional, informational only",
      "terms": ["NVIDIA", "NIXL", "CUDA", "...", "\"quoted phrase\""]
    }

Requirements
------------
- GitHub CLI `gh`, authenticated: `gh auth login` (needs at least public
  read access; a plain PAT with `public_repo` works too).
- Python 3.8+, no third-party dependencies.

Usage
-----
    python3 pr_keyword_stats.py                              # uses terms/nvidia.json
    python3 pr_keyword_stats.py --config terms/amd.json
    python3 pr_keyword_stats.py --config terms/nvidia.json terms/amd.json   # + comparison
    python3 pr_keyword_stats.py --org llm-d --out-dir ./out --state merged

Notes / limitations
--------------------
- The GitHub Search API caps any single query at 1000 results (10 pages of
  100). If a term's total_count exceeds 1000, this script warns you; narrow
  that term (e.g. split by date range with `created:YYYY-MM-DD..YYYY-MM-DD`)
  to get complete coverage.
- The Search API has its own rate limit (30 req/min) separate from the core
  API limit. This script sleeps between calls to stay under that.
- Keyword matching against title/body/comments is inherently a heuristic --
  tune each category's terms to taste.
"""

import argparse
import collections
import csv
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_CONFIG = os.path.join(SCRIPT_DIR, "terms", "nvidia.json")
SEARCH_SLEEP_SECONDS = 2.2  # keep comfortably under the 30 req/min search API limit


def slugify(label):
    slug = re.sub(r"[^a-z0-9]+", "_", label.lower()).strip("_")
    return slug or "category"


def load_category(config_path):
    with open(config_path) as f:
        data = json.load(f)
    label = data.get("label") or os.path.splitext(os.path.basename(config_path))[0]
    terms = data.get("terms")
    if not terms:
        raise ValueError(f"{config_path}: no 'terms' list found")
    return {
        "label": label,
        "slug": slugify(label),
        "description": data.get("description", ""),
        "terms": terms,
        "source": config_path,
    }


def run_gh_api(query_string, page):
    encoded = urllib.parse.quote_plus(query_string)
    cmd = ["gh", "api", f"search/issues?q={encoded}&per_page=100&page={page}"]
    for attempt in range(5):
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode == 0:
            return json.loads(proc.stdout)
        sys.stderr.write(f"  [warn] gh api failed (attempt {attempt + 1}): {proc.stderr.strip()}\n")
        time.sleep(5 * (attempt + 1))
    raise RuntimeError(f"gh api call failed repeatedly for: {query_string}")


def fetch_term(org, term, pr_state):
    base_q = f"org:{org} is:pr {term}"
    if pr_state == "merged":
        base_q += " is:merged"
    elif pr_state == "open":
        base_q += " is:open"
    elif pr_state == "closed":
        base_q += " is:closed"

    first = run_gh_api(base_q, page=1)
    total = first.get("total_count", 0)
    items = list(first.get("items", []))

    if total > 1000:
        sys.stderr.write(
            f"  [warn] term {term!r} has {total} results; only first 1000 are "
            f"reachable via the Search API. Consider splitting by date range.\n"
        )

    pages_needed = min(-(-total // 100), 10)  # ceil div, capped at 10
    for page in range(2, pages_needed + 1):
        time.sleep(SEARCH_SLEEP_SECONDS)
        data = run_gh_api(base_q, page=page)
        items.extend(data.get("items", []))

    return total, items


def repo_from_url(repository_url):
    parts = repository_url.rstrip("/").split("/")
    return f"{parts[-2]}/{parts[-1]}"


def month_of(iso_ts):
    if not iso_ts:
        return None
    return iso_ts[:7]  # "YYYY-MM"


def fetch_category(org, category, pr_state):
    """Run all terms for one category, dedup by PR id. Returns (prs, term_totals)."""
    prs = {}
    term_totals = {}
    for term in category["terms"]:
        print(f"[fetch] [{category['label']}] {term!r} ...", flush=True)
        total, items = fetch_term(org, term, pr_state)
        term_totals[term] = total
        print(f"        -> total_count={total}, fetched={len(items)}")
        for item in items:
            pr_id = item["id"]
            rec = prs.get(pr_id)
            if rec is None:
                rec = {
                    "repo": repo_from_url(item["repository_url"]),
                    "number": item["number"],
                    "title": item["title"],
                    "url": item["html_url"],
                    "author": item.get("user", {}).get("login"),
                    "state": item.get("state"),
                    "created_at": item.get("created_at"),
                    "closed_at": item.get("closed_at"),
                    "merged_at": (item.get("pull_request") or {}).get("merged_at"),
                    "matched_terms": set(),
                }
                prs[pr_id] = rec
            rec["matched_terms"].add(term)
        time.sleep(SEARCH_SLEEP_SECONDS)
    return list(prs.values()), term_totals


def write_category_outputs(out_dir, category, all_prs, term_totals):
    slug = category["slug"]

    prs_csv_path = os.path.join(out_dir, f"{slug}_prs.csv")
    with open(prs_csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "number", "title", "url", "author", "state", "merged", "created_at", "merged_at", "closed_at", "matched_terms"])
        for r in sorted(all_prs, key=lambda r: r["created_at"] or ""):
            w.writerow([
                r["repo"], r["number"], r["title"], r["url"], r["author"], r["state"],
                bool(r["merged_at"]), r["created_at"], r["merged_at"], r["closed_at"],
                ";".join(sorted(r["matched_terms"])),
            ])
    print(f"[write] {prs_csv_path}")

    opened_by_month = collections.Counter()
    merged_by_month = collections.Counter()
    for r in all_prs:
        m = month_of(r["created_at"])
        if m:
            opened_by_month[m] += 1
        mm = month_of(r["merged_at"])
        if mm:
            merged_by_month[mm] += 1

    months = sorted(set(opened_by_month) | set(merged_by_month))
    monthly_csv_path = os.path.join(out_dir, f"{slug}_monthly_summary.csv")
    with open(monthly_csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["month", "opened", "merged", "cumulative_opened"])
        cum = 0
        for m in months:
            cum += opened_by_month[m]
            w.writerow([m, opened_by_month[m], merged_by_month[m], cum])
    print(f"[write] {monthly_csv_path}")

    repo_counts = collections.Counter(r["repo"] for r in all_prs)
    repo_merged_counts = collections.Counter(r["repo"] for r in all_prs if r["merged_at"])
    repo_csv_path = os.path.join(out_dir, f"{slug}_repo_summary.csv")
    with open(repo_csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["repo", "total_prs", "merged_prs"])
        for repo, count in repo_counts.most_common():
            w.writerow([repo, count, repo_merged_counts[repo]])
    print(f"[write] {repo_csv_path}")

    term_unique_counts = collections.Counter()
    for r in all_prs:
        for t in r["matched_terms"]:
            term_unique_counts[t] += 1
    term_csv_path = os.path.join(out_dir, f"{slug}_term_summary.csv")
    with open(term_csv_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["term", "search_total_count", "unique_prs_matched"])
        for term in category["terms"]:
            w.writerow([term, term_totals.get(term, ""), term_unique_counts.get(term, 0)])
    print(f"[write] {term_csv_path}")

    print(f"\n=== [{category['label']}] Month-to-month evolution (opened / merged) ===")
    for m in months:
        print(f"  {m}:  opened={opened_by_month[m]:>4}   merged={merged_by_month[m]:>4}")

    print(f"\n=== [{category['label']}] By repo ===")
    for repo, count in repo_counts.most_common():
        print(f"  {repo:<35} total={count:>4}  merged={repo_merged_counts[repo]:>4}")

    return {
        "months": months,
        "opened_by_month": opened_by_month,
        "merged_by_month": merged_by_month,
        "repo_counts": repo_counts,
        "total_unique": len(all_prs),
    }


def write_comparison(out_dir, categories, results):
    """Write a cross-category comparison CSV when more than one category was run."""
    all_months = sorted(set().union(*(set(r["months"]) for r in results.values())))
    comp_path = os.path.join(out_dir, "comparison_monthly.csv")
    with open(comp_path, "w", newline="") as f:
        w = csv.writer(f)
        header = ["month"]
        for cat in categories:
            header += [f"{cat['slug']}_opened", f"{cat['slug']}_merged"]
        w.writerow(header)
        for m in all_months:
            row = [m]
            for cat in categories:
                r = results[cat["slug"]]
                row += [r["opened_by_month"].get(m, 0), r["merged_by_month"].get(m, 0)]
            w.writerow(row)
    print(f"[write] {comp_path}")

    print("\n=== Category comparison: total unique PRs matched ===")
    for cat in categories:
        print(f"  {cat['label']:<15} {results[cat['slug']]['total_unique']}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--org", default="llm-d", help="GitHub org to scan (default: llm-d)")
    parser.add_argument("--out-dir", default="./out", help="Directory to write CSV output into")
    parser.add_argument(
        "--config",
        nargs="+",
        default=[DEFAULT_CONFIG],
        help="One or more category JSON files (default: terms/nvidia.json). "
             "Pass multiple to also get a cross-category comparison CSV.",
    )
    parser.add_argument(
        "--state",
        choices=["all", "open", "closed", "merged"],
        default="all",
        help="Restrict to PRs of this state (default: all)",
    )
    args = parser.parse_args()

    categories = [load_category(p) for p in args.config]
    os.makedirs(args.out_dir, exist_ok=True)

    results = {}
    for category in categories:
        print(f"\n########## Category: {category['label']} ({category['source']}) ##########")
        all_prs, term_totals = fetch_category(args.org, category, args.state)
        print(f"\n[done] {len(all_prs)} unique PRs matched for {category['label']!r} "
              f"across {len(category['terms'])} terms in org:{args.org}\n")
        results[category["slug"]] = write_category_outputs(args.out_dir, category, all_prs, term_totals)

    if len(categories) > 1:
        write_comparison(args.out_dir, categories, results)


if __name__ == "__main__":
    main()
