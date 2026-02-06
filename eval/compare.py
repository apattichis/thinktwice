"""Side-by-side comparison of pipeline results.

Computes per-sample differences, statistical significance (McNemar's test),
and generates comparison examples.
"""

import json
import logging
import math
from pathlib import Path
from typing import Optional

from eval.metrics import compute_all_metrics, _classify_output, _extract_output, _normalize_gold

logger = logging.getLogger(__name__)


def load_results(path: str) -> list[dict]:
    """Load results from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return data.get("results", data) if isinstance(data, dict) else data


def compare_pipelines(
    ss_results: list[dict],
    tt_results: list[dict],
) -> dict:
    """Compare single-shot and ThinkTwice results side-by-side.

    Returns comparison metrics and example diffs.
    """
    ss_metrics = compute_all_metrics(ss_results)
    tt_metrics = compute_all_metrics(tt_results)

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
            "ss_confidence": m_ss.get("confidence_after", 0),
            "tt_confidence": m_tt.get("confidence_after", 0),
            "ss_duration_ms": r_ss.get("duration_ms", 0),
            "tt_duration_ms": r_tt.get("duration_ms", 0),
            "tt_iterations": m_tt.get("iterations_used", 0),
            "tt_gate_decision": m_tt.get("gate_decision", ""),
            "tt_trust_winner": m_tt.get("trust_winner", ""),
        }
        diff["confidence_delta"] = diff["tt_confidence"] - diff["ss_confidence"]
        diff["duration_delta_ms"] = diff["tt_duration_ms"] - diff["ss_duration_ms"]
        paired_diffs.append(diff)

    # Statistical significance -- McNemar's test on correctness
    mcnemar_result = _mcnemar_test(ss_results, tt_results) if common_inputs else None

    # Supplementary: paired t-test on confidence deltas
    confidence_deltas = [d["confidence_delta"] for d in paired_diffs]
    ttest_result = _paired_t_test(confidence_deltas) if confidence_deltas else None

    # Find best/worst/interesting examples
    sorted_by_improvement = sorted(paired_diffs, key=lambda d: d["confidence_delta"], reverse=True)
    examples = {
        "best_improvement": sorted_by_improvement[:3] if sorted_by_improvement else [],
        "worst_regression": sorted_by_improvement[-3:] if sorted_by_improvement else [],
        "fast_path_examples": [d for d in paired_diffs if d["tt_gate_decision"] == "skip"][:3],
        "draft_wins": [d for d in paired_diffs if d["tt_trust_winner"] == "draft"][:3],
    }

    return {
        "single_shot_metrics": ss_metrics,
        "thinktwice_metrics": tt_metrics,
        "paired_comparison": {
            "total_paired": len(paired_diffs),
            "mean_confidence_delta": sum(confidence_deltas) / len(confidence_deltas) if confidence_deltas else 0,
            "mean_duration_delta_ms": sum(d["duration_delta_ms"] for d in paired_diffs) / len(paired_diffs) if paired_diffs else 0,
            "tt_improved_count": sum(1 for d in confidence_deltas if d > 0),
            "tt_same_count": sum(1 for d in confidence_deltas if d == 0),
            "tt_regressed_count": sum(1 for d in confidence_deltas if d < 0),
        },
        "statistical_significance": mcnemar_result,
        "confidence_ttest": ttest_result,
        "examples": examples,
    }


def _is_correct(result: dict) -> bool:
    """Check if a result's prediction matches the gold verdict."""
    gold = result.get("gold_verdict")
    if gold is None:
        return False
    gold_norm = _normalize_gold(gold)
    predicted = _classify_output(_extract_output(result))
    if gold_norm == "true" and predicted == "true":
        return True
    if gold_norm == "false" and predicted == "false":
        return True
    if gold_norm == "partial" and predicted in ("partial", "true"):
        return True
    return False


def _mcnemar_test(a_results: list[dict], b_results: list[dict]) -> dict:
    """McNemar's test for paired classifier comparison.

    Standard test for comparing two classifiers on the same dataset.
    Tests whether the disagreements between classifiers are symmetric.

    Contingency table:
        |             | B correct | B wrong |
        | A correct   |     a     |    b    |
        | A wrong     |     c     |    d    |

    Only b and c (discordant pairs) matter.
    H0: b = c (classifiers make the same number of errors on different samples)
    """
    a_by_input = {r["input"]: r for r in a_results}
    b_by_input = {r["input"]: r for r in b_results}
    common = set(a_by_input.keys()) & set(b_by_input.keys())

    # Count contingency table cells
    both_correct = 0    # a
    a_only = 0          # b: A correct, B wrong
    b_only = 0          # c: A wrong, B correct
    both_wrong = 0      # d

    for inp in common:
        ra = a_by_input[inp]
        rb = b_by_input[inp]
        if ra.get("gold_verdict") is None:
            continue

        a_ok = _is_correct(ra)
        b_ok = _is_correct(rb)

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

    # McNemar's chi-squared (with continuity correction for small samples)
    chi2 = (abs(a_only - b_only) - 1) ** 2 / (a_only + b_only)
    # Chi-squared CDF approximation (1 df)
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


def mcnemar_test(
    ss_results: list[dict],
    tt_results: list[dict],
) -> dict:
    """Run McNemar's test: Single-Shot vs ThinkTwice."""
    return {
        "tt_vs_ss": _mcnemar_test(ss_results, tt_results),
    }


def _chi2_cdf_1df(x: float) -> float:
    """CDF of chi-squared distribution with 1 degree of freedom."""
    if x <= 0:
        return 0.0
    # Chi2(1df) CDF = 2 * Phi(sqrt(x)) - 1 = erf(sqrt(x/2))
    return math.erf(math.sqrt(x / 2))


def _paired_t_test(deltas: list[float]) -> dict:
    """Compute paired t-test for confidence deltas."""
    n = len(deltas)
    if n < 2:
        return {"significant": False, "reason": "Not enough samples"}

    mean = sum(deltas) / n
    variance = sum((d - mean) ** 2 for d in deltas) / (n - 1)
    std_err = math.sqrt(variance / n) if variance > 0 else 0

    if std_err == 0:
        return {"significant": False, "t_stat": 0, "p_approx": 1.0, "mean_delta": mean}

    t_stat = mean / std_err
    # Approximate p-value using normal distribution for large n
    p_approx = 2 * (1 - _normal_cdf(abs(t_stat)))

    return {
        "significant": p_approx < 0.05,
        "t_stat": round(t_stat, 4),
        "p_approx": round(p_approx, 6),
        "mean_delta": round(mean, 2),
        "std_err": round(std_err, 4),
        "n": n,
    }


def _normal_cdf(x: float) -> float:
    """Approximate standard normal CDF."""
    return 0.5 * (1 + math.erf(x / math.sqrt(2)))
