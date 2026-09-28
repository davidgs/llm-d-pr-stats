#!/usr/bin/env python3
"""
Generate charts from the CSVs produced by pr_keyword_stats.py.

Auto-discovers every category present in --out-dir by looking for
`<slug>_monthly_summary.csv` / `<slug>_repo_summary.csv` files, so it works
for any number/kind of categories without editing this script.

Usage:
    python3 make_charts.py --out-dir ./out
"""
import argparse
import csv
import glob
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

COLORS = ["#76b900", "#1f2a44", "#e07b39", "#5b9bd5", "#a05195", "#d45087"]


def discover_slugs(out_dir):
    slugs = []
    for path in sorted(glob.glob(os.path.join(out_dir, "*_monthly_summary.csv"))):
        slug = os.path.basename(path)[: -len("_monthly_summary.csv")]
        slugs.append(slug)
    return slugs


def label_for(slug, out_dir):
    # best-effort: use the term_summary.csv presence just to confirm; slug->Title Case
    return slug.replace("_", " ").upper() if len(slug) <= 5 else slug.replace("_", " ").title()


def read_monthly(path):
    months, opened, merged, cum = [], [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            months.append(row["month"])
            opened.append(int(row["opened"]))
            merged.append(int(row["merged"]))
            cum.append(int(row["cumulative_opened"]))
    return months, opened, merged, cum


def read_repo(path):
    repos, totals, mergeds = [], [], []
    with open(path) as f:
        for row in csv.DictReader(f):
            repos.append(row["repo"].split("/")[-1])
            totals.append(int(row["total_prs"]))
            mergeds.append(int(row["merged_prs"]))
    return repos, totals, mergeds


def chart_single_category(out_dir, slug):
    label = label_for(slug, out_dir)
    months, opened, merged, cum = read_monthly(os.path.join(out_dir, f"{slug}_monthly_summary.csv"))

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(11, 8), sharex=True)
    x = range(len(months))
    width = 0.4
    ax1.bar([i - width / 2 for i in x], opened, width=width, label="Opened", color=COLORS[0])
    ax1.bar([i + width / 2 for i in x], merged, width=width, label="Merged", color=COLORS[1])
    ax1.set_ylabel("PRs per month")
    ax1.set_title(f"{label}-related PRs opened vs. merged per month")
    ax1.legend()
    ax1.grid(axis="y", linestyle="--", alpha=0.4)

    ax2.plot(x, cum, marker="o", color=COLORS[0])
    ax2.set_ylabel("Cumulative opened PRs")
    ax2.set_title(f"Cumulative {label}-related PRs over time")
    ax2.grid(axis="y", linestyle="--", alpha=0.4)

    plt.xticks(list(x), months, rotation=45, ha="right")
    plt.tight_layout()
    out_path = os.path.join(out_dir, f"{slug}_pr_monthly_trend.png")
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved {out_path}")

    repo_path = os.path.join(out_dir, f"{slug}_repo_summary.csv")
    if os.path.exists(repo_path):
        repos, totals, mergeds = read_repo(repo_path)
        fig2, ax = plt.subplots(figsize=(10, max(4, 0.4 * len(repos))))
        y = range(len(repos))
        ax.barh(y, totals, color=COLORS[0], label="Total matched PRs")
        ax.barh(y, mergeds, color=COLORS[1], label="Merged")
        ax.set_yticks(list(y))
        ax.set_yticklabels(repos)
        ax.invert_yaxis()
        ax.set_xlabel(f"{label}-related PRs")
        ax.set_title(f"{label}-related PRs by repo")
        ax.legend()
        ax.grid(axis="x", linestyle="--", alpha=0.4)
        plt.tight_layout()
        out_path2 = os.path.join(out_dir, f"{slug}_pr_by_repo.png")
        plt.savefig(out_path2, dpi=150)
        plt.close(fig2)
        print(f"saved {out_path2}")


def chart_comparison(out_dir, slugs):
    comp_path = os.path.join(out_dir, "comparison_monthly.csv")
    if not os.path.exists(comp_path):
        return
    with open(comp_path) as f:
        rows = list(csv.DictReader(f))
    months = [r["month"] for r in rows]
    x = range(len(months))

    fig, ax = plt.subplots(figsize=(11, 6))
    for i, slug in enumerate(slugs):
        col = f"{slug}_opened"
        if col not in rows[0]:
            continue
        series = [int(r[col]) for r in rows]
        ax.plot(x, series, marker="o", label=label_for(slug, out_dir), color=COLORS[i % len(COLORS)])
    ax.set_xticks(list(x))
    ax.set_xticklabels(months, rotation=45, ha="right")
    ax.set_ylabel("PRs opened per month")
    ax.set_title("Category comparison: PRs opened per month")
    ax.legend()
    ax.grid(axis="y", linestyle="--", alpha=0.4)
    plt.tight_layout()
    out_path = os.path.join(out_dir, "comparison_monthly_trend.png")
    plt.savefig(out_path, dpi=150)
    plt.close(fig)
    print(f"saved {out_path}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="./out")
    args = parser.parse_args()

    slugs = discover_slugs(args.out_dir)
    if not slugs:
        print(f"No *_monthly_summary.csv files found in {args.out_dir}. Run pr_keyword_stats.py first.")
        return

    for slug in slugs:
        chart_single_category(args.out_dir, slug)

    if len(slugs) > 1:
        chart_comparison(args.out_dir, slugs)


if __name__ == "__main__":
    main()
