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
    "ifeval": "ifeval",
}


def get_dataset_type(name: str) -> str:
    """Get the evaluation type for a dataset name."""
    dtype = DATASET_TYPES.get(name)
    if dtype is None:
        raise ValueError(f"Unknown dataset type: {name}. Choose from: {list(DATASET_TYPES.keys())}")
    return dtype


def get_metrics_for_dataset(name: str, results: list[dict]) -> dict:
    """Compute metrics appropriate for the dataset type."""
    dtype = get_dataset_type(name)

    if dtype == "ifeval":
        from eval.ifeval_metrics import compute_ifeval_metrics
        return compute_ifeval_metrics(results)


def get_report_for_dataset(
    name: str,
    results: list[dict],
    output_dir: str = "results",
    comparison: dict | None = None,
    single_shot_metrics: dict | None = None,
) -> str:
    """Generate the report appropriate for the dataset type."""
    dtype = get_dataset_type(name)

    if dtype == "ifeval":
        from eval.ifeval_report import generate_ifeval_report
        return generate_ifeval_report(
            results, name, output_dir=output_dir,
            comparison=comparison, ss_metrics=single_shot_metrics,
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
