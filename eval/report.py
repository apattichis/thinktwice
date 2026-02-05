"""Professional evaluation report generator with visualizations.

Generates comprehensive Markdown reports with embedded matplotlib charts:
- Radar charts for multi-metric comparison
- Bar charts for v1 vs v2 comparison
- Ablation heatmaps
- Confidence distribution plots
- Per-domain breakdown tables
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from eval.metrics import compute_all_metrics

logger = logging.getLogger(__name__)

# Check for matplotlib availability
try:
    import matplotlib
    matplotlib.use("Agg")  # Non-interactive backend
    import matplotlib.pyplot as plt
    import matplotlib.ticker as mticker
    import numpy as np
    HAS_MATPLOTLIB = True
except ImportError:
    HAS_MATPLOTLIB = False
    logger.warning("matplotlib not available — charts will be skipped")


# Professional color palette
COLORS = {
    "v1": "#FF9500",       # Orange
    "v2": "#007AFF",       # Blue
    "success": "#34C759",  # Green
    "error": "#FF3B30",    # Red
    "warning": "#FF9F0A",  # Amber
    "neutral": "#8E8E93",  # Gray
    "bg": "#F5F5F7",       # Light bg
    "text": "#1D1D1F",     # Dark text
}


def _setup_style():
    """Configure matplotlib for professional-looking charts."""
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


def generate_radar_chart(metrics: dict, output_path: str, title: str = "Pipeline Metrics") -> Optional[str]:
    """Generate a radar chart comparing multiple metric dimensions."""
    if not HAS_MATPLOTLIB:
        return None

    _setup_style()

    categories = [
        "Accuracy", "Constraint\nSatisfaction", "Verification\nRate",
        "Confidence\nDelta", "Gate\nEfficiency", "Speed"
    ]
    n = len(categories)

    # Extract values (normalize to 0-1)
    values = [
        metrics.get("accuracy", {}).get("accuracy", 0),
        metrics.get("constraint_satisfaction", {}).get("satisfaction_rate", 0),
        metrics.get("verification", {}).get("verification_rate", 0),
        min(max(metrics.get("refinement_delta", {}).get("positive_rate", 0), 0), 1),
        metrics.get("gate_efficiency", {}).get("fast_path_rate", 0),
        max(0, 1 - (metrics.get("latency", {}).get("mean_ms", 30000) / 60000)),  # Inverse latency
    ]

    angles = [i / float(n) * 2 * 3.14159 for i in range(n)]
    values_plot = values + [values[0]]
    angles_plot = angles + [angles[0]]

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
    ax.fill(angles_plot, values_plot, color=COLORS["v2"], alpha=0.15)
    ax.plot(angles_plot, values_plot, color=COLORS["v2"], linewidth=2.5, marker="o", markersize=8)

    ax.set_xticks(angles)
    ax.set_xticklabels(categories, fontweight="medium")
    ax.set_ylim(0, 1)
    ax.set_yticks([0.2, 0.4, 0.6, 0.8, 1.0])
    ax.set_yticklabels(["20%", "40%", "60%", "80%", "100%"], fontsize=8, color="#8E8E93")
    ax.set_title(title, pad=20, fontsize=16, fontweight="bold", color=COLORS["text"])

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_comparison_bars(v1_metrics: dict, v2_metrics: dict, output_path: str) -> Optional[str]:
    """Generate side-by-side bar chart comparing v1 vs v2."""
    if not HAS_MATPLOTLIB:
        return None

    _setup_style()

    labels = [
        "Accuracy", "Constraint\nSatisfaction", "Verification\nRate",
        "Confidence\nAfter", "Refinement\nDelta"
    ]

    v1_vals = [
        v1_metrics.get("accuracy", {}).get("accuracy", 0) * 100,
        v1_metrics.get("constraint_satisfaction", {}).get("satisfaction_rate", 0) * 100,
        v1_metrics.get("verification", {}).get("verification_rate", 0) * 100,
        v1_metrics.get("refinement_delta", {}).get("mean_delta", 0) + 50,  # Normalize
        v1_metrics.get("refinement_delta", {}).get("positive_rate", 0) * 100,
    ]

    v2_vals = [
        v2_metrics.get("accuracy", {}).get("accuracy", 0) * 100,
        v2_metrics.get("constraint_satisfaction", {}).get("satisfaction_rate", 0) * 100,
        v2_metrics.get("verification", {}).get("verification_rate", 0) * 100,
        v2_metrics.get("refinement_delta", {}).get("mean_delta", 0) + 50,
        v2_metrics.get("refinement_delta", {}).get("positive_rate", 0) * 100,
    ]

    x = range(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 6))
    bars1 = ax.bar([i - width/2 for i in x], v1_vals, width, label="v1 (Linear)", color=COLORS["v1"], alpha=0.85, edgecolor="white", linewidth=0.5)
    bars2 = ax.bar([i + width/2 for i in x], v2_vals, width, label="v2 (Research)", color=COLORS["v2"], alpha=0.85, edgecolor="white", linewidth=0.5)

    ax.set_xlabel("")
    ax.set_ylabel("Score (%)")
    ax.set_title("v1 vs v2 Pipeline Comparison", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")
    ax.set_ylim(0, 105)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())

    # Value labels on bars
    for bar in bars1:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8, color=COLORS["v1"])
    for bar in bars2:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{bar.get_height():.0f}%', ha='center', va='bottom', fontsize=8, color=COLORS["v2"])

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_domain_breakdown(results: list[dict], output_path: str) -> Optional[str]:
    """Generate per-domain accuracy breakdown chart."""
    if not HAS_MATPLOTLIB:
        return None

    _setup_style()

    # Compute per-domain metrics
    domains = {}
    for r in results:
        domain = r.get("domain", "unknown")
        if domain not in domains:
            domains[domain] = {"correct": 0, "total": 0}
        domains[domain]["total"] += 1
        # Simplified accuracy check
        gold = r.get("gold_verdict", "")
        output = r.get("output", "").lower()
        if gold == "true" and ("verified" in output or "true" in output or "accurate" in output):
            domains[domain]["correct"] += 1
        elif gold == "false" and ("refuted" in output or "false" in output or "incorrect" in output):
            domains[domain]["correct"] += 1
        elif gold == "partial" and ("partial" in output or "nuance" in output):
            domains[domain]["correct"] += 1

    if not domains:
        return None

    sorted_domains = sorted(domains.items(), key=lambda x: x[1]["total"], reverse=True)
    names = [d[0].replace("_", " ").title() for d in sorted_domains]
    accuracies = [d[1]["correct"] / d[1]["total"] * 100 if d[1]["total"] > 0 else 0 for d in sorted_domains]
    counts = [d[1]["total"] for d in sorted_domains]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(names, accuracies, color=COLORS["v2"], alpha=0.85, edgecolor="white", height=0.6)

    ax.set_xlabel("Accuracy (%)")
    ax.set_title("Accuracy by Domain", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xlim(0, 105)
    ax.invert_yaxis()

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2,
                f'{bar.get_width():.0f}% (n={count})', va='center', fontsize=9)

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_latency_distribution(results: list[dict], output_path: str) -> Optional[str]:
    """Generate latency distribution histogram."""
    if not HAS_MATPLOTLIB:
        return None

    _setup_style()

    durations = [r.get("duration_ms", 0) / 1000 for r in results if r.get("duration_ms")]
    if not durations:
        return None

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(durations, bins=20, color=COLORS["v2"], alpha=0.8, edgecolor="white", linewidth=0.5)

    mean_d = sum(durations) / len(durations)
    ax.axvline(mean_d, color=COLORS["error"], linestyle="--", linewidth=2, label=f"Mean: {mean_d:.1f}s")

    ax.set_xlabel("Duration (seconds)")
    ax.set_ylabel("Count")
    ax.set_title("Pipeline Latency Distribution", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_report(
    results: list[dict],
    dataset_name: str,
    output_dir: str = "results",
    comparison: Optional[dict] = None,
    ablation_results: Optional[dict] = None,
    single_shot_metrics: Optional[dict] = None,
) -> str:
    """Generate a comprehensive evaluation report.

    Args:
        results: Primary evaluation results (v2).
        dataset_name: Name of the dataset.
        output_dir: Directory for output files.
        comparison: Optional v1 vs v2 comparison data.
        ablation_results: Optional ablation study results.
        single_shot_metrics: Optional single-shot baseline metrics.

    Returns:
        Path to the generated report.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    charts_dir = output_path / "charts"
    charts_dir.mkdir(exist_ok=True)

    metrics = compute_all_metrics(results)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append(f"# ThinkTwice Evaluation Report")
    lines.append(f"")
    lines.append(f"**Dataset:** {dataset_name}  ")
    lines.append(f"**Generated:** {timestamp}  ")
    lines.append(f"**Total Samples:** {len(results)}  ")
    lines.append(f"")

    # --- Executive Summary ---
    lines.append("## Executive Summary")
    lines.append("")
    acc = metrics["accuracy"]
    cs = metrics["constraint_satisfaction"]
    ver = metrics["verification"]
    gate = metrics["gate_efficiency"]
    trust = metrics["trust"]
    lat = metrics["latency"]
    ref = metrics["refinement_delta"]

    lines.append(f"| Metric | Value |")
    lines.append(f"|--------|-------|")
    lines.append(f"| **Accuracy** | {acc['accuracy']:.1%} ({acc['correct']}/{acc['total']}) |")
    lines.append(f"| **Constraint Satisfaction** | {cs['satisfaction_rate']:.1%} ({cs['satisfied']}/{cs['total']}) |")
    lines.append(f"| **Claims Verified** | {ver['verified']}/{ver['total_claims']} ({ver['verification_rate']:.1%}) |")
    lines.append(f"| **Claims Refuted** | {ver['refuted']}/{ver['total_claims']} ({ver['refutation_rate']:.1%}) |")
    lines.append(f"| **Gate Fast-Path Rate** | {gate['fast_path_rate']:.1%} |")
    lines.append(f"| **Avg Iterations** | {gate['avg_iterations']:.1f} |")
    lines.append(f"| **Trust: Draft Wins** | {trust['draft_wins']}/{trust['total_runs']} ({trust['draft_override_rate']:.1%}) |")
    lines.append(f"| **Mean Confidence Delta** | {ref['mean_delta']:+.1f} |")
    lines.append(f"| **Mean Latency** | {lat['mean_ms']/1000:.1f}s |")
    lines.append(f"| **P95 Latency** | {lat['p95_ms']/1000:.1f}s |")
    lines.append("")

    # Radar chart
    radar_path = generate_radar_chart(metrics, str(charts_dir / "radar.png"), f"{dataset_name} — Pipeline Metrics")
    if radar_path:
        lines.append(f"![Pipeline Metrics Radar](charts/radar.png)")
        lines.append("")

    # --- 3-Way Baseline Comparison ---
    if comparison or single_shot_metrics:
        lines.append("## Baseline Comparison")
        lines.append("")

        if single_shot_metrics and comparison:
            ssm = single_shot_metrics
            v1m = comparison["v1_metrics"]
            v2m = comparison["v2_metrics"]

            lines.append("| Metric | Single-Shot | V1 (Linear) | V2 (Research) |")
            lines.append("|--------|-------------|-------------|---------------|")
            lines.append(f"| **Accuracy** | {ssm['accuracy']['accuracy']:.1%} | {v1m['accuracy']['accuracy']:.1%} | {v2m['accuracy']['accuracy']:.1%} |")
            lines.append(f"| **Mean Latency** | {ssm['latency']['mean_ms']/1000:.1f}s | {v1m['latency']['mean_ms']/1000:.1f}s | {v2m['latency']['mean_ms']/1000:.1f}s |")
            lines.append(f"| **Claims Verified** | N/A | {v1m['verification']['verified']} | {v2m['verification']['verified']} |")
            lines.append(f"| **Claims Refuted** | N/A | {v1m['verification']['refuted']} | {v2m['verification']['refuted']} |")
            lines.append(f"| **Constraint Satisfaction** | N/A | N/A | {v2m['constraint_satisfaction']['satisfaction_rate']:.1%} |")
            lines.append(f"| **Gate Fast-Path** | N/A | N/A | {v2m['gate_efficiency']['fast_path_rate']:.1%} |")
            lines.append("")

            # Improvement over single-shot
            ss_acc = ssm['accuracy']['accuracy']
            v2_acc = v2m['accuracy']['accuracy']
            if ss_acc > 0:
                improvement = ((v2_acc - ss_acc) / ss_acc) * 100
                lines.append(f"> **V2 improves accuracy by {improvement:+.1f}% over single-shot baseline.**")
                lines.append("")

        elif comparison:
            # V1 vs V2 only
            v1m = comparison["v1_metrics"]
            v2m = comparison["v2_metrics"]

            lines.append("| Metric | V1 (Linear) | V2 (Research) | Delta |")
            lines.append("|--------|-------------|---------------|-------|")
            lines.append(f"| Accuracy | {v1m['accuracy']['accuracy']:.1%} | {v2m['accuracy']['accuracy']:.1%} | {v2m['accuracy']['accuracy'] - v1m['accuracy']['accuracy']:+.1%} |")
            lines.append(f"| Mean Latency | {v1m['latency']['mean_ms']/1000:.1f}s | {v2m['latency']['mean_ms']/1000:.1f}s | {(v2m['latency']['mean_ms'] - v1m['latency']['mean_ms'])/1000:+.1f}s |")
            lines.append("")

        comp_bars = generate_comparison_bars(
            comparison["v1_metrics"] if comparison else metrics,
            comparison["v2_metrics"] if comparison else metrics,
            str(charts_dir / "comparison.png")
        )
        if comp_bars:
            lines.append(f"![Baseline Comparison](charts/comparison.png)")
            lines.append("")

        if comparison:
            paired = comparison.get("paired_comparison", {})
            lines.append(f"**Paired Comparison ({paired.get('total_paired', 0)} samples):**")
            lines.append(f"- V2 improved: {paired.get('v2_improved_count', 0)}")
            lines.append(f"- Same: {paired.get('v2_same_count', 0)}")
            lines.append(f"- V2 regressed: {paired.get('v2_regressed_count', 0)}")
            lines.append(f"- Mean confidence delta: {paired.get('mean_confidence_delta', 0):+.1f}")
            lines.append("")

            sig = comparison.get("statistical_significance")
            if sig:
                lines.append(f"**Statistical Significance:** {'Yes' if sig.get('significant') else 'No'} (t={sig.get('t_stat', 0):.2f}, p={sig.get('p_approx', 1):.4f})")
                lines.append("")

    # --- Per-Domain Breakdown ---
    domain_chart = generate_domain_breakdown(results, str(charts_dir / "domains.png"))
    if domain_chart:
        lines.append("## Per-Domain Breakdown")
        lines.append("")
        lines.append(f"![Domain Breakdown](charts/domains.png)")
        lines.append("")

    per_domain = acc.get("per_domain", {})
    if per_domain:
        lines.append(f"| Domain | Accuracy | Samples |")
        lines.append(f"|--------|----------|---------|")
        for domain, data in sorted(per_domain.items()):
            lines.append(f"| {domain.replace('_', ' ').title()} | {data['accuracy']:.1%} | {data['total']} |")
        lines.append("")

    # --- Latency Analysis ---
    latency_chart = generate_latency_distribution(results, str(charts_dir / "latency.png"))
    if latency_chart:
        lines.append("## Latency Analysis")
        lines.append("")
        lines.append(f"![Latency Distribution](charts/latency.png)")
        lines.append("")

    lines.append(f"| Statistic | Value |")
    lines.append(f"|-----------|-------|")
    lines.append(f"| Mean | {lat['mean_ms']/1000:.1f}s |")
    lines.append(f"| Median | {lat['median_ms']/1000:.1f}s |")
    lines.append(f"| P95 | {lat['p95_ms']/1000:.1f}s |")
    lines.append(f"| Min | {lat['min_ms']/1000:.1f}s |")
    lines.append(f"| Max | {lat['max_ms']/1000:.1f}s |")
    lines.append("")

    # --- Ablation Results ---
    if ablation_results:
        lines.append("## Ablation Study")
        lines.append("")
        lines.append("| Configuration | Accuracy | Constraint Sat. | Mean Latency | Iterations |")
        lines.append("|---------------|----------|-----------------|-------------|------------|")

        for config_name, config_results in ablation_results.items():
            config_metrics = compute_all_metrics(config_results)
            cm_acc = config_metrics["accuracy"]["accuracy"]
            cm_cs = config_metrics["constraint_satisfaction"]["satisfaction_rate"]
            cm_lat = config_metrics["latency"]["mean_ms"] / 1000
            cm_iter = config_metrics["gate_efficiency"]["avg_iterations"]
            lines.append(f"| {config_name} | {cm_acc:.1%} | {cm_cs:.1%} | {cm_lat:.1f}s | {cm_iter:.1f} |")
        lines.append("")

    # --- Gate Analysis ---
    lines.append("## Gate Analysis")
    lines.append("")
    lines.append(f"- **Total runs:** {gate['total_runs']}")
    lines.append(f"- **Fast-path (skipped refinement):** {gate['fast_path_count']} ({gate['fast_path_rate']:.1%})")
    lines.append(f"- **Average iterations when refining:** {gate['avg_iterations']:.1f}")
    lines.append("")

    # --- Trust Analysis ---
    lines.append("## Trust & Rank Analysis")
    lines.append("")
    lines.append(f"- **Draft wins:** {trust['draft_wins']} ({trust['draft_override_rate']:.1%})")
    lines.append(f"- **Refined wins:** {trust['refined_wins']}")
    lines.append(f"- **Blended:** {trust['blended']}")
    lines.append(f"- **Avg draft score:** {trust['avg_draft_score']:.1f}")
    lines.append(f"- **Avg refined score:** {trust['avg_refined_score']:.1f}")
    lines.append("")

    # Write report
    report_path = output_path / f"report_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Report generated: %s", report_path)
    return str(report_path)
