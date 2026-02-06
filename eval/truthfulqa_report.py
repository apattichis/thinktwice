"""TruthfulQA evaluation report generator with visualizations.

Generates comprehensive Markdown reports with charts:
- SS vs TT truthfulness/informativeness comparison
- Per-category horizontal bar chart
- Latency analysis
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from eval.truthfulqa_metrics import compute_truthfulqa_metrics

logger = logging.getLogger(__name__)

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available -- charts will be skipped")


COLORS = {
    "ss": "#8E8E93",
    "tt": "#007AFF",
    "success": "#34C759",
    "error": "#FF3B30",
    "warning": "#FF9F0A",
    "text": "#1D1D1F",
    "accent": "#5856D6",
    "truthful": "#34C759",
    "informative": "#007AFF",
    "both": "#5856D6",
}


def _setup_style():
    if not HAS_MATPLOTLIB:
        return
    plt.rcParams.update({
        "figure.facecolor": "#FFFFFF",
        "axes.facecolor": "#FAFAFA",
        "axes.edgecolor": "#E5E5E5",
        "axes.grid": True,
        "grid.color": "#F0F0F0",
        "grid.linewidth": 0.8,
        "font.family": "sans-serif",
        "font.size": 11,
        "axes.titlesize": 14,
        "axes.titleweight": "bold",
        "axes.labelsize": 11,
        "xtick.labelsize": 10,
        "ytick.labelsize": 10,
        "legend.fontsize": 10,
        "figure.dpi": 150,
        "savefig.dpi": 150,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.3,
    })


def _chart_truthfulness_comparison(ss_metrics: dict, tt_metrics: dict, output_path: str) -> Optional[str]:
    """Grouped bar chart: SS vs TT on truthful, informative, both."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    labels = ["Truthful +\nInformative", "Truthful\nOnly", "Informative\nOnly"]
    ss_vals = [
        ss_metrics.get("truthful_informative_rate", 0) * 100,
        ss_metrics.get("truthful_rate", 0) * 100,
        ss_metrics.get("informative_rate", 0) * 100,
    ]
    tt_vals = [
        tt_metrics.get("truthful_informative_rate", 0) * 100,
        tt_metrics.get("truthful_rate", 0) * 100,
        tt_metrics.get("informative_rate", 0) * 100,
    ]

    x = np.arange(len(labels))
    width = 0.32
    fig, ax = plt.subplots(figsize=(10, 6))

    bars_ss = ax.bar(x - width/2, ss_vals, width, label="Single-Shot",
                     color=COLORS["ss"], alpha=0.85, edgecolor="white", linewidth=0.5)
    bars_tt = ax.bar(x + width/2, tt_vals, width, label="ThinkTwice",
                     color=COLORS["tt"], alpha=0.85, edgecolor="white", linewidth=0.5)

    ax.set_ylabel("Rate (%)")
    ax.set_title("TruthfulQA: Truthfulness & Informativeness",
                 fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")
    ax.set_ylim(0, 110)

    for bars in [bars_ss, bars_tt]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 1.5, f'{h:.1f}%',
                        ha='center', va='bottom', fontsize=9, fontweight='medium')

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def _chart_per_category(metrics: dict, output_path: str) -> Optional[str]:
    """Horizontal bar chart of per-category truthful+informative rate."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    per_cat = metrics.get("per_category", {})
    if not per_cat:
        return None

    # Sort by both_rate and filter to categories with enough samples
    sorted_cats = sorted(per_cat.items(), key=lambda x: x[1]["both_rate"], reverse=True)
    # Only show categories with at least 1 sample
    sorted_cats = [(k, v) for k, v in sorted_cats if v["total"] >= 1]

    if not sorted_cats:
        return None

    names = [c[0] for c in sorted_cats]
    both_rates = [c[1]["both_rate"] * 100 for c in sorted_cats]
    counts = [c[1]["total"] for c in sorted_cats]

    fig, ax = plt.subplots(figsize=(11, max(5, len(names) * 0.4 + 2)))

    bars = ax.barh(range(len(names)), both_rates, color=COLORS["both"], alpha=0.85,
                   edgecolor="white", height=0.65, linewidth=0.5)

    # Color by performance level
    for bar, rate in zip(bars, both_rates):
        if rate >= 80:
            bar.set_color(COLORS["success"])
        elif rate >= 50:
            bar.set_color(COLORS["warning"])
        else:
            bar.set_color(COLORS["error"])
        bar.set_alpha(0.85)

    ax.set_yticks(range(len(names)))
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Truthful + Informative Rate (%)")
    ax.set_title("TruthfulQA: Per-Category Performance",
                 fontsize=14, fontweight="bold", color=COLORS["text"])
    ax.set_xlim(0, 115)
    ax.invert_yaxis()

    for bar, count, rate in zip(bars, counts, both_rates):
        ax.text(min(rate + 1.5, 108), bar.get_y() + bar.get_height()/2,
                f'{rate:.0f}% (n={count})', va='center', fontsize=8)

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def _chart_latency_comparison(ss_lat: dict, tt_lat: dict, output_path: str) -> Optional[str]:
    """Latency comparison bar chart."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    labels = ["Single-Shot", "ThinkTwice"]
    means = [ss_lat.get("mean_ms", 0)/1000, tt_lat.get("mean_ms", 0)/1000]
    p95s = [ss_lat.get("p95_ms", 0)/1000, tt_lat.get("p95_ms", 0)/1000]
    colors = [COLORS["ss"], COLORS["tt"]]

    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))

    bars_mean = ax.bar(x - width/2, means, width, label="Mean", color=colors, alpha=0.85, edgecolor="white")
    bars_p95 = ax.bar(x + width/2, p95s, width, label="P95", color=colors, alpha=0.45, edgecolor="white")

    for bar in list(bars_mean) + list(bars_p95):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{bar.get_height():.1f}s', ha='center', va='bottom', fontsize=9)

    ax.set_ylabel("Duration (seconds)")
    ax.set_title("TruthfulQA: Latency Comparison", fontsize=14, fontweight="bold", color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Main report generator
# ---------------------------------------------------------------------------

def generate_truthfulqa_report(
    results: list[dict],
    dataset_name: str,
    output_dir: str = "results",
    comparison: dict | None = None,
    ss_metrics: dict | None = None,
) -> str:
    """Generate a comprehensive TruthfulQA evaluation report."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    charts_dir = output_path / "charts"
    charts_dir.mkdir(exist_ok=True)

    metrics = compute_truthfulqa_metrics(results)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    section = 0
    lines = []
    lines.append("# TruthfulQA: Misconception Resistance Report")
    lines.append("")
    lines.append(f"**Dataset:** {dataset_name}  ")
    lines.append(f"**Generated:** {timestamp}  ")
    lines.append(f"**Total Questions:** {metrics['total_judged']}  ")
    lines.append(f"**Categories:** {len(metrics.get('per_category', {}))}  ")
    lines.append(f"**Pipeline:** ThinkTwice (self-correcting pipeline)  ")
    lines.append(f"**Judge Model:** Claude Haiku 4.5  ")
    lines.append("")

    # --- Executive Summary ---
    section += 1
    lines.append(f"## {section}. Executive Summary")
    lines.append("")
    lines.append("TruthfulQA tests whether models avoid generating common misconceptions and false beliefs. "
                 "This evaluates ThinkTwice's web verification and self-verification capabilities.")
    lines.append("")

    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| **Truthful + Informative** | {metrics['truthful_informative_rate']:.1%} ({metrics['both_count']}/{metrics['total_judged']}) |")
    lines.append(f"| **Truthful Rate** | {metrics['truthful_rate']:.1%} ({metrics['truthful_count']}/{metrics['total_judged']}) |")
    lines.append(f"| **Informative Rate** | {metrics['informative_rate']:.1%} ({metrics['informative_count']}/{metrics['total_judged']}) |")
    lat = metrics["latency"]
    lines.append(f"| **Mean Latency** | {lat['mean_ms']/1000:.1f}s |")
    lines.append(f"| **P95 Latency** | {lat['p95_ms']/1000:.1f}s |")
    lines.append("")

    # --- Methodology ---
    section += 1
    lines.append(f"## {section}. Methodology")
    lines.append("")
    lines.append("### TruthfulQA Metrics")
    lines.append("")
    lines.append("- **Truthful**: Response contains no false claims (saying \"I don't know\" counts as truthful)")
    lines.append("- **Informative**: Response actually answers the question (\"I don't know\" is NOT informative)")
    lines.append("- **Truthful + Informative** (headline metric): Response is both truthful AND informative")
    lines.append("")
    lines.append("### Judge")
    lines.append("")
    lines.append("Claude Haiku 4.5 is used as the judge model. Each response is evaluated against the dataset's "
                 "correct and incorrect reference answers. The judge determines truthfulness by checking whether "
                 "the response aligns with correct answers and avoids incorrect ones (common misconceptions).")
    lines.append("")

    # --- Comparison ---
    if comparison and ss_metrics:
        ssm = ss_metrics
        ttm = comparison["thinktwice_metrics"]

        section += 1
        lines.append(f"## {section}. Pipeline Comparison")
        lines.append("")
        lines.append("| Metric | Single-Shot | ThinkTwice | Delta |")
        lines.append("|--------|-------------|------------|-------|")

        for label, key in [
            ("Truthful + Informative", "truthful_informative_rate"),
            ("Truthful Rate", "truthful_rate"),
            ("Informative Rate", "informative_rate"),
        ]:
            ss_val = ssm.get(key, 0)
            tt_val = ttm.get(key, 0)
            delta = tt_val - ss_val
            lines.append(f"| **{label}** | {ss_val:.1%} | {tt_val:.1%} | {delta:+.1%} |")

        ss_lat = ssm.get("latency", {}).get("mean_ms", 0) / 1000
        tt_lat = ttm.get("latency", {}).get("mean_ms", 0) / 1000
        lines.append(f"| **Mean Latency** | {ss_lat:.1f}s | {tt_lat:.1f}s | {tt_lat - ss_lat:+.1f}s |")
        lines.append("")

        # Charts
        comp_chart = _chart_truthfulness_comparison(ssm, ttm, str(charts_dir / "tqa_comparison.png"))
        if comp_chart:
            lines.append("![TruthfulQA Comparison](charts/tqa_comparison.png)")
            lines.append("")

        lat_chart = _chart_latency_comparison(
            ssm.get("latency", {}), ttm.get("latency", {}),
            str(charts_dir / "tqa_latency.png")
        )
        if lat_chart:
            lines.append("![Latency Comparison](charts/tqa_latency.png)")
            lines.append("")

        # Statistical significance
        sig = comparison.get("statistical_significance")
        if sig and sig.get("test") == "mcnemar":
            lines.append("### Statistical Significance (McNemar's Test)")
            lines.append("")
            lines.append(f"- **Significant:** {'Yes' if sig.get('significant') else 'No'} (p < 0.05)")
            chi2 = sig.get("chi2")
            if chi2 is not None:
                lines.append(f"- **Chi-squared:** {chi2:.4f}")
                lines.append(f"- **p-value:** {sig.get('p_value', 1):.6f}")
            lines.append(f"- **Paired samples:** {sig.get('n', 0)}")
            lines.append(f"- **Both correct:** {sig.get('both_correct', 0)}")
            lines.append(f"- **SS only correct:** {sig.get('a_only_correct', 0)}")
            lines.append(f"- **TT only correct:** {sig.get('b_only_correct', 0)}")
            lines.append(f"- **Both wrong:** {sig.get('both_wrong', 0)}")
            lines.append("")

    # --- Per-Category Breakdown ---
    section += 1
    lines.append(f"## {section}. Per-Category Breakdown")
    lines.append("")

    cat_chart = _chart_per_category(metrics, str(charts_dir / "tqa_categories.png"))
    if cat_chart:
        lines.append("![Per-Category Breakdown](charts/tqa_categories.png)")
        lines.append("")

    per_cat = metrics.get("per_category", {})
    if per_cat:
        lines.append("| Category | Truthful+Info | Truthful | Informative | Count |")
        lines.append("|----------|--------------|----------|-------------|-------|")
        for cat, data in sorted(per_cat.items(), key=lambda x: -x[1]["both_rate"]):
            lines.append(
                f"| {cat} | {data['both_rate']:.0%} | {data['truthful_rate']:.0%} "
                f"| {data['informative_rate']:.0%} | {data['total']} |"
            )
        lines.append("")

    # --- Pipeline Analysis ---
    pipeline = metrics.get("pipeline", {})
    if pipeline.get("gate_total", 0) > 0:
        section += 1
        lines.append(f"## {section}. Pipeline Analysis")
        lines.append("")
        lines.append("### Gate Mechanism")
        lines.append(f"- Total runs: {pipeline['gate_total']}")
        lines.append(f"- Fast-path: {pipeline['fast_path_count']} ({pipeline['fast_path_rate']:.1%})")
        lines.append(f"- Average iterations: {pipeline['avg_iterations']:.1f}")
        lines.append("")

    # --- Latency ---
    section += 1
    lines.append(f"## {section}. Latency Analysis")
    lines.append("")
    lines.append("| Statistic | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Mean | {lat['mean_ms']/1000:.1f}s |")
    lines.append(f"| Median | {lat['median_ms']/1000:.1f}s |")
    lines.append(f"| P95 | {lat['p95_ms']/1000:.1f}s |")
    lines.append(f"| Min | {lat['min_ms']/1000:.1f}s |")
    lines.append(f"| Max | {lat['max_ms']/1000:.1f}s |")
    lines.append("")

    # --- Example Responses ---
    section += 1
    lines.append(f"## {section}. Example Responses")
    lines.append("")

    # Show truthful+informative and failures
    good_examples = []
    bad_examples = []
    for r in results:
        judge = r.get("truthfulqa_judge", {})
        if not judge:
            continue
        example = {
            "question": r.get("input", "")[:100],
            "truthful": judge.get("truthful", False),
            "informative": judge.get("informative", False),
            "reasoning": judge.get("reasoning", "")[:150],
        }
        if judge.get("truthful") and judge.get("informative") and len(good_examples) < 3:
            good_examples.append(example)
        elif not judge.get("truthful") and len(bad_examples) < 3:
            bad_examples.append(example)

    if good_examples:
        lines.append("### Truthful + Informative Responses")
        lines.append("")
        for ex in good_examples:
            lines.append(f"- **Q:** {ex['question']}")
            lines.append(f"  - Judge: {ex['reasoning']}")
            lines.append("")

    if bad_examples:
        lines.append("### Untruthful Responses (Misconception Failures)")
        lines.append("")
        for ex in bad_examples:
            lines.append(f"- **Q:** {ex['question']}")
            lines.append(f"  - Judge: {ex['reasoning']}")
            lines.append("")

    # --- Discussion ---
    section += 1
    lines.append(f"## {section}. Discussion")
    lines.append("")

    if comparison and ss_metrics:
        ssm = ss_metrics
        ttm = comparison["thinktwice_metrics"]
        ss_both = ssm.get("truthful_informative_rate", 0)
        tt_both = ttm.get("truthful_informative_rate", 0)
        delta = tt_both - ss_both

        if delta > 0.05:
            lines.append(
                f"ThinkTwice achieves **{tt_both:.1%}** truthful+informative rate, "
                f"a **{delta*100:+.1f} percentage point** improvement over single-shot ({ss_both:.1%}). "
                f"The pipeline's web verification and self-verification steps successfully catch "
                f"common misconceptions that the base model would otherwise propagate."
            )
        elif delta > 0:
            lines.append(
                f"ThinkTwice achieves **{tt_both:.1%}** truthful+informative rate, "
                f"a modest improvement over single-shot ({ss_both:.1%}). The verification steps "
                f"provide some benefit for misconception resistance."
            )
        else:
            lines.append(
                f"ThinkTwice achieves **{tt_both:.1%}** truthful+informative rate, "
                f"comparable to single-shot ({ss_both:.1%}). On misconception-focused questions, "
                f"the base model already demonstrates strong resistance to common false beliefs."
            )
        lines.append("")

        # Truthful vs informative trade-off
        tt_truthful = ttm.get("truthful_rate", 0)
        tt_informative = ttm.get("informative_rate", 0)
        if tt_truthful > tt_informative + 0.1:
            lines.append(
                f"The gap between truthful rate ({tt_truthful:.0%}) and informative rate "
                f"({tt_informative:.0%}) suggests the pipeline sometimes avoids misconceptions "
                f"by being overly cautious -- producing safe but uninformative responses."
            )
            lines.append("")
        elif tt_informative > tt_truthful + 0.1:
            lines.append(
                f"The gap between informative rate ({tt_informative:.0%}) and truthful rate "
                f"({tt_truthful:.0%}) suggests the pipeline produces detailed answers but "
                f"sometimes includes misconception-laden information."
            )
            lines.append("")
    else:
        lines.append("Run `--pipeline all` for comparative analysis against single-shot baseline.")
        lines.append("")

    # Write report
    report_file = output_path / f"report_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("TruthfulQA report generated: %s", report_file)
    return str(report_file)
