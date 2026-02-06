"""CLI entry point for the ThinkTwice evaluation framework.

Usage:
    python eval/run_eval.py --dataset factcheck50 --pipeline v2 --output results/
    python eval/run_eval.py --dataset truthfulqa --pipeline both --output results/ --samples 100
    python eval/run_eval.py --ablation --dataset factcheck50 --output results/
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
from eval.compare import compare_v1_v2


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
    """Run single-shot baseline, v1, and v2 on the same dataset and compare.

    Three baselines:
    - Single-shot: Raw Claude API call, no pipeline (control group)
    - V1: Original 4-step linear pipeline
    - V2: Research-inspired pipeline with gating, iteration, and trust ranking
    """
    print(f"\n{'='*60}")
    print(f"  Running SINGLE-SHOT baseline on {dataset_name}...")
    print(f"{'='*60}\n")
    ss_results = await run_pipeline(dataset, dataset_name, "single_shot", f"{output_dir}/single_shot", max_samples)

    print(f"\n{'='*60}")
    print(f"  Running V1 pipeline on {dataset_name}...")
    print(f"{'='*60}\n")
    v1_results = await run_pipeline(dataset, dataset_name, "v1", f"{output_dir}/v1", max_samples)

    print(f"\n{'='*60}")
    print(f"  Running V2 pipeline on {dataset_name}...")
    print(f"{'='*60}\n")
    v2_results = await run_pipeline(dataset, dataset_name, "v2", f"{output_dir}/v2", max_samples)

    # Compare v1 vs v2
    comparison = compare_v1_v2(v1_results, v2_results)

    # 3-way McNemar's test
    from eval.compare import mcnemar_three_way
    comparison["mcnemar_three_way"] = mcnemar_three_way(ss_results, v1_results, v2_results)

    # Compute single-shot metrics for the report
    ss_metrics = compute_all_metrics(ss_results)

    # Generate report with all baselines
    report_path = generate_report(
        v2_results,
        dataset_name,
        output_dir=output_dir,
        comparison=comparison,
        single_shot_metrics=ss_metrics,
    )

    v1m = comparison['v1_metrics']
    v2m = comparison['v2_metrics']

    print(f"\n{'='*60}")
    print(f"  RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"\n  {'Metric':<22} {'Single-Shot':>12} {'V1':>12} {'V2':>12}")
    print(f"  {'-'*58}")
    print(f"  {'Accuracy':<22} {ss_metrics['accuracy']['accuracy']:>11.1%} {v1m['accuracy']['accuracy']:>11.1%} {v2m['accuracy']['accuracy']:>11.1%}")
    print(f"  {'Macro F1':<22} {ss_metrics['classification']['macro']['f1']:>11.3f} {v1m['classification']['macro']['f1']:>11.3f} {v2m['classification']['macro']['f1']:>11.3f}")
    print(f"  {'Weighted F1':<22} {ss_metrics['classification']['weighted']['f1']:>11.3f} {v1m['classification']['weighted']['f1']:>11.3f} {v2m['classification']['weighted']['f1']:>11.3f}")
    print(f"  {'Mean Latency':<22} {ss_metrics['latency']['mean_ms']/1000:>10.1f}s {v1m['latency']['mean_ms']/1000:>10.1f}s {v2m['latency']['mean_ms']/1000:>10.1f}s")

    sig = comparison.get('statistical_significance', {})
    if sig:
        print(f"\n  Statistical Significance (V2 vs V1):")
        print(f"    t={sig.get('t_stat', 0):.4f}, p={sig.get('p_approx', 1):.6f} {'(significant)' if sig.get('significant') else '(not significant)'}")

    print(f"\n  Report: {report_path}")
    return ss_results, v1_results, v2_results, comparison


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
        ablation_results.get("v2_full", []),
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
  python eval/run_eval.py --dataset factcheck50 --pipeline v2
  python eval/run_eval.py --dataset truthfulqa --pipeline both --samples 50
  python eval/run_eval.py --ablation --dataset factcheck50
  python eval/run_eval.py --report --input results/
        """,
    )

    parser.add_argument("--dataset", choices=["factcheck50", "factcheck_bench", "truthfulqa", "halueval"],
                        help="Dataset to evaluate on")
    parser.add_argument("--pipeline", choices=["v1", "v2", "single_shot", "all"], default="v2",
                        help="Pipeline version: v1, v2, single_shot, or all (runs all 3 baselines)")
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
