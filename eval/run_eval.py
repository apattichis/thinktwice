"""CLI entry point for the ThinkTwice evaluation framework.

Usage:
    python eval/run_eval.py --dataset factcheck_bench --pipeline thinktwice --output results/
    python eval/run_eval.py --dataset truthfulqa --pipeline all --output results/ --samples 100
    python eval/run_eval.py --ablation --dataset factcheck_bench --output results/
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
from eval.metrics import compute_all_metrics
from eval.report import generate_report
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
    if name == "factcheck50":
        from eval.datasets.factcheck50 import get_dataset
        return get_dataset()[:max_samples] if max_samples else get_dataset()
    elif name == "factcheck_bench":
        from eval.datasets.factcheck_bench import get_dataset
        return get_dataset()[:max_samples] if max_samples else get_dataset()
    elif name == "truthfulqa":
        from eval.datasets.truthfulqa import get_dataset
        return get_dataset(max_samples=max_samples)
    elif name == "halueval":
        from eval.datasets.halueval import get_dataset
        return get_dataset(max_samples=max_samples)
    else:
        raise ValueError(f"Unknown dataset: {name}. Choose from: factcheck50, factcheck_bench, truthfulqa, halueval")


async def run_pipeline(dataset: list[dict], dataset_name: str, version: str, output_dir: str, max_samples: int | None = None, resume_from: str | None = None):
    """Run a single pipeline version on a dataset."""
    runner = EvalRunner(pipeline_version=version, output_dir=output_dir)
    await runner.initialize()
    results = await runner.run_dataset(dataset, f"{dataset_name}", max_samples=max_samples, resume_from=resume_from)
    return results


async def run_all(dataset: list[dict], dataset_name: str, output_dir: str, max_samples: int | None = None):
    """Run single-shot baseline and ThinkTwice on the same dataset and compare.

    Two baselines:
    - Single-shot: Raw Claude API call, no pipeline (control group)
    - ThinkTwice: Self-correcting pipeline with gating, iteration, and trust ranking
    """
    print(f"\n{'='*60}")
    print(f"  Running SINGLE-SHOT baseline on {dataset_name}...")
    print(f"{'='*60}\n")
    ss_results = await run_pipeline(dataset, dataset_name, "single_shot", f"{output_dir}/single_shot", max_samples)

    print(f"\n{'='*60}")
    print(f"  Running THINKTWICE pipeline on {dataset_name}...")
    print(f"{'='*60}\n")
    tt_results = await run_pipeline(dataset, dataset_name, "thinktwice", f"{output_dir}/thinktwice", max_samples)

    # Compare pipelines
    comparison = compare_pipelines(ss_results, tt_results)

    # Compute single-shot metrics for the report
    ss_metrics = compute_all_metrics(ss_results)

    # Generate report with both baselines
    report_path = generate_report(
        tt_results,
        dataset_name,
        output_dir=output_dir,
        comparison=comparison,
        single_shot_metrics=ss_metrics,
    )

    ssm = ss_metrics
    ttm = comparison['thinktwice_metrics']

    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"\n  {'Metric':<22} {'Single-Shot':>12} {'ThinkTwice':>12}")
    print(f"  {'-'*46}")
    print(f"  {'Accuracy':<22} {ssm['accuracy']['accuracy']:>11.1%} {ttm['accuracy']['accuracy']:>11.1%}")
    print(f"  {'Macro F1':<22} {ssm['classification']['macro']['f1']:>11.3f} {ttm['classification']['macro']['f1']:>11.3f}")
    print(f"  {'Weighted F1':<22} {ssm['classification']['weighted']['f1']:>11.3f} {ttm['classification']['weighted']['f1']:>11.3f}")
    print(f"  {'Mean Latency':<22} {ssm['latency']['mean_ms']/1000:>10.1f}s {ttm['latency']['mean_ms']/1000:>10.1f}s")

    sig = comparison.get('statistical_significance', {})
    if sig:
        print(f"\n  Statistical Significance (ThinkTwice vs Single-Shot):")
        if sig.get("test") == "mcnemar":
            chi2 = sig.get("chi2", "N/A")
            p = sig.get("p_value", 1)
            print(f"    chi2={chi2}, p={p:.6f} {'(significant)' if sig.get('significant') else '(not significant)'}")
        else:
            print(f"    t={sig.get('t_stat', 0):.4f}, p={sig.get('p_approx', 1):.6f} {'(significant)' if sig.get('significant') else '(not significant)'}")

    print(f"\n  Report: {report_path}")
    return ss_results, tt_results, comparison


async def run_ablation(dataset: list[dict], dataset_name: str, output_dir: str, max_samples: int | None = None):
    """Run ablation study."""
    from eval.ablation import run_ablation as _run_ablation

    print(f"\n{'='*60}")
    print(f"Running ablation study on {dataset_name}...")
    print(f"{'='*60}\n")

    ablation_results = await _run_ablation(
        dataset, dataset_name, output_dir=output_dir, max_samples=max_samples
    )

    # Compute metrics per config
    for config_name, results in ablation_results.items():
        metrics = compute_all_metrics(results)
        print(f"\n{config_name}:")
        print(f"  Accuracy: {metrics['accuracy']['accuracy']:.1%}")
        print(f"  Constraint Satisfaction: {metrics['constraint_satisfaction']['satisfaction_rate']:.1%}")
        print(f"  Mean Latency: {metrics['latency']['mean_ms']/1000:.1f}s")

    # Generate report with ablation
    report_path = generate_report(
        ablation_results.get("thinktwice_full", []),
        dataset_name,
        output_dir=output_dir,
        ablation_results=ablation_results,
    )
    print(f"\nAblation report generated: {report_path}")


async def generate_report_from_files(input_dir: str, output_dir: str):
    """Generate a report from existing result files."""
    input_path = Path(input_dir)
    result_files = list(input_path.glob("*.json"))

    if not result_files:
        print(f"No result files found in {input_dir}")
        return

    # Load the most recent result file
    result_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    latest = result_files[0]
    print(f"Loading results from: {latest}")

    with open(latest) as f:
        data = json.load(f)

    results = data.get("results", [])
    dataset_name = data.get("dataset", "unknown")

    report_path = generate_report(results, dataset_name, output_dir=output_dir)
    print(f"Report generated: {report_path}")


def main():
    parser = argparse.ArgumentParser(
        description="ThinkTwice Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python eval/run_eval.py --dataset factcheck_bench --pipeline thinktwice
  python eval/run_eval.py --dataset truthfulqa --pipeline all --samples 50
  python eval/run_eval.py --ablation --dataset factcheck_bench
  python eval/run_eval.py --report --input results/
        """,
    )

    parser.add_argument("--dataset", choices=["factcheck50", "factcheck_bench", "truthfulqa", "halueval"],
                        help="Dataset to evaluate on")
    parser.add_argument("--pipeline", choices=["thinktwice", "single_shot", "all"], default="thinktwice",
                        help="Pipeline version: thinktwice, single_shot, or all (runs both)")
    parser.add_argument("--output", default="results", help="Output directory (default: results)")
    parser.add_argument("--samples", type=int, default=None, help="Max samples to process")
    parser.add_argument("--ablation", action="store_true", help="Run ablation study")
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

    if args.ablation:
        asyncio.run(run_ablation(dataset, args.dataset, args.output, args.samples))
    elif args.pipeline == "all":
        asyncio.run(run_all(dataset, args.dataset, args.output, args.samples))
    else:
        async def _run():
            results = await run_pipeline(dataset, args.dataset, args.pipeline, args.output, args.samples, resume_from=args.resume)
            metrics = compute_all_metrics(results)
            print(f"\nResults ({len(results)} samples):")
            print(f"  Accuracy: {metrics['accuracy']['accuracy']:.1%}")
            print(f"  Constraint Satisfaction: {metrics['constraint_satisfaction']['satisfaction_rate']:.1%}")
            print(f"  Mean Latency: {metrics['latency']['mean_ms']/1000:.1f}s")

            report_path = generate_report(results, args.dataset, output_dir=args.output)
            print(f"\nReport: {report_path}")

        asyncio.run(_run())


if __name__ == "__main__":
    main()
