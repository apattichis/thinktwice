"""Dataset type dispatch -- routes metrics, reports, and correctness checks
to the appropriate handler based on dataset name.

Each dataset type has its own metric computation, report generation, and
correctness function (for McNemar's test). Adding a new dataset type requires:
1. Adding a mapping entry to DATASET_TYPES
2. Implementing compute/report/correct functions in a metrics module
3. Registering them in the dispatch functions below
"""

import logging

logger = logging.getLogger(__name__)

# Maps dataset names to their evaluation type
DATASET_TYPES = {
    "factcheck50": "factcheck",
    "factcheck_bench": "factcheck",
    "halueval": "factcheck",
    "ifeval": "ifeval",
    "truthfulqa": "truthfulqa",
}


def get_dataset_type(name: str) -> str:
    """Get the evaluation type for a dataset name."""
    return DATASET_TYPES.get(name, "factcheck")


def get_metrics_for_dataset(name: str, results: list[dict]) -> dict:
    """Compute metrics appropriate for the dataset type."""
    dtype = get_dataset_type(name)

    if dtype == "ifeval":
        from eval.ifeval_metrics import compute_ifeval_metrics
        return compute_ifeval_metrics(results)
    elif dtype == "truthfulqa":
        from eval.truthfulqa_metrics import compute_truthfulqa_metrics
        return compute_truthfulqa_metrics(results)
    else:
        from eval.metrics import compute_all_metrics
        return compute_all_metrics(results)


def get_report_for_dataset(
    name: str,
    results: list[dict],
    output_dir: str = "results",
    comparison: dict | None = None,
    single_shot_metrics: dict | None = None,
    **kwargs,
) -> str:
    """Generate the report appropriate for the dataset type."""
    dtype = get_dataset_type(name)

    if dtype == "ifeval":
        from eval.ifeval_report import generate_ifeval_report
        return generate_ifeval_report(
            results, name, output_dir=output_dir,
            comparison=comparison, ss_metrics=single_shot_metrics,
        )
    elif dtype == "truthfulqa":
        from eval.truthfulqa_report import generate_truthfulqa_report
        return generate_truthfulqa_report(
            results, name, output_dir=output_dir,
            comparison=comparison, ss_metrics=single_shot_metrics,
        )
    else:
        from eval.report import generate_report
        return generate_report(
            results, name, output_dir=output_dir,
            comparison=comparison, single_shot_metrics=single_shot_metrics,
            **kwargs,
        )


def get_correct_fn(name: str):
    """Return the correctness function for McNemar's test.

    Each function takes a result dict and returns bool.
    """
    dtype = get_dataset_type(name)

    if dtype == "ifeval":
        def _is_correct_ifeval(result: dict) -> bool:
            """All instructions must pass strict verification."""
            judgements = result.get("ifeval_judgements", {})
            if not judgements:
                return False
            return judgements.get("prompt_strict", False)
        return _is_correct_ifeval

    elif dtype == "truthfulqa":
        def _is_correct_truthfulqa(result: dict) -> bool:
            """Judge must rate as both truthful and informative."""
            judge = result.get("truthfulqa_judge", {})
            if not judge:
                return False
            return judge.get("truthful", False) and judge.get("informative", False)
        return _is_correct_truthfulqa

    else:
        from eval.compare import _is_correct as _is_correct_factcheck
        return _is_correct_factcheck
