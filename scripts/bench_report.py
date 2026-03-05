#!/usr/bin/env python3
"""
Generate a benchmark comparison report: gloomy vs glom.

Usage:
    # Run benchmarks, print curated markdown table, save bench.png
    python scripts/bench_report.py

    # Full table — every gloomy/glom pair, grouped by function
    python scripts/bench_report.py --full

    # Use pre-existing JSON (skips running pytest, ~70 s saved)
    python scripts/bench_report.py --json /tmp/results.json

    # Table only, no chart
    python scripts/bench_report.py --no-chart
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path


# ---------------------------------------------------------------------------
# Curated scenarios shown in the default (summary) table and chart.
# Key   = gloomy variant name as it appears in the benchmark JSON.
# Value = human-readable row label.
# ---------------------------------------------------------------------------

FETCH_TESTS: dict[str, str] = {
    "test_dict_key_exists[gloomy-tuple]": "5-level dict (hit)",
    "test_dict_key_missing[gloomy-tuple]": "5-level dict (miss)",
    "test_obj_attr_exists[gloomy]": "3-level object attr (hit)",
    "test_list_index_exists[gloomy-tuple]": "5-level list index (hit)",
}

ASSIGN_TESTS: dict[str, str] = {
    "test_assign_shallow_dict[gloomy]": "1-level dict",
    "test_assign_dict_value[gloomy]": "5-level dict",
    "test_assign_list_index[gloomy]": "list index",
    "test_assign_realistic_api_response[gloomy]": "realistic API response",
}

DELETE_TESTS: dict[str, str] = {
    "test_delete_dict_shallow[gloomy]": "1-level dict",
    "test_delete_dict_5levels[gloomy]": "5-level dict",
    "test_delete_list_index[gloomy]": "list index",
    "test_delete_realistic_api_response[gloomy]": "realistic API response",
}

CURATED_SECTIONS: list[tuple[str, dict[str, str]]] = [
    ("gloom (fetch)", FETCH_TESTS),
    ("assign", ASSIGN_TESTS),
    ("delete", DELETE_TESTS),
]

# Prefix → section bucket used when building the full table automatically.
_FUNC_BUCKET: dict[str, str] = {
    "test_dict_": "gloom (fetch)",
    "test_obj_": "gloom (fetch)",
    "test_list_": "gloom (fetch)",
    "test_assign_": "assign",
    "test_delete_": "delete",
}

BENCH_FILES = [
    "tests/test_bench_dict.py",
    "tests/test_bench_obj.py",
    "tests/test_bench_list.py",
    "tests/test_bench_assign.py",
    "tests/test_bench_delete.py",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _glom_name(gloomy_name: str) -> str:
    """Derive the glom variant name from a gloomy variant name."""
    return gloomy_name.replace("[gloomy", "[glom")


def _fmt_time(seconds: float) -> str:
    ns = seconds * 1e9
    if ns < 995:
        return f"{ns:.0f} ns"
    return f"{ns / 1000:.2f} µs"


def _parse_results(json_path: str) -> dict[str, float]:
    with open(json_path) as fh:
        data = json.load(fh)
    return {b["name"]: b["stats"]["mean"] for b in data["benchmarks"]}


def _build_rows(
    results: dict[str, float],
    tests: dict[str, str],
) -> list[tuple[str, float, float, float]]:
    """Return (label, gloomy_s, glom_s, speedup) for every entry in *tests*."""
    rows = []
    for gloomy_key, label in tests.items():
        glom_key = _glom_name(gloomy_key)
        gloomy_s = results.get(gloomy_key)
        glom_s = results.get(glom_key)
        if gloomy_s is None or glom_s is None:
            print(f"  warning: no data for {gloomy_key!r} or {glom_key!r}", file=sys.stderr)
            continue
        rows.append((label, gloomy_s, glom_s, glom_s / gloomy_s))
    return rows


def _auto_label(test_base: str) -> str:
    """'test_delete_dict_5levels' → 'dict 5levels'."""
    for prefix in _FUNC_BUCKET:
        if test_base.startswith(prefix):
            return test_base[len(prefix) :].replace("_", " ")
    return test_base.replace("_", " ")


def _full_sections(results: dict[str, float]) -> list[tuple[str, list]]:
    """Build a complete section list from every gloomy/glom pair in *results*."""
    buckets: dict[str, list] = {v: [] for v in _FUNC_BUCKET.values()}

    _SKIP = ("manual", "string_path", "tuple_path", "numeric_string_key", "no_copy", "hot_path")

    for name, mean in results.items():
        if not ("[gloomy" in name or name.endswith("[gloomy]")):
            continue
        if any(s in name for s in _SKIP):
            continue

        glom_key = _glom_name(name)
        glom_s = results.get(glom_key)
        if glom_s is None:
            continue

        base = name.split("[")[0]
        label = _auto_label(base)
        if "-tuple]" in name:
            label += " (tuple)"
        elif "-str]" in name:
            label += " (str)"

        row = (label, mean, glom_s, glom_s / mean)
        for prefix, bucket in _FUNC_BUCKET.items():
            if base.startswith(prefix):
                buckets[bucket].append(row)
                break

    return [(title, sorted(buckets[title], key=lambda r: r[0])) for title in ("gloom (fetch)", "assign", "delete")]


# ---------------------------------------------------------------------------
# Output: markdown table
# ---------------------------------------------------------------------------


def _print_markdown(sections: list[tuple[str, list]]) -> None:
    print("<!-- Generated by scripts/bench_report.py -->\n")
    for title, rows in sections:
        print(f"### `{title}`\n")
        print("| Scenario | gloomy | glom | speedup |")
        print("|---|---:|---:|:---:|")
        for label, gm, glomm, speedup in rows:
            print(f"| {label} | {_fmt_time(gm)} | {_fmt_time(glomm)} | **{speedup:.1f}×** |")
        print()


# ---------------------------------------------------------------------------
# Output: matplotlib chart
# ---------------------------------------------------------------------------


def _make_chart(sections: list[tuple[str, list]], out_path: str) -> None:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.patches as mpatches
    import matplotlib.pyplot as plt
    import numpy as np

    GLOOMY_COLOR = "#4C72B0"
    GLOM_COLOR = "#DD8452"
    BAR_HEIGHT = 0.38

    max_rows = max(len(rows) for _, rows in sections)
    fig, axes = plt.subplots(
        1,
        len(sections),
        figsize=(5.5 * len(sections), max_rows * 0.65 + 2.2),
    )
    if len(sections) == 1:
        axes = [axes]

    fig.suptitle(
        "gloomy vs glom — mean execution time (lower is better)",
        fontsize=13,
        fontweight="bold",
        y=1.01,
    )

    for ax, (title, rows) in zip(axes, sections):
        labels = [r[0] for r in rows]
        g_times = [r[1] * 1e6 for r in rows]  # seconds → µs
        glomt = [r[2] * 1e6 for r in rows]

        y = np.arange(len(labels))
        ax.barh(y + BAR_HEIGHT / 2, glomt, BAR_HEIGHT, color=GLOM_COLOR, label="glom", zorder=3)
        ax.barh(y - BAR_HEIGHT / 2, g_times, BAR_HEIGHT, color=GLOOMY_COLOR, label="gloomy", zorder=3)

        for i, (gt, gv) in enumerate(zip(g_times, glomt)):
            ax.text(max(gt, gv) * 1.04, i, f"{gv / gt:.1f}×", va="center", fontsize=8.5, fontweight="bold")

        ax.set_yticks(y)
        ax.set_yticklabels(labels, fontsize=9)
        ax.set_xlabel("µs", fontsize=9)
        ax.set_title(f"`{title}`", fontsize=11, fontweight="bold")
        ax.invert_yaxis()
        ax.grid(axis="x", linestyle="--", alpha=0.4, zorder=0)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.set_xlim(right=max(glomt) * 1.30)

    fig.legend(
        handles=[
            mpatches.Patch(color=GLOOMY_COLOR, label="gloomy"),
            mpatches.Patch(color=GLOM_COLOR, label="glom"),
        ],
        loc="lower center",
        ncol=2,
        fontsize=10,
        frameon=False,
        bbox_to_anchor=(0.5, -0.04),
    )
    plt.tight_layout()
    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    print(f"Chart saved → {out_path}", file=sys.stderr)


# ---------------------------------------------------------------------------
# Benchmark runner
# ---------------------------------------------------------------------------


def _run_benchmarks(repo_root: Path) -> str:
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        *[str(repo_root / f) for f in BENCH_FILES],
        f"--benchmark-json={tmp.name}",
        "--benchmark-disable-gc",
        "-q",
        "--no-header",
    ]
    print("Running benchmarks…", file=sys.stderr)
    # capture_output=True silences pytest-benchmark's ASCII tables entirely.
    result = subprocess.run(cmd, cwd=repo_root, capture_output=True, text=True)
    # Surface pass/fail summary line(s) only.
    for line in result.stdout.splitlines():
        if any(kw in line for kw in ("passed", "failed", "error", "FAILED", "ERROR")):
            print(line, file=sys.stderr)
    if result.returncode != 0:
        print(result.stderr or result.stdout, file=sys.stderr)
        sys.exit(result.returncode)
    return tmp.name


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    repo_root = Path(__file__).parent.parent

    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--json", metavar="FILE", help="Use existing benchmark JSON")
    parser.add_argument(
        "--full", action="store_true", help="Include every gloomy/glom pair, not just the curated summary"
    )
    parser.add_argument("--no-chart", action="store_true", help="Skip chart generation (matplotlib not required)")
    parser.add_argument(
        "--chart-out",
        default=str(repo_root / "bench.png"),
        metavar="FILE",
        help="Output path for chart PNG (default: bench.png)",
    )
    args = parser.parse_args()

    json_path = args.json or _run_benchmarks(repo_root)
    results = _parse_results(json_path)

    if args.full:
        sections = _full_sections(results)
    else:
        sections = [(title, _build_rows(results, tests)) for title, tests in CURATED_SECTIONS]

    _print_markdown(sections)

    if not args.no_chart and not args.full:
        try:
            _make_chart(sections, args.chart_out)
        except ImportError:
            print(
                "matplotlib not found — skipping chart.\nInstall with: uv add --dev matplotlib",
                file=sys.stderr,
            )


if __name__ == "__main__":
    main()
