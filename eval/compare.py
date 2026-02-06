"""Side-by-side comparison of pipeline results.

Computes per-sample differences, statistical significance (McNemar's test),
and generates comparison examples.
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def load_results(path: str) -> list[dict]:
    """Load results from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return data.get("results", data) if isinstance(data, dict) else data


def compare_pipelines(
    ss_results: list[dict],
    tt_results: list[dict],
    dataset_name: str = "ifeval",
) -> dict:
    """Compare single-shot and ThinkTwice results side-by-side.

    Returns comparison metrics and example diffs.
    """
    from eval.dataset_types import get_metrics_for_dataset, get_correct_fn
    ss_metrics = get_metrics_for_dataset(dataset_name, ss_results)
    tt_metrics = get_metrics_for_dataset(dataset_name, tt_results)
    correct_fn = get_correct_fn(dataset_name)

    # Per-sample comparison (match by input)
    ss_by_input = {r["input"]: r for r in ss_results}
    tt_by_input = {r["input"]: r for r in tt_results}
    common_inputs = set(ss_by_input.keys()) & set(tt_by_input.keys())

    paired_diffs = []
    for inp in common_inputs:
        r_ss = ss_by_input[inp]
        r_tt = tt_by_input[inp]

        m_ss = r_ss.get("metrics", {})
        m_tt = r_tt.get("metrics", {})

        diff = {
            "input": inp[:100],
            "ss_duration_ms": r_ss.get("duration_ms", 0),
            "tt_duration_ms": r_tt.get("duration_ms", 0),
            "tt_iterations": m_tt.get("iterations_used", 0),
            "tt_gate_decision": m_tt.get("gate_decision", ""),
            "ss_correct": correct_fn(r_ss),
            "tt_correct": correct_fn(r_tt),
        }
        diff["duration_delta_ms"] = diff["tt_duration_ms"] - diff["ss_duration_ms"]
        paired_diffs.append(diff)

    # Statistical significance -- McNemar's test on correctness
    mcnemar_result = _mcnemar_test(ss_results, tt_results, correct_fn=correct_fn) if common_inputs else None

    # Duration deltas
    duration_deltas = [d["duration_delta_ms"] for d in paired_diffs]

    # Find interesting examples
    fixed = [d for d in paired_diffs if not d["ss_correct"] and d["tt_correct"]]
    broken = [d for d in paired_diffs if d["ss_correct"] and not d["tt_correct"]]

    return {
        "single_shot_metrics": ss_metrics,
        "thinktwice_metrics": tt_metrics,
        "paired_comparison": {
            "total_paired": len(paired_diffs),
            "mean_duration_delta_ms": sum(duration_deltas) / len(duration_deltas) if duration_deltas else 0,
            "tt_fixed": len(fixed),
            "tt_broke": len(broken),
            "both_correct": sum(1 for d in paired_diffs if d["ss_correct"] and d["tt_correct"]),
            "both_wrong": sum(1 for d in paired_diffs if not d["ss_correct"] and not d["tt_correct"]),
        },
        "statistical_significance": mcnemar_result,
        "examples": {
            "fixed_by_tt": fixed[:5],
            "broken_by_tt": broken[:5],
        },
    }


def _mcnemar_test(a_results: list[dict], b_results: list[dict], correct_fn=None) -> dict:
    """McNemar's test for paired classifier comparison."""
    if correct_fn is None:
        raise ValueError("correct_fn is required")

    a_by_input = {r["input"]: r for r in a_results}
    b_by_input = {r["input"]: r for r in b_results}
    common = set(a_by_input.keys()) & set(b_by_input.keys())

    both_correct = 0
    a_only = 0
    b_only = 0
    both_wrong = 0

    for inp in common:
        ra = a_by_input[inp]
        rb = b_by_input[inp]

        a_ok = correct_fn(ra)
        b_ok = correct_fn(rb)

        if a_ok and b_ok:
            both_correct += 1
        elif a_ok and not b_ok:
            a_only += 1
        elif not a_ok and b_ok:
            b_only += 1
        else:
            both_wrong += 1

    n_discordant = a_only + b_only
    n_total = both_correct + a_only + b_only + both_wrong

    if n_discordant == 0:
        return {
            "test": "mcnemar",
            "significant": False,
            "reason": "No discordant pairs",
            "n": n_total,
            "both_correct": both_correct,
            "a_only_correct": a_only,
            "b_only_correct": b_only,
            "both_wrong": both_wrong,
        }

    chi2 = (abs(a_only - b_only) - 1) ** 2 / (a_only + b_only)
    p_value = 1 - _chi2_cdf_1df(chi2)

    return {
        "test": "mcnemar",
        "significant": p_value < 0.05,
        "chi2": round(chi2, 4),
        "p_value": round(p_value, 6),
        "n": n_total,
        "both_correct": both_correct,
        "a_only_correct": a_only,
        "b_only_correct": b_only,
        "both_wrong": both_wrong,
    }


def _chi2_cdf_1df(x: float) -> float:
    """CDF of chi-squared distribution with 1 degree of freedom."""
    if x <= 0:
        return 0.0
    return math.erf(math.sqrt(x / 2))


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
