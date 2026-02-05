"""Ablation study runner for the ThinkTwice v2 pipeline.

Runs the pipeline with different components disabled to measure their
individual contributions. Supports parallel ablation runs.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from eval.runner import EvalRunner

logger = logging.getLogger(__name__)

# Ablation configurations
ABLATION_CONFIGS = {
    "single_shot": {
        "description": "Single-shot Claude (no pipeline, control group)",
        "pipeline_version": "single_shot",
        "overrides": {},
    },
    "v1_baseline": {
        "description": "V1 pipeline (4-step linear)",
        "pipeline_version": "v1",
        "overrides": {},
    },
    "v2_full": {
        "description": "V2 full pipeline (all components enabled)",
        "pipeline_version": "v2",
        "overrides": {},
    },
    "v2_no_gate": {
        "description": "V2 without gate (always refine)",
        "pipeline_version": "v2",
        "overrides": {"gate_threshold": 100},  # Impossible threshold = always refine
    },
    "v2_no_self_verify": {
        "description": "V2 without self-verification track",
        "pipeline_version": "v2",
        "overrides": {"self_verify_enabled": False},
    },
    "v2_no_loop": {
        "description": "V2 with single iteration (no convergence loop)",
        "pipeline_version": "v2",
        "overrides": {"max_iterations": 1},
    },
    "v2_no_trust": {
        "description": "V2 without trust comparison (always use refined)",
        "pipeline_version": "v2",
        "overrides": {"trust_blend_enabled": False},
    },
    "v2_gate_only": {
        "description": "V2 with aggressive gate (high fast-path rate)",
        "pipeline_version": "v2",
        "overrides": {"gate_threshold": 40, "gate_min_pass_rate": 0.5},
    },
}


async def run_ablation(
    dataset: list[dict],
    dataset_name: str,
    configs: Optional[list[str]] = None,
    output_dir: str = "results",
    max_samples: Optional[int] = None,
) -> dict:
    """Run ablation study across multiple configurations.

    Args:
        dataset: The evaluation dataset.
        dataset_name: Name for output files.
        configs: List of config names to run (None = all).
        output_dir: Output directory.
        max_samples: Max samples per configuration.

    Returns:
        Dict of config_name -> results.
    """
    target_configs = configs or list(ABLATION_CONFIGS.keys())
    all_results = {}

    for config_name in target_configs:
        config = ABLATION_CONFIGS.get(config_name)
        if not config:
            logger.warning("Unknown ablation config: %s", config_name)
            continue

        logger.info("Running ablation: %s — %s", config_name, config["description"])

        runner = EvalRunner(
            pipeline_version=config["pipeline_version"],
            output_dir=f"{output_dir}/ablation/{config_name}",
        )
        await runner.initialize()

        # Apply overrides
        if runner.pipeline and config["overrides"]:
            settings_override = config["overrides"]
            for key, value in settings_override.items():
                if key == "gate_threshold":
                    runner.pipeline.gatekeeper.gate_threshold = value
                elif key == "gate_min_pass_rate":
                    runner.pipeline.gatekeeper.gate_min_pass_rate = value
                elif key == "max_iterations":
                    runner.pipeline.max_iterations = value
                elif key == "self_verify_enabled":
                    runner.pipeline.verifier.self_verify_enabled = value
                elif key == "trust_blend_enabled":
                    runner.pipeline.truster.blend_enabled = value
                elif key == "convergence_threshold":
                    runner.pipeline.convergence_threshold = value

        results = await runner.run_dataset(
            dataset,
            f"{dataset_name}_{config_name}",
            max_samples=max_samples,
        )
        all_results[config_name] = results

    # Save combined ablation results
    output_path = Path(output_dir) / f"ablation_{dataset_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump({
            "dataset": dataset_name,
            "configs": {k: ABLATION_CONFIGS[k]["description"] for k in target_configs},
            "timestamp": datetime.now().isoformat(),
            "results": {k: len(v) for k, v in all_results.items()},
        }, f, indent=2)

    return all_results
