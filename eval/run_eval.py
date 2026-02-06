"""CLI entry point for the ThinkTwice evaluation framework.

Usage:
    python eval/run_eval.py --dataset ifeval --pipeline thinktwice --output results/
    python eval/run_eval.py --dataset ifeval --pipeline all --output results/ --samples 120
    python eval/run_eval.py --dataset truthfulqa --pipeline all --output results/ --samples 100
    python eval/run_eval.py --report --input results/ --output results/
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Add project root and backend to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from eval.runner import EvalRunner
from eval.dataset_types import get_dataset_type, get_metrics_for_dataset, get_report_for_dataset
from eval.compare import compare_pipelines


def setup_logging(verbose: bool = False):
    """Configure logging for the evaluation runner."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )


def get_dataset(name: str, max_samples: int | None = None) -> list[dict]:
    """Load a dataset by name."""
    if name == "truthfulqa":
        from eval.datasets.truthfulqa import get_dataset
        return get_dataset(max_samples=max_samples)
    elif name == "ifeval":
        from eval.datasets.ifeval import get_dataset
        return get_dataset(max_samples=max_samples)
    else:
        raise ValueError(f"Unknown dataset: {name}. Choose from: truthfulqa, ifeval")


async def run_pipeline(dataset: list[dict], dataset_name: str, version: str, output_dir: str, max_samples: int | None = None, resume_from: str | None = None):
    """Run a single pipeline version on a dataset."""
    runner = EvalRunner(pipeline_version=version, output_dir=output_dir)
    await runner.initialize()
    results = await runner.run_dataset(dataset, f"{dataset_name}", max_samples=max_samples, resume_from=resume_from)
    return results


async def _post_process(results: list[dict], dataset_name: str) -> list[dict]:
    """Run dataset-specific post-processing (e.g., LLM judge for TruthfulQA)."""
    dtype = get_dataset_type(dataset_name)

    if dtype == "truthfulqa":
        from eval.truthfulqa_metrics import judge_batch
        results = await judge_batch(results)
    elif dtype == "ifeval":
        from eval.ifeval_metrics import judge_all
        results = judge_all(results)

    return results


def _resave_results(results: list[dict], output_dir: str, dataset_name: str):
    """Re-save results after post-processing to persist judgement data."""
    out_path = Path(output_dir)
    result_files = sorted(out_path.glob(f"{dataset_name}_*.json"), key=lambda f: f.stat().st_mtime, reverse=True)
    if not result_files:
        return
    latest = result_files[0]
    with open(latest) as f:
        data = json.load(f)
    data["results"] = results
    with open(latest, "w") as f:
        json.dump(data, f, indent=2)
    logging.getLogger(__name__).info("Re-saved results with judgements to %s", latest)


async def run_all(dataset: list[dict], dataset_name: str, output_dir: str, max_samples: int | None = None):
    """Run single-shot baseline and ThinkTwice on the same dataset and compare."""
    print(f"\n{'='*60}")
    print(f"  Running SINGLE-SHOT baseline on {dataset_name}...")
    print(f"{'='*60}\n")
    ss_results = await run_pipeline(dataset, dataset_name, "single_shot", f"{output_dir}/single_shot", max_samples)
    ss_results = await _post_process(ss_results, dataset_name)
    _resave_results(ss_results, f"{output_dir}/single_shot", dataset_name)

    print(f"\n{'='*60}")
    print(f"  Running THINKTWICE pipeline on {dataset_name}...")
    print(f"{'='*60}\n")
    tt_results = await run_pipeline(dataset, dataset_name, "thinktwice", f"{output_dir}/thinktwice", max_samples)
    tt_results = await _post_process(tt_results, dataset_name)
    _resave_results(tt_results, f"{output_dir}/thinktwice", dataset_name)

    # Compare pipelines
    comparison = compare_pipelines(ss_results, tt_results, dataset_name=dataset_name)

    # Compute single-shot metrics
    ss_metrics = get_metrics_for_dataset(dataset_name, ss_results)

    # Generate report
    report_path = get_report_for_dataset(
        dataset_name, tt_results,
        output_dir=output_dir,
        comparison=comparison,
        single_shot_metrics=ss_metrics,
    )

    _print_summary(dataset_name, ss_metrics, comparison, report_path)
    return ss_results, tt_results, comparison


def _print_summary(dataset_name: str, ss_metrics: dict, comparison: dict, report_path: str):
    """Print results summary adapted to the dataset type."""
    dtype = get_dataset_type(dataset_name)
    ttm = comparison['thinktwice_metrics']

    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")

    if dtype == "ifeval":
        ssm = ss_metrics
        print(f"\n  {'Metric':<30} {'Single-Shot':>12} {'ThinkTwice':>12}")
        print(f"  {'-'*54}")
        print(f"  {'Prompt Strict Acc':<30} {ssm.get('prompt_strict_accuracy', 0):>11.1%} {ttm.get('prompt_strict_accuracy', 0):>11.1%}")
        print(f"  {'Instr Strict Acc':<30} {ssm.get('instruction_strict_accuracy', 0):>11.1%} {ttm.get('instruction_strict_accuracy', 0):>11.1%}")
        print(f"  {'Prompt Loose Acc':<30} {ssm.get('prompt_loose_accuracy', 0):>11.1%} {ttm.get('prompt_loose_accuracy', 0):>11.1%}")
        print(f"  {'Instr Loose Acc':<30} {ssm.get('instruction_loose_accuracy', 0):>11.1%} {ttm.get('instruction_loose_accuracy', 0):>11.1%}")
        ss_lat = ssm.get('latency', {})
        tt_lat = ttm.get('latency', {})
        print(f"  {'Mean Latency':<30} {ss_lat.get('mean_ms', 0)/1000:>10.1f}s {tt_lat.get('mean_ms', 0)/1000:>10.1f}s")

    elif dtype == "truthfulqa":
        ssm = ss_metrics
        print(f"\n  {'Metric':<30} {'Single-Shot':>12} {'ThinkTwice':>12}")
        print(f"  {'-'*54}")
        print(f"  {'Truthful + Informative':<30} {ssm.get('truthful_informative_rate', 0):>11.1%} {ttm.get('truthful_informative_rate', 0):>11.1%}")
        print(f"  {'Truthful Rate':<30} {ssm.get('truthful_rate', 0):>11.1%} {ttm.get('truthful_rate', 0):>11.1%}")
        print(f"  {'Informative Rate':<30} {ssm.get('informative_rate', 0):>11.1%} {ttm.get('informative_rate', 0):>11.1%}")
        ss_lat = ssm.get('latency', {})
        tt_lat = ttm.get('latency', {})
        print(f"  {'Mean Latency':<30} {ss_lat.get('mean_ms', 0)/1000:>10.1f}s {tt_lat.get('mean_ms', 0)/1000:>10.1f}s")

    sig = comparison.get('statistical_significance', {})
    if sig:
        print(f"\n  Statistical Significance (ThinkTwice vs Single-Shot):")
        if sig.get("test") == "mcnemar":
            chi2 = sig.get("chi2", "N/A")
            p = sig.get("p_value", 1)
            print(f"    chi2={chi2}, p={p:.6f} {'(significant)' if sig.get('significant') else '(not significant)'}")

    print(f"\n  Report: {report_path}")


async def generate_report_from_files(input_dir: str, output_dir: str):
    """Generate a report from existing result files."""
    input_path = Path(input_dir)
    result_files = list(input_path.glob("*.json"))

    if not result_files:
        print(f"No result files found in {input_dir}")
        return

    result_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    latest = result_files[0]
    print(f"Loading results from: {latest}")

    with open(latest) as f:
        data = json.load(f)

    results = data.get("results", [])
    dataset_name = data.get("dataset", "unknown")

    report_path = get_report_for_dataset(dataset_name, results, output_dir=output_dir)
    print(f"Report generated: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="ThinkTwice Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python eval/run_eval.py --dataset ifeval --pipeline all --samples 120
  python eval/run_eval.py --dataset truthfulqa --pipeline all --samples 100
  python eval/run_eval.py --dataset ifeval --pipeline thinktwice --samples 5
  python eval/run_eval.py --report --input results/
        """,
    )

    parser.add_argument("--dataset", choices=["truthfulqa", "ifeval"],
                        help="Dataset to evaluate on")
    parser.add_argument("--pipeline", choices=["thinktwice", "single_shot", "all"], default="thinktwice",
                        help="Pipeline version: thinktwice, single_shot, or all (runs both)")
    parser.add_argument("--output", default="results", help="Output directory (default: results)")
    parser.add_argument("--samples", type=int, default=None, help="Max samples to process")
    parser.add_argument("--report", action="store_true", help="Generate report from existing results")
    parser.add_argument("--input", default="results", help="Input directory for report generation")
    parser.add_argument("--resume", default=None, help="Path to checkpoint file to resume from")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args = parser.parse_args()
    setup_logging(args.verbose)

    if args.report:
        asyncio.run(generate_report_from_files(args.input, args.output))
        return

    if not args.dataset:
        parser.error("--dataset is required unless using --report")

    dataset = get_dataset(args.dataset, args.samples)
    print(f"Loaded {len(dataset)} samples from {args.dataset}")

    if args.pipeline == "all":
        asyncio.run(run_all(dataset, args.dataset, args.output, args.samples))
    else:
        async def _run():
            results = await run_pipeline(dataset, args.dataset, args.pipeline, args.output, args.samples, resume_from=args.resume)
            results = await _post_process(results, args.dataset)
            _resave_results(results, args.output, args.dataset)
            metrics = get_metrics_for_dataset(args.dataset, results)

            dtype = get_dataset_type(args.dataset)
            print(f"\nResults ({len(results)} samples):")

            if dtype == "ifeval":
                print(f"  Prompt Strict Accuracy: {metrics.get('prompt_strict_accuracy', 0):.1%}")
                print(f"  Instruction Strict Accuracy: {metrics.get('instruction_strict_accuracy', 0):.1%}")
                print(f"  Prompt Loose Accuracy: {metrics.get('prompt_loose_accuracy', 0):.1%}")
                print(f"  Mean Latency: {metrics.get('latency', {}).get('mean_ms', 0)/1000:.1f}s")
            elif dtype == "truthfulqa":
                print(f"  Truthful + Informative: {metrics.get('truthful_informative_rate', 0):.1%}")
                print(f"  Truthful Rate: {metrics.get('truthful_rate', 0):.1%}")
                print(f"  Informative Rate: {metrics.get('informative_rate', 0):.1%}")
                print(f"  Mean Latency: {metrics.get('latency', {}).get('mean_ms', 0)/1000:.1f}s")

            report_path = get_report_for_dataset(args.dataset, results, output_dir=args.output)
            print(f"\nReport: {report_path}")

        asyncio.run(_run())


if __name__ == "__main__":
    main()
