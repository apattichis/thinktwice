"""Professional evaluation report generator with visualizations.

Generates comprehensive Markdown reports with embedded matplotlib charts:
- Radar charts for multi-metric overview
- 3-way bar charts (single-shot vs v1 vs v2)
- Per-class F1 breakdown charts
- Per-domain and per-difficulty accuracy
- Ablation study comparison
- Latency distribution
- Statistical significance reporting
"""

import json
import logging
import math
from datetime import datetime
from pathlib import Path
from typing import Optional

from eval.metrics import compute_all_metrics, _classify_output

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
    logger.warning("matplotlib not available — charts will be skipped")


COLORS = {
    "ss": "#8E8E93",       # Gray — single-shot
    "v1": "#FF9500",       # Orange — v1
    "v2": "#007AFF",       # Blue — v2
    "success": "#34C759",
    "error": "#FF3B30",
    "warning": "#FF9F0A",
    "neutral": "#C7C7CC",
    "text": "#1D1D1F",
    "true": "#34C759",     # Green
    "false": "#FF3B30",    # Red
    "partial": "#FF9F0A",  # Amber
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


def generate_radar_chart(metrics: dict, output_path: str, title: str = "Pipeline Metrics") -> Optional[str]:
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    categories = ["Accuracy", "Macro F1", "Constraint\nSatisfaction", "Verification\nRate", "Gate\nEfficiency", "Speed"]
    n = len(categories)
    values = [
        metrics.get("accuracy", {}).get("accuracy", 0),
        metrics.get("classification", {}).get("macro", {}).get("f1", 0),
        metrics.get("constraint_satisfaction", {}).get("satisfaction_rate", 0),
        metrics.get("verification", {}).get("verification_rate", 0),
        metrics.get("gate_efficiency", {}).get("fast_path_rate", 0),
        max(0, 1 - (metrics.get("latency", {}).get("mean_ms", 30000) / 60000)),
    ]

    angles = [i / float(n) * 2 * math.pi for i in range(n)]
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


def generate_three_way_comparison(ss_metrics: dict, v1_metrics: dict, v2_metrics: dict, output_path: str) -> Optional[str]:
    """Generate 3-way grouped bar chart: single-shot vs v1 vs v2."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    labels = ["Accuracy", "Macro F1", "Weighted F1"]
    ss_vals = [
        ss_metrics.get("accuracy", {}).get("accuracy", 0) * 100,
        ss_metrics.get("classification", {}).get("macro", {}).get("f1", 0) * 100,
        ss_metrics.get("classification", {}).get("weighted", {}).get("f1", 0) * 100,
    ]
    v1_vals = [
        v1_metrics.get("accuracy", {}).get("accuracy", 0) * 100,
        v1_metrics.get("classification", {}).get("macro", {}).get("f1", 0) * 100,
        v1_metrics.get("classification", {}).get("weighted", {}).get("f1", 0) * 100,
    ]
    v2_vals = [
        v2_metrics.get("accuracy", {}).get("accuracy", 0) * 100,
        v2_metrics.get("classification", {}).get("macro", {}).get("f1", 0) * 100,
        v2_metrics.get("classification", {}).get("weighted", {}).get("f1", 0) * 100,
    ]

    x = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 6))

    bars_ss = ax.bar(x - width, ss_vals, width, label="Single-Shot", color=COLORS["ss"], alpha=0.85, edgecolor="white")
    bars_v1 = ax.bar(x, v1_vals, width, label="V1 (Linear)", color=COLORS["v1"], alpha=0.85, edgecolor="white")
    bars_v2 = ax.bar(x + width, v2_vals, width, label="V2 (Research)", color=COLORS["v2"], alpha=0.85, edgecolor="white")

    ax.set_ylabel("Score (%)")
    ax.set_title("Pipeline Comparison: Accuracy & F1", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")
    ax.set_ylim(0, 105)

    for bars in [bars_ss, bars_v1, bars_v2]:
        for bar in bars:
            h = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.1f}%', ha='center', va='bottom', fontsize=8)

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_per_class_f1_chart(ss_clf: dict, v1_clf: dict, v2_clf: dict, output_path: str) -> Optional[str]:
    """Generate per-class F1 chart across all 3 baselines."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    classes = ["true", "false", "partial"]
    labels = ["True", "False", "Partial"]
    ss_f1 = [ss_clf.get("per_class", {}).get(c, {}).get("f1", 0) * 100 for c in classes]
    v1_f1 = [v1_clf.get("per_class", {}).get(c, {}).get("f1", 0) * 100 for c in classes]
    v2_f1 = [v2_clf.get("per_class", {}).get(c, {}).get("f1", 0) * 100 for c in classes]

    x = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 6))

    ax.bar(x - width, ss_f1, width, label="Single-Shot", color=COLORS["ss"], alpha=0.85, edgecolor="white")
    ax.bar(x, v1_f1, width, label="V1 (Linear)", color=COLORS["v1"], alpha=0.85, edgecolor="white")
    ax.bar(x + width, v2_f1, width, label="V2 (Research)", color=COLORS["v2"], alpha=0.85, edgecolor="white")

    ax.set_ylabel("F1 Score (%)")
    ax.set_title("Per-Class F1 Score Comparison", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")
    ax.set_ylim(0, 105)

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_difficulty_chart(results: list[dict], output_path: str) -> Optional[str]:
    """Generate accuracy by difficulty level chart."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    acc = compute_all_metrics(results)["accuracy"]
    per_diff = acc.get("per_difficulty", {})
    if not per_diff:
        return None

    order = ["easy", "medium", "hard"]
    names = [d.title() for d in order if d in per_diff]
    accuracies = [per_diff[d]["accuracy"] * 100 for d in order if d in per_diff]
    counts = [per_diff[d]["total"] for d in order if d in per_diff]
    colors = [COLORS["success"], COLORS["warning"], COLORS["error"]]

    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(names, accuracies, color=colors[:len(names)], alpha=0.85, edgecolor="white", width=0.5)

    for bar, count in zip(bars, counts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 1.5,
                f'{bar.get_height():.1f}%\n(n={count})', ha='center', va='bottom', fontsize=9)

    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy by Difficulty Level", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_ylim(0, 110)

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_domain_breakdown(results: list[dict], output_path: str) -> Optional[str]:
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    domains = {}
    for r in results:
        domain = r.get("domain", "unknown")
        if domain not in domains:
            domains[domain] = {"correct": 0, "total": 0}
        gold = r.get("gold_verdict")
        if gold is None:
            continue
        domains[domain]["total"] += 1
        predicted = _classify_output(r.get("output", ""))
        is_correct = False
        if gold in ("true", True) and predicted == "true":
            is_correct = True
        elif gold in ("false", False) and predicted == "false":
            is_correct = True
        elif gold == "partial" and predicted in ("partial", "true"):
            is_correct = True
        if is_correct:
            domains[domain]["correct"] += 1

    if not domains:
        return None

    sorted_domains = sorted(domains.items(), key=lambda x: x[1]["total"], reverse=True)
    names = [d[0].replace("_", " ").title() for d in sorted_domains]
    accuracies = [d[1]["correct"] / d[1]["total"] * 100 if d[1]["total"] > 0 else 0 for d in sorted_domains]
    counts = [d[1]["total"] for d in sorted_domains]

    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.5 + 2)))
    bars = ax.barh(names, accuracies, color=COLORS["v2"], alpha=0.85, edgecolor="white", height=0.6)

    ax.set_xlabel("Accuracy (%)")
    ax.set_title("Accuracy by Domain", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xlim(0, 115)
    ax.invert_yaxis()

    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + 1.5, bar.get_y() + bar.get_height()/2,
                f'{bar.get_width():.0f}% (n={count})', va='center', fontsize=9)

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_latency_comparison(ss_lat: dict, v1_lat: dict, v2_lat: dict, output_path: str) -> Optional[str]:
    """Generate latency comparison box-style chart."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    labels = ["Single-Shot", "V1 (Linear)", "V2 (Research)"]
    means = [ss_lat.get("mean_ms", 0)/1000, v1_lat.get("mean_ms", 0)/1000, v2_lat.get("mean_ms", 0)/1000]
    p95s = [ss_lat.get("p95_ms", 0)/1000, v1_lat.get("p95_ms", 0)/1000, v2_lat.get("p95_ms", 0)/1000]
    colors = [COLORS["ss"], COLORS["v1"], COLORS["v2"]]

    x = np.arange(len(labels))
    width = 0.35
    fig, ax = plt.subplots(figsize=(9, 5))

    bars_mean = ax.bar(x - width/2, means, width, label="Mean", color=colors, alpha=0.85, edgecolor="white")
    bars_p95 = ax.bar(x + width/2, p95s, width, label="P95", color=colors, alpha=0.45, edgecolor="white")

    for bar in bars_mean:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{bar.get_height():.1f}s', ha='center', va='bottom', fontsize=9)
    for bar in bars_p95:
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{bar.get_height():.1f}s', ha='center', va='bottom', fontsize=9)

    ax.set_ylabel("Duration (seconds)")
    ax.set_title("Latency Comparison", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_latency_distribution(results: list[dict], output_path: str) -> Optional[str]:
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
    ax.set_title("V2 Pipeline Latency Distribution", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_ablation_chart(ablation_results: dict, output_path: str) -> Optional[str]:
    """Generate ablation study comparison chart."""
    if not HAS_MATPLOTLIB or not ablation_results:
        return None
    _setup_style()

    configs = []
    accuracies = []
    f1s = []
    latencies = []

    for name, results in ablation_results.items():
        m = compute_all_metrics(results)
        configs.append(name.replace("v2_", "").replace("_", "\n"))
        accuracies.append(m["accuracy"]["accuracy"] * 100)
        f1s.append(m["classification"]["macro"]["f1"] * 100)
        latencies.append(m["latency"]["mean_ms"] / 1000)

    x = np.arange(len(configs))
    width = 0.35
    fig, ax1 = plt.subplots(figsize=(14, 6))

    bars1 = ax1.bar(x - width/2, accuracies, width, label="Accuracy (%)", color=COLORS["v2"], alpha=0.85, edgecolor="white")
    bars2 = ax1.bar(x + width/2, f1s, width, label="Macro F1 (%)", color=COLORS["success"], alpha=0.85, edgecolor="white")
    ax1.set_ylabel("Score (%)")
    ax1.set_ylim(0, 110)

    ax2 = ax1.twinx()
    ax2.plot(x, latencies, color=COLORS["error"], marker="s", linewidth=2, markersize=8, label="Latency (s)")
    ax2.set_ylabel("Mean Latency (s)", color=COLORS["error"])

    ax1.set_xticks(x)
    ax1.set_xticklabels(configs, fontsize=9)
    ax1.set_title("Ablation Study Results", fontsize=16, fontweight="bold", color=COLORS["text"])

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, framealpha=0.9, edgecolor="#E5E5E5")

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
    """Generate a comprehensive evaluation report with all charts and analysis."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    charts_dir = output_path / "charts"
    charts_dir.mkdir(exist_ok=True)

    metrics = compute_all_metrics(results)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    lines = []
    lines.append("# ThinkTwice Evaluation Report")
    lines.append("")
    lines.append(f"**Dataset:** {dataset_name}  ")
    lines.append(f"**Generated:** {timestamp}  ")
    lines.append(f"**Total Samples:** {len(results)}  ")
    lines.append(f"**Pipeline Version:** V2 (Research-inspired self-correcting pipeline)  ")
    lines.append("")

    # ─── Executive Summary ───
    lines.append("## 1. Executive Summary")
    lines.append("")

    acc = metrics["accuracy"]
    clf = metrics["classification"]
    cs = metrics["constraint_satisfaction"]
    ver = metrics["verification"]
    gate = metrics["gate_efficiency"]
    trust = metrics["trust"]
    lat = metrics["latency"]
    ref = metrics["refinement_delta"]

    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    lines.append(f"| **Accuracy** | {acc['accuracy']:.1%} ({acc['correct']}/{acc['total']}) |")
    lines.append(f"| **Macro F1** | {clf['macro']['f1']:.3f} |")
    lines.append(f"| **Weighted F1** | {clf['weighted']['f1']:.3f} |")
    lines.append(f"| **Macro Precision** | {clf['macro']['precision']:.3f} |")
    lines.append(f"| **Macro Recall** | {clf['macro']['recall']:.3f} |")
    lines.append(f"| **Mean Latency** | {lat['mean_ms']/1000:.1f}s |")
    lines.append(f"| **P95 Latency** | {lat['p95_ms']/1000:.1f}s |")
    lines.append("")

    radar_path = generate_radar_chart(metrics, str(charts_dir / "radar.png"), f"{dataset_name} — V2 Pipeline Metrics")
    if radar_path:
        lines.append("![Pipeline Metrics Radar](charts/radar.png)")
        lines.append("")

    # ─── Per-Class Classification ───
    lines.append("## 2. Per-Class Classification Metrics")
    lines.append("")
    lines.append("| Class | Precision | Recall | F1 | Support |")
    lines.append("|-------|-----------|--------|-----|---------|")
    for cls in ["true", "false", "partial"]:
        pc = clf["per_class"].get(cls, {})
        lines.append(f"| **{cls.title()}** | {pc.get('precision', 0):.3f} | {pc.get('recall', 0):.3f} | {pc.get('f1', 0):.3f} | {pc.get('support', 0)} |")
    lines.append(f"| **Macro Avg** | {clf['macro']['precision']:.3f} | {clf['macro']['recall']:.3f} | {clf['macro']['f1']:.3f} | {acc['total']} |")
    lines.append(f"| **Weighted Avg** | {clf['weighted']['precision']:.3f} | {clf['weighted']['recall']:.3f} | {clf['weighted']['f1']:.3f} | {acc['total']} |")
    lines.append("")

    # ─── 3-Way Baseline Comparison ───
    if comparison and single_shot_metrics:
        ssm = single_shot_metrics
        v1m = comparison["v1_metrics"]
        v2m = comparison["v2_metrics"]

        lines.append("## 3. Baseline Comparison")
        lines.append("")
        lines.append("| Metric | Single-Shot | V1 (Linear) | V2 (Research) |")
        lines.append("|--------|-------------|-------------|---------------|")
        lines.append(f"| **Accuracy** | {ssm['accuracy']['accuracy']:.1%} | {v1m['accuracy']['accuracy']:.1%} | {v2m['accuracy']['accuracy']:.1%} |")
        lines.append(f"| **Macro F1** | {ssm['classification']['macro']['f1']:.3f} | {v1m['classification']['macro']['f1']:.3f} | {v2m['classification']['macro']['f1']:.3f} |")
        lines.append(f"| **Weighted F1** | {ssm['classification']['weighted']['f1']:.3f} | {v1m['classification']['weighted']['f1']:.3f} | {v2m['classification']['weighted']['f1']:.3f} |")
        lines.append(f"| **Mean Latency** | {ssm['latency']['mean_ms']/1000:.1f}s | {v1m['latency']['mean_ms']/1000:.1f}s | {v2m['latency']['mean_ms']/1000:.1f}s |")
        lines.append(f"| **P95 Latency** | {ssm['latency']['p95_ms']/1000:.1f}s | {v1m['latency']['p95_ms']/1000:.1f}s | {v2m['latency']['p95_ms']/1000:.1f}s |")
        lines.append("")

        # Per-class F1 comparison
        lines.append("**Per-Class F1 by Pipeline:**")
        lines.append("")
        lines.append("| Class | Single-Shot | V1 | V2 |")
        lines.append("|-------|-------------|-----|-----|")
        for cls in ["true", "false", "partial"]:
            ss_f1 = ssm['classification']['per_class'].get(cls, {}).get('f1', 0)
            v1_f1 = v1m['classification']['per_class'].get(cls, {}).get('f1', 0)
            v2_f1 = v2m['classification']['per_class'].get(cls, {}).get('f1', 0)
            lines.append(f"| **{cls.title()}** | {ss_f1:.3f} | {v1_f1:.3f} | {v2_f1:.3f} |")
        lines.append("")

        # Improvement summary
        ss_acc = ssm['accuracy']['accuracy']
        v1_acc = v1m['accuracy']['accuracy']
        v2_acc = v2m['accuracy']['accuracy']
        lines.append("**Key Findings:**")
        if ss_acc > 0:
            lines.append(f"- V2 accuracy vs single-shot: {v2_acc - ss_acc:+.1%} ({((v2_acc - ss_acc) / ss_acc) * 100:+.1f}% relative)")
        if v1_acc > 0:
            lines.append(f"- V2 accuracy vs V1: {v2_acc - v1_acc:+.1%} ({((v2_acc - v1_acc) / v1_acc) * 100:+.1f}% relative)")
        lines.append(f"- V2 latency overhead vs single-shot: {(v2m['latency']['mean_ms'] - ssm['latency']['mean_ms'])/1000:+.1f}s")
        lines.append("")

        # Charts
        comp_chart = generate_three_way_comparison(ssm, v1m, v2m, str(charts_dir / "comparison.png"))
        if comp_chart:
            lines.append("![Baseline Comparison](charts/comparison.png)")
            lines.append("")

        f1_chart = generate_per_class_f1_chart(ssm["classification"], v1m["classification"], v2m["classification"], str(charts_dir / "per_class_f1.png"))
        if f1_chart:
            lines.append("![Per-Class F1](charts/per_class_f1.png)")
            lines.append("")

        lat_chart = generate_latency_comparison(ssm["latency"], v1m["latency"], v2m["latency"], str(charts_dir / "latency_comparison.png"))
        if lat_chart:
            lines.append("![Latency Comparison](charts/latency_comparison.png)")
            lines.append("")

        # Statistical significance
        sig = comparison.get("statistical_significance")
        if sig:
            lines.append("### Statistical Significance (Paired t-test)")
            lines.append("")
            lines.append(f"- **Significant:** {'Yes' if sig.get('significant') else 'No'} (p < 0.05)")
            lines.append(f"- **t-statistic:** {sig.get('t_stat', 0):.4f}")
            lines.append(f"- **p-value:** {sig.get('p_approx', 1):.6f}")
            lines.append(f"- **Mean confidence delta (V2 - V1):** {sig.get('mean_delta', 0):+.2f}")
            lines.append(f"- **Standard error:** {sig.get('std_err', 0):.4f}")
            lines.append(f"- **Paired samples:** {sig.get('n', 0)}")
            lines.append("")

        # Paired analysis
        paired = comparison.get("paired_comparison", {})
        if paired:
            lines.append("### Paired Sample Analysis")
            lines.append("")
            lines.append(f"- V2 improved confidence: **{paired.get('v2_improved_count', 0)}** samples")
            lines.append(f"- No change: **{paired.get('v2_same_count', 0)}** samples")
            lines.append(f"- V2 regressed: **{paired.get('v2_regressed_count', 0)}** samples")
            lines.append(f"- Mean confidence delta: **{paired.get('mean_confidence_delta', 0):+.1f}**")
            lines.append(f"- Mean latency delta: **{paired.get('mean_duration_delta_ms', 0)/1000:+.1f}s**")
            lines.append("")

    # ─── Per-Domain Breakdown ───
    lines.append("## 4. Per-Domain Breakdown")
    lines.append("")
    domain_chart = generate_domain_breakdown(results, str(charts_dir / "domains.png"))
    if domain_chart:
        lines.append("![Domain Breakdown](charts/domains.png)")
        lines.append("")

    per_domain = acc.get("per_domain", {})
    if per_domain:
        lines.append("| Domain | Accuracy | Correct | Total |")
        lines.append("|--------|----------|---------|-------|")
        for domain, data in sorted(per_domain.items(), key=lambda x: x[1]["accuracy"], reverse=True):
            lines.append(f"| {domain.replace('_', ' ').title()} | {data['accuracy']:.1%} | {data['correct']} | {data['total']} |")
        lines.append("")

    # ─── Per-Difficulty Breakdown ───
    per_diff = acc.get("per_difficulty", {})
    if per_diff:
        lines.append("## 5. Per-Difficulty Breakdown")
        lines.append("")

        diff_chart = generate_difficulty_chart(results, str(charts_dir / "difficulty.png"))
        if diff_chart:
            lines.append("![Difficulty Breakdown](charts/difficulty.png)")
            lines.append("")

        lines.append("| Difficulty | Accuracy | Correct | Total |")
        lines.append("|-----------|----------|---------|-------|")
        for diff in ["easy", "medium", "hard"]:
            if diff in per_diff:
                d = per_diff[diff]
                lines.append(f"| {diff.title()} | {d['accuracy']:.1%} | {d['correct']} | {d['total']} |")
        lines.append("")

    # ─── V2 Pipeline-Specific Metrics ───
    lines.append("## 6. V2 Pipeline Analysis")
    lines.append("")

    lines.append("### Gate Mechanism")
    lines.append(f"- Total runs: {gate['total_runs']}")
    lines.append(f"- Fast-path (skipped refinement): {gate['fast_path_count']} ({gate['fast_path_rate']:.1%})")
    lines.append(f"- Average iterations when refining: {gate['avg_iterations']:.1f}")
    lines.append("")

    lines.append("### Constraint Satisfaction")
    lines.append(f"- Total constraints evaluated: {cs['total']}")
    lines.append(f"- Satisfied: {cs['satisfied']} ({cs['satisfaction_rate']:.1%})")
    lines.append("")

    lines.append("### Verification")
    lines.append(f"- Total claims checked: {ver['total_claims']}")
    lines.append(f"- Verified: {ver['verified']} ({ver['verification_rate']:.1%})")
    lines.append(f"- Refuted: {ver['refuted']} ({ver['refutation_rate']:.1%})")
    lines.append(f"- Unclear: {ver['unclear']}")
    lines.append("")

    lines.append("### Trust & Rank")
    lines.append(f"- Draft wins: {trust['draft_wins']} ({trust['draft_override_rate']:.1%})")
    lines.append(f"- Refined wins: {trust['refined_wins']}")
    lines.append(f"- Blended: {trust['blended']}")
    lines.append(f"- Avg draft score: {trust['avg_draft_score']:.1f}")
    lines.append(f"- Avg refined score: {trust['avg_refined_score']:.1f}")
    lines.append("")

    lines.append("### Refinement Delta")
    lines.append(f"- Mean confidence delta: {ref['mean_delta']:+.1f}")
    lines.append(f"- Positive rate: {ref['positive_rate']:.1%}")
    lines.append(f"- Samples: {ref.get('total_samples', 0)}")
    lines.append("")

    # ─── Latency ───
    lines.append("## 7. Latency Analysis")
    lines.append("")
    lat_dist = generate_latency_distribution(results, str(charts_dir / "latency.png"))
    if lat_dist:
        lines.append("![Latency Distribution](charts/latency.png)")
        lines.append("")

    lines.append("| Statistic | Value |")
    lines.append("|-----------|-------|")
    lines.append(f"| Mean | {lat['mean_ms']/1000:.1f}s |")
    lines.append(f"| Median | {lat['median_ms']/1000:.1f}s |")
    lines.append(f"| P95 | {lat['p95_ms']/1000:.1f}s |")
    lines.append(f"| Min | {lat['min_ms']/1000:.1f}s |")
    lines.append(f"| Max | {lat['max_ms']/1000:.1f}s |")
    lines.append(f"| Total samples | {lat.get('total_samples', 0)} |")
    lines.append("")

    # ─── Ablation Study ───
    if ablation_results:
        lines.append("## 8. Ablation Study")
        lines.append("")
        lines.append("Each configuration isolates one V2 component to measure its contribution.")
        lines.append("")
        lines.append("| Configuration | Accuracy | Macro F1 | Mean Latency | Iterations |")
        lines.append("|---------------|----------|----------|-------------|------------|")

        for config_name, config_results in ablation_results.items():
            cm = compute_all_metrics(config_results)
            lines.append(f"| {config_name} | {cm['accuracy']['accuracy']:.1%} | {cm['classification']['macro']['f1']:.3f} | {cm['latency']['mean_ms']/1000:.1f}s | {cm['gate_efficiency']['avg_iterations']:.1f} |")
        lines.append("")

        abl_chart = generate_ablation_chart(ablation_results, str(charts_dir / "ablation.png"))
        if abl_chart:
            lines.append("![Ablation Study](charts/ablation.png)")
            lines.append("")

    # ─── Error Analysis ───
    mismatches = acc.get("mismatches", [])
    if mismatches:
        lines.append("## 9. Error Analysis")
        lines.append("")
        lines.append(f"Misclassified samples ({len(mismatches)} shown):")
        lines.append("")
        lines.append("| Input | Gold | Predicted |")
        lines.append("|-------|------|-----------|")
        for m in mismatches:
            lines.append(f"| {m['input'][:60]}... | {m['gold']} | {m['predicted']} |")
        lines.append("")

    # Write report
    report_path = output_path / f"report_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Report generated: %s", report_path)
    return str(report_path)
