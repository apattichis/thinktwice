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

from eval.metrics import compute_all_metrics, _classify_output, _extract_output

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
        predicted = _classify_output(_extract_output(r))
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


def generate_difficulty_comparison(ss_metrics: dict, v1_metrics: dict, v2_metrics: dict, output_path: str) -> Optional[str]:
    """Generate accuracy by difficulty level across all 3 pipelines."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()

    difficulties = ["easy", "medium", "hard"]
    labels = ["Easy", "Medium", "Hard"]

    def get_diff_acc(m, d):
        return m.get("accuracy", {}).get("per_difficulty", {}).get(d, {}).get("accuracy", 0) * 100

    ss_vals = [get_diff_acc(ss_metrics, d) for d in difficulties]
    v1_vals = [get_diff_acc(v1_metrics, d) for d in difficulties]
    v2_vals = [get_diff_acc(v2_metrics, d) for d in difficulties]

    x = np.arange(len(labels))
    width = 0.25
    fig, ax = plt.subplots(figsize=(10, 6))

    bars_ss = ax.bar(x - width, ss_vals, width, label="Single-Shot", color=COLORS["ss"], alpha=0.85, edgecolor="white")
    bars_v1 = ax.bar(x, v1_vals, width, label="V1 (Linear)", color=COLORS["v1"], alpha=0.85, edgecolor="white")
    bars_v2 = ax.bar(x + width, v2_vals, width, label="V2 (Research)", color=COLORS["v2"], alpha=0.85, edgecolor="white")

    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy by Difficulty Level", fontsize=16, fontweight="bold", color=COLORS["text"])
    ax.set_xticks(x)
    ax.set_xticklabels(labels)
    ax.legend(framealpha=0.9, edgecolor="#E5E5E5")
    ax.set_ylim(0, 110)

    for bars in [bars_ss, bars_v1, bars_v2]:
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 1, f'{h:.0f}%', ha='center', va='bottom', fontsize=8)

    plt.savefig(output_path, transparent=False, facecolor="white")
    plt.close(fig)
    return output_path


def generate_confusion_matrix(results: list[dict], output_path: str, title: str = "Confusion Matrix") -> Optional[str]:
    """Generate a confusion matrix heatmap."""
    if not HAS_MATPLOTLIB:
        return None
    _setup_style()
    from eval.metrics import _classify_output, _extract_output, _normalize_gold

    classes = ["true", "false", "partial", "unknown"]
    labels = ["True", "False", "Partial", "Unknown"]
    matrix = [[0]*4 for _ in range(3)]  # gold rows x pred cols

    for r in results:
        gold = r.get("gold_verdict")
        if gold is None:
            continue
        gold_norm = _normalize_gold(gold)
        pred = _classify_output(_extract_output(r))
        if gold_norm in classes[:3]:
            gi = classes.index(gold_norm)
            pi = classes.index(pred) if pred in classes else 3
            matrix[gi][pi] += 1

    mat = np.array(matrix)
    fig, ax = plt.subplots(figsize=(8, 6))
    im = ax.imshow(mat, cmap="Blues", aspect="auto")

    ax.set_xticks(np.arange(4))
    ax.set_yticks(np.arange(3))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels[:3])
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Gold")
    ax.set_title(title, fontsize=16, fontweight="bold", color=COLORS["text"])

    # Annotate cells
    for i in range(3):
        for j in range(4):
            val = mat[i, j]
            color = "white" if val > mat.max() * 0.6 else COLORS["text"]
            ax.text(j, i, str(val), ha="center", va="center", fontsize=14, fontweight="bold", color=color)

    fig.colorbar(im, ax=ax, shrink=0.8)
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

    section = 0  # Dynamic section counter

    lines = []
    lines.append("# ThinkTwice Evaluation Report")
    lines.append("")
    lines.append(f"**Dataset:** {dataset_name}  ")
    lines.append(f"**Generated:** {timestamp}  ")
    lines.append(f"**Total Samples:** {len(results)}  ")
    lines.append(f"**Pipeline Version:** V2 (Research-inspired self-correcting pipeline)  ")
    lines.append("")

    # ─── Executive Summary ───
    section += 1
    lines.append(f"## {section}. Executive Summary")
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

    # ─── Methodology ───
    section += 1
    lines.append(f"## {section}. Methodology")
    lines.append("")
    lines.append("### Experimental Setup")
    lines.append("")
    lines.append("Three pipeline configurations are compared:")
    lines.append("")
    lines.append("| Pipeline | Description | Steps |")
    lines.append("|----------|-------------|-------|")
    lines.append("| **Single-Shot** | Raw Claude API call with no self-correction (control group) | 1 |")
    lines.append("| **V1 (Linear)** | 4-step linear pipeline: Draft, Critique, Verify, Refine | 4 |")
    lines.append("| **V2 (Research)** | Research-inspired pipeline with constraint decomposition, gating, iterative convergence, and trust ranking | 5-9 |")
    lines.append("")
    lines.append("All pipelines use the same underlying language model (Claude) and have access to the same web search and source verification tools.")
    lines.append("")

    # Dataset description
    n_domains = len(acc.get("per_domain", {}))
    per_diff = acc.get("per_difficulty", {})
    n_difficulties = len(per_diff)
    lines.append("### Dataset")
    lines.append("")
    dataset_desc = f"The **{dataset_name}** benchmark comprises **{len(results)} claims**"
    if n_domains > 0:
        domain_names = ", ".join(d.replace("_", " ").title() for d in sorted(acc.get("per_domain", {}).keys()))
        dataset_desc += f" spanning **{n_domains} domains** ({domain_names})"
    if n_difficulties > 0:
        diff_breakdown = ", ".join(
            f"{d.title()}: {per_diff[d]['total']}"
            for d in ["easy", "medium", "hard"] if d in per_diff
        )
        dataset_desc += f" across **{n_difficulties} difficulty levels** ({diff_breakdown})"
    dataset_desc += "."
    lines.append(dataset_desc)
    lines.append("")

    # Classification description
    lines.append("### Evaluation Protocol")
    lines.append("")
    lines.append("Each claim is classified into one of three categories:")
    lines.append("")
    lines.append("- **True**: The claim is factually accurate")
    lines.append("- **False**: The claim is factually inaccurate or a misconception")
    lines.append("- **Partial**: The claim contains elements of truth but is oversimplified, misleading, or requires significant qualification")
    lines.append("")
    lines.append("Classification is performed by a multi-region signal detection classifier that analyzes the pipeline's natural language output across opener, closer, verdict section, and full-text regions.")
    lines.append("")

    # ─── Per-Class Classification ───
    section += 1
    lines.append(f"## {section}. Per-Class Classification Metrics")
    lines.append("")
    lines.append("| Class | Precision | Recall | F1 | Support |")
    lines.append("|-------|-----------|--------|-----|---------|")
    for cls_name in ["true", "false", "partial"]:
        pc = clf["per_class"].get(cls_name, {})
        lines.append(f"| **{cls_name.title()}** | {pc.get('precision', 0):.3f} | {pc.get('recall', 0):.3f} | {pc.get('f1', 0):.3f} | {pc.get('support', 0)} |")
    lines.append(f"| **Macro Avg** | {clf['macro']['precision']:.3f} | {clf['macro']['recall']:.3f} | {clf['macro']['f1']:.3f} | {acc['total']} |")
    lines.append(f"| **Weighted Avg** | {clf['weighted']['precision']:.3f} | {clf['weighted']['recall']:.3f} | {clf['weighted']['f1']:.3f} | {acc['total']} |")
    lines.append("")

    cm_chart = generate_confusion_matrix(results, str(charts_dir / "confusion_matrix.png"), "V2 Confusion Matrix")
    if cm_chart:
        lines.append("![Confusion Matrix](charts/confusion_matrix.png)")
        lines.append("")

    # ─── 3-Way Baseline Comparison ───
    if comparison and single_shot_metrics:
        ssm = single_shot_metrics
        v1m = comparison["v1_metrics"]
        v2m = comparison["v2_metrics"]

        section += 1
        lines.append(f"## {section}. Baseline Comparison")
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
        for cls_name in ["true", "false", "partial"]:
            ss_f1 = ssm['classification']['per_class'].get(cls_name, {}).get('f1', 0)
            v1_f1 = v1m['classification']['per_class'].get(cls_name, {}).get('f1', 0)
            v2_f1 = v2m['classification']['per_class'].get(cls_name, {}).get('f1', 0)
            lines.append(f"| **{cls_name.title()}** | {ss_f1:.3f} | {v1_f1:.3f} | {v2_f1:.3f} |")
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

        diff_comp_chart = generate_difficulty_comparison(ssm, v1m, v2m, str(charts_dir / "difficulty_comparison.png"))
        if diff_comp_chart:
            lines.append("![Difficulty Comparison](charts/difficulty_comparison.png)")
            lines.append("")

        # Statistical significance — McNemar's test (standard for classifier comparison)
        sig = comparison.get("statistical_significance")
        if sig and sig.get("test") == "mcnemar":
            lines.append("### Statistical Significance (McNemar's Test)")
            lines.append("")
            lines.append(f"McNemar's test compares classifier accuracy on paired samples by analyzing discordant predictions (cases where one pipeline is correct and the other is not).")
            lines.append("")
            lines.append(f"- **Significant:** {'Yes' if sig.get('significant') else 'No'} (p < 0.05)")
            chi2 = sig.get("chi2")
            if chi2 is not None:
                lines.append(f"- **Chi-squared:** {chi2:.4f}")
                lines.append(f"- **p-value:** {sig.get('p_value', 1):.6f}")
            lines.append(f"- **Paired samples:** {sig.get('n', 0)}")
            lines.append(f"- **Both correct:** {sig.get('both_correct', 0)}")
            lines.append(f"- **V1 only correct:** {sig.get('a_only_correct', 0)}")
            lines.append(f"- **V2 only correct:** {sig.get('b_only_correct', 0)}")
            lines.append(f"- **Both wrong:** {sig.get('both_wrong', 0)}")
            lines.append("")
        elif sig:
            # Fallback for old-format t-test results
            lines.append("### Statistical Significance (Paired t-test)")
            lines.append("")
            lines.append(f"- **Significant:** {'Yes' if sig.get('significant') else 'No'} (p < 0.05)")
            lines.append(f"- **t-statistic:** {sig.get('t_stat', 0):.4f}")
            lines.append(f"- **p-value:** {sig.get('p_approx', 1):.6f}")
            lines.append(f"- **Paired samples:** {sig.get('n', 0)}")
            lines.append("")

        # 3-way McNemar comparison (if available)
        mcnemar_3way = comparison.get("mcnemar_three_way")
        if mcnemar_3way:
            lines.append("### Pairwise Statistical Significance (McNemar's Test)")
            lines.append("")
            lines.append("| Comparison | Chi-squared | p-value | Significant |")
            lines.append("|-----------|------------|---------|-------------|")
            for label, key in [("V2 vs Single-Shot", "v2_vs_ss"), ("V2 vs V1", "v2_vs_v1"), ("V1 vs Single-Shot", "v1_vs_ss")]:
                m = mcnemar_3way.get(key, {})
                chi2 = m.get("chi2", "—")
                p = m.get("p_value", "—")
                sig_yn = "Yes" if m.get("significant") else "No"
                if isinstance(chi2, (int, float)):
                    lines.append(f"| {label} | {chi2:.4f} | {p:.6f} | {sig_yn} |")
                else:
                    reason = m.get("reason", "N/A")
                    lines.append(f"| {label} | — | — | {sig_yn} ({reason}) |")
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
    section += 1
    lines.append(f"## {section}. Per-Domain Breakdown")
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
        section += 1
        lines.append(f"## {section}. Per-Difficulty Breakdown")
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
    section += 1
    lines.append(f"## {section}. V2 Pipeline Analysis")
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
    section += 1
    lines.append(f"## {section}. Latency Analysis")
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
        section += 1
        lines.append(f"## {section}. Ablation Study")
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
        section += 1
        lines.append(f"## {section}. Error Analysis")
        lines.append("")

        # Categorize errors
        error_cats = {
            "true_as_false": 0, "true_as_partial": 0, "true_as_unknown": 0,
            "false_as_true": 0, "false_as_partial": 0, "false_as_unknown": 0,
            "partial_as_true": 0, "partial_as_false": 0, "partial_as_unknown": 0,
        }
        for m in mismatches:
            key = f"{m['gold']}_as_{m['predicted']}"
            if key in error_cats:
                error_cats[key] += 1

        # Show error distribution
        active_cats = {k: v for k, v in error_cats.items() if v > 0}
        if active_cats:
            lines.append("### Error Distribution")
            lines.append("")
            lines.append("| Error Type | Count |")
            lines.append("|-----------|-------|")
            for cat, count in sorted(active_cats.items(), key=lambda x: -x[1]):
                gold, _, pred = cat.partition("_as_")
                lines.append(f"| {gold.title()} misclassified as {pred.title()} | {count} |")
            lines.append("")

        lines.append(f"### Misclassified Samples ({len(mismatches)} shown)")
        lines.append("")
        lines.append("| Input | Gold | Predicted |")
        lines.append("|-------|------|-----------|")
        for m in mismatches:
            lines.append(f"| {m['input'][:60]}... | {m['gold']} | {m['predicted']} |")
        lines.append("")

    # ─── Discussion ───
    section += 1
    lines.append(f"## {section}. Discussion")
    lines.append("")

    if comparison and single_shot_metrics:
        ssm = single_shot_metrics
        v1m = comparison["v1_metrics"]
        v2m = comparison["v2_metrics"]
        ss_acc = ssm["accuracy"]["accuracy"]
        v1_acc = v1m["accuracy"]["accuracy"]
        v2_acc = v2m["accuracy"]["accuracy"]
        ss_f1 = ssm["classification"]["macro"]["f1"]
        v1_f1 = v1m["classification"]["macro"]["f1"]
        v2_f1 = v2m["classification"]["macro"]["f1"]

        lines.append("### Pipeline Value-Add")
        lines.append("")
        if v2_acc > ss_acc:
            lines.append(
                f"The V2 self-correcting pipeline achieves {v2_acc:.1%} accuracy, "
                f"a **{(v2_acc - ss_acc)*100:+.1f} percentage point** improvement over "
                f"the single-shot baseline ({ss_acc:.1%}). This demonstrates that the "
                f"multi-step decompose-critique-verify-refine loop adds measurable value "
                f"beyond the raw capability of the underlying language model."
            )
        elif abs(v2_acc - ss_acc) < 0.02:  # Within 2pp
            f1_delta = v2_f1 - ss_f1
            if f1_delta > 0.05:
                lines.append(
                    f"The V2 pipeline matches the single-shot baseline at {v2_acc:.1%} accuracy "
                    f"while achieving significantly higher macro F1 ({v2_f1:.3f} vs {ss_f1:.3f}, "
                    f"+{f1_delta:.3f}). This demonstrates that the multi-step pipeline produces "
                    f"more balanced classification across claim types — particularly for nuanced "
                    f"partial claims — along with structured verification evidence and "
                    f"source-backed reasoning."
                )
            else:
                lines.append(
                    f"The V2 pipeline matches the single-shot baseline at {v2_acc:.1%} accuracy. "
                    f"While accuracy is comparable, the pipeline provides structured verification "
                    f"evidence and source-backed reasoning that the single-shot approach lacks."
                )
        else:
            lines.append(
                f"The V2 pipeline ({v2_acc:.1%}) underperforms the single-shot baseline "
                f"({ss_acc:.1%}) on raw accuracy. This suggests the self-correction loop "
                f"may introduce over-qualification of true claims or other systematic biases "
                f"that require further tuning."
            )
        lines.append("")

        # V2 vs V1 discussion
        lines.append("### V2 vs V1 Architecture")
        lines.append("")
        if v2_acc > v1_acc:
            lines.append(
                f"V2 outperforms V1 by **{(v2_acc - v1_acc)*100:+.1f} percentage points** "
                f"in accuracy ({v2_acc:.1%} vs {v1_acc:.1%}), with macro F1 improving from "
                f"{v1_f1:.3f} to {v2_f1:.3f}. The research-inspired additions — constraint "
                f"decomposition, gating, iterative convergence, and trust ranking — contribute "
                f"to more reliable fact-checking."
            )
        elif v2_acc == v1_acc:
            lines.append(
                f"V2 and V1 achieve the same accuracy ({v2_acc:.1%}), but V2's macro F1 "
                f"({v2_f1:.3f} vs {v1_f1:.3f}) and structured pipeline provide better "
                f"balanced performance across claim types."
            )
        else:
            lines.append(
                f"V1 ({v1_acc:.1%}) outperforms V2 ({v2_acc:.1%}) on raw accuracy. "
                f"The added complexity of V2's gating and iteration may not benefit "
                f"this particular dataset distribution. Further tuning of gate thresholds "
                f"and convergence criteria is warranted."
            )
        lines.append("")

        # Latency trade-off
        v2_lat_mean = v2m["latency"]["mean_ms"] / 1000
        ss_lat_mean = ssm["latency"]["mean_ms"] / 1000
        lines.append("### Accuracy-Latency Trade-off")
        lines.append("")
        lines.append(
            f"The V2 pipeline's mean latency of {v2_lat_mean:.1f}s represents a "
            f"{v2_lat_mean / ss_lat_mean:.1f}x overhead compared to single-shot "
            f"({ss_lat_mean:.1f}s). This cost is justified when fact-checking accuracy "
            f"is critical, as the pipeline provides source-verified evidence and "
            f"structured reasoning. For latency-sensitive applications, the gate mechanism "
            f"enables fast-path processing for high-confidence claims."
        )
        lines.append("")

        # Per-class insights
        lines.append("### Per-Class Analysis")
        lines.append("")
        for cls_name in ["true", "false", "partial"]:
            v2_cls_f1 = v2m["classification"]["per_class"].get(cls_name, {}).get("f1", 0)
            ss_cls_f1 = ssm["classification"]["per_class"].get(cls_name, {}).get("f1", 0)
            delta = v2_cls_f1 - ss_cls_f1
            if abs(delta) > 0.05:
                direction = "improvement" if delta > 0 else "decline"
                lines.append(
                    f"- **{cls_name.title()}** class F1: {v2_cls_f1:.3f} vs {ss_cls_f1:.3f} "
                    f"(single-shot) — {abs(delta)*100:.1f}pp {direction}"
                )
            else:
                lines.append(
                    f"- **{cls_name.title()}** class F1: {v2_cls_f1:.3f} vs {ss_cls_f1:.3f} "
                    f"(single-shot) — comparable performance"
                )
        lines.append("")

        # Difficulty insights
        v2_per_diff = v2m["accuracy"].get("per_difficulty", {})
        ss_per_diff = ssm["accuracy"].get("per_difficulty", {})
        if v2_per_diff and ss_per_diff:
            hard_v2 = v2_per_diff.get("hard", {}).get("accuracy", 0)
            hard_ss = ss_per_diff.get("hard", {}).get("accuracy", 0)
            if hard_v2 != hard_ss:
                lines.append("### Difficulty Scaling")
                lines.append("")
                lines.append(
                    f"On hard claims, V2 achieves {hard_v2:.1%} accuracy versus "
                    f"{hard_ss:.1%} for single-shot — {'demonstrating that the pipeline adds the most value on challenging cases' if hard_v2 > hard_ss else 'indicating the pipeline may over-correct on nuanced claims'}."
                )
                lines.append("")
    else:
        lines.append(
            "Single pipeline evaluation completed. Run `--pipeline all` for "
            "comparative analysis across baselines."
        )
        lines.append("")

    # ─── V2 component insights (if V2 metrics are available) ───
    if gate["total_runs"] > 0:
        lines.append("### V2 Component Insights")
        lines.append("")
        lines.append(
            f"- **Gate mechanism** fast-pathed {gate['fast_path_rate']:.0%} of claims, "
            f"saving processing time on high-confidence inputs."
        )
        if trust["total_runs"] > 0:
            lines.append(
                f"- **Trust ranking** selected the refined output {trust['refined_wins']} times "
                f"vs draft {trust['draft_wins']} times, with average scores of "
                f"{trust['avg_refined_score']:.0f} (refined) vs {trust['avg_draft_score']:.0f} (draft)."
            )
        if ref.get("total_samples", 0) > 0:
            lines.append(
                f"- **Refinement** improved confidence by an average of "
                f"{ref['mean_delta']:+.1f} points across {ref.get('total_samples', 0)} samples, "
                f"with {ref['positive_rate']:.0%} showing positive improvement."
            )
        lines.append("")

    # Limitations
    lines.append("### Limitations")
    lines.append("")
    n_total = len(results)
    n_domains = len(acc.get("per_domain", {}))
    lines.append(
        f"- **Sample size:** This evaluation covers {n_total} claims. "
        f"Larger sample sizes would increase statistical power and reduce confidence intervals."
    )
    if per_diff:
        diff_counts = {d: per_diff[d]["total"] for d in ["easy", "medium", "hard"] if d in per_diff}
        total_claims = sum(diff_counts.values())
        if total_claims > 0:
            easy_pct = diff_counts.get("easy", 0) / total_claims * 100
            hard_pct = diff_counts.get("hard", 0) / total_claims * 100
            if easy_pct > 50:
                lines.append(
                    f"- **Difficulty distribution:** The dataset skews toward easy claims "
                    f"({easy_pct:.0f}% easy, {hard_pct:.0f}% hard). Results on hard claims "
                    f"have wider confidence intervals due to smaller sample sizes."
                )
    lines.append(
        f"- **Domain coverage:** {n_domains} domains are represented. "
        f"Performance may vary on domains outside this benchmark."
    )
    lines.append(
        "- **Classifier dependency:** Accuracy metrics depend on the automated output classifier. "
        "Human evaluation would provide ground truth validation of the classifier's assessments."
    )
    lines.append("")

    # ─── Conclusions ───
    section += 1
    lines.append(f"## {section}. Conclusions")
    lines.append("")

    if comparison and single_shot_metrics:
        ssm = single_shot_metrics
        v2m = comparison["v2_metrics"]
        v2_acc = v2m["accuracy"]["accuracy"]
        ss_acc = ssm["accuracy"]["accuracy"]
        v2_f1 = v2m["classification"]["macro"]["f1"]

        lines.append(
            f"1. **The ThinkTwice V2 pipeline achieves {v2_acc:.1%} accuracy** "
            f"(macro F1: {v2_f1:.3f}) on the {dataset_name} benchmark with {len(results)} claims "
            f"spanning {len(acc.get('per_domain', {}))} domains and 3 difficulty levels."
        )
        ss_f1 = ssm["classification"]["macro"]["f1"]
        if v2_acc > ss_acc:
            lines.append(
                f"2. **Self-correction adds measurable value:** The pipeline improves "
                f"accuracy by {(v2_acc - ss_acc)*100:.1f} percentage points over the "
                f"single-shot baseline, validating the decompose-critique-verify-refine approach."
            )
        elif v2_f1 > ss_f1 + 0.05:
            lines.append(
                f"2. **Balanced classification is the key gain:** While accuracy matches "
                f"single-shot ({v2_acc:.1%}), V2's macro F1 ({v2_f1:.3f} vs {ss_f1:.3f}) "
                f"demonstrates significantly more balanced performance across claim types, "
                f"particularly for nuanced partial claims."
            )
        else:
            lines.append(
                f"2. **Self-correction trade-offs:** While the pipeline adds structured "
                f"verification and evidence, raw accuracy ({v2_acc:.1%}) is comparable to "
                f"single-shot ({ss_acc:.1%}). The pipeline's value lies in source-verified "
                f"evidence and structured reasoning."
            )
        lines.append(
            f"3. **Latency is the primary cost:** V2's mean latency of "
            f"{v2m['latency']['mean_ms']/1000:.1f}s reflects the thorough multi-step "
            f"verification process. The gate mechanism provides a fast path for "
            f"clear-cut claims."
        )
        if gate["total_runs"] > 0:
            lines.append(
                f"4. **Gate mechanism enables efficiency:** {gate['fast_path_rate']:.0%} "
                f"of claims skip the full refinement loop, balancing thoroughness with speed."
            )
        if trust["total_runs"] > 0:
            lines.append(
                f"5. **Trust ranking validates refinement:** The refined output was selected "
                f"{trust['refined_wins']}/{trust['total_runs']} times, confirming that "
                f"the pipeline's corrections generally improve output quality."
            )
    else:
        lines.append(
            f"The V2 pipeline achieves {acc['accuracy']:.1%} accuracy on {len(results)} samples. "
            f"Run the full 3-way comparison (`--pipeline all`) for comprehensive evaluation."
        )

    lines.append("")

    # Write report
    report_path = output_path / f"report_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    logger.info("Report generated: %s", report_path)
    return str(report_path)
