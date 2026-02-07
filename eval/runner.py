"""Evaluation runner -- processes datasets through the ThinkTwice pipeline.

Supports single-shot baseline and ThinkTwice pipeline. Tracks all metrics
per sample, saves results to JSON, and supports resuming from checkpoints.

Baselines:
  - single_shot: Raw Claude API call, no pipeline (control group)
  - thinktwice: Self-correcting pipeline with gating, iteration, and trust ranking
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add backend to path for direct imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

# Load .env from project root (config.py uses ../. relative to backend/)
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

from config import get_settings
from services.llm import LLMService
from services.search import SearchService
from services.scraper import ScraperService
from core.pipeline import ThinkTwicePipeline

logger = logging.getLogger(__name__)


class EvalRunner:
    """Runs evaluation datasets through the pipeline and collects results."""

    def __init__(
        self,
        pipeline_version: str = "thinktwice",
        output_dir: str = "results",
        checkpoint_interval: int = 5,
    ):
        self.pipeline_version = pipeline_version
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.checkpoint_interval = checkpoint_interval
        self.pipeline: Optional[ThinkTwicePipeline] = None
        self.results: list[dict] = []

    async def initialize(self) -> None:
        """Initialize the pipeline for evaluation."""
        settings = get_settings()
        llm = LLMService(
            api_key=settings.anthropic_api_key,
            model=settings.model_name,
            max_tokens=settings.max_tokens,
            timeout=settings.timeout,
        )
        search = SearchService(
            brave_key=settings.brave_search_api_key,
            tavily_key=settings.tavily_api_key,
        )
        scraper = ScraperService()
        self.pipeline = ThinkTwicePipeline(
            llm=llm,
            search=search,
            scraper=scraper,
            gate_threshold=settings.gate_threshold,
            gate_min_pass_rate=settings.gate_min_pass_rate,
            max_iterations=settings.max_iterations,
            convergence_threshold=settings.convergence_threshold,
            self_verify_enabled=settings.self_verify_enabled,
            self_verify_parallel=settings.self_verify_parallel,
            trust_blend_enabled=settings.trust_blend_enabled,
        )

    async def run_single_shot(self, input_text: str) -> dict:
        """Run a single-shot baseline (raw Claude, no pipeline).

        This is the control group -- same model, zero self-correction.
        Shows the raw value added by the pipeline.
        """
        from models.schemas import ThinkRequest

        request = ThinkRequest(input=input_text)

        start = time.monotonic()
        try:
            output = await self.pipeline.single_shot(request)
        except Exception as e:
            logger.error("Single-shot failed: %s", e)
            output = f"Error: {e}"

        duration = int((time.monotonic() - start) * 1000)

        return {
            "input": input_text,
            "pipeline_version": "single_shot",
            "output": output,
            "duration_ms": duration,
            "metrics": {
                "total_duration_ms": duration,
                "confidence_before": 0,
                "confidence_after": 0,
                "gate_decision": "N/A",
                "fast_path": True,
                "iterations_used": 0,
                "trust_winner": "N/A",
                "constraints_total": 0,
                "constraints_satisfied": 0,
                "claims_checked": 0,
                "claims_verified": 0,
                "claims_refuted": 0,
                "claims_unclear": 0,
            },
            "events": [],
            "timestamp": datetime.now().isoformat(),
        }

    async def run_single(self, input_text: str) -> dict:
        """Run a single input through the pipeline and collect all events."""
        # Single-shot baseline uses a separate path
        if self.pipeline_version == "single_shot":
            return await self.run_single_shot(input_text)

        from models.schemas import ThinkRequest

        request = ThinkRequest(input=input_text)

        events = []
        final_output = ""
        draft_output = ""
        last_refine_content = ""
        metrics_data = {}
        start = time.monotonic()

        try:
            async for event_str in self.pipeline.execute(request):
                # Parse SSE event
                lines = event_str.strip().split("\n")
                event_name = ""
                event_data = {}
                for line in lines:
                    if line.startswith("event: "):
                        event_name = line[7:]
                    elif line.startswith("data: "):
                        try:
                            event_data = json.loads(line[6:])
                        except json.JSONDecodeError:
                            pass

                events.append({"event": event_name, "data": event_data})

                # Capture draft content for format guard comparison
                if event_name == "step_complete" and event_data.get("step") == "draft":
                    draft_output = event_data.get("content", "")

                # Capture refine step content as fallback for final output
                if event_name == "step_complete" and event_data.get("step") == "refine":
                    last_refine_content = event_data.get("content", "")

                if event_name == "pipeline_complete":
                    final_output = event_data.get("final_output", "")
                    metrics_data = event_data

        except Exception as e:
            logger.error("Pipeline failed for input: %s -- %s", input_text[:100], e)
            return {
                "input": input_text,
                "pipeline_version": self.pipeline_version,
                "error": str(e),
                "duration_ms": int((time.monotonic() - start) * 1000),
                "events": events,
            }

        duration = int((time.monotonic() - start) * 1000)

        # Use refine step content as fallback if pipeline_complete didn't include final_output
        if not final_output and last_refine_content:
            final_output = last_refine_content

        return {
            "input": input_text,
            "pipeline_version": self.pipeline_version,
            "output": final_output,
            "draft_output": draft_output,
            "duration_ms": duration,
            "metrics": metrics_data,
            "events": events,
            "timestamp": datetime.now().isoformat(),
        }

    async def run_dataset(
        self,
        dataset: list[dict],
        dataset_name: str,
        max_samples: Optional[int] = None,
        resume_from: Optional[str] = None,
    ) -> list[dict]:
        """Run a full dataset through the pipeline.

        Args:
            dataset: List of dicts with 'input', 'mode', and optional gold fields.
            dataset_name: Name for output files.
            max_samples: Limit number of samples to process.
            resume_from: Path to checkpoint file to resume from.
        """
        if not self.pipeline:
            await self.initialize()

        # Resume from checkpoint
        completed_inputs = set()
        if resume_from and Path(resume_from).exists():
            with open(resume_from) as f:
                checkpoint_data = json.load(f)
                self.results = checkpoint_data.get("results", [])
                completed_inputs = {r["input"] for r in self.results}
                logger.info("Resumed from checkpoint: %d completed", len(completed_inputs))

        samples = dataset[:max_samples] if max_samples else dataset
        total = len(samples)

        for i, sample in enumerate(samples):
            if sample["input"] in completed_inputs:
                continue

            logger.info("[%d/%d] Processing: %s", i + 1, total, sample["input"][:80])

            result = await self.run_single(sample["input"])

            # Attach all sample metadata (gold data, domain, etc.)
            for key, value in sample.items():
                if key not in ("input", "mode"):
                    result[key] = value

            self.results.append(result)

            # Checkpoint
            if (i + 1) % self.checkpoint_interval == 0:
                self._save_checkpoint(dataset_name)
                logger.info("Checkpoint saved (%d/%d)", i + 1, total)

        # Save final results
        self._save_results(dataset_name)
        return self.results

    def _save_checkpoint(self, dataset_name: str) -> None:
        """Save checkpoint for resuming."""
        path = self.output_dir / f"{dataset_name}_checkpoint.json"
        with open(path, "w") as f:
            json.dump({"results": self.results, "timestamp": datetime.now().isoformat()}, f, indent=2)

    def _save_results(self, dataset_name: str) -> None:
        """Save final results."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = self.output_dir / f"{dataset_name}_{self.pipeline_version}_{timestamp}.json"
        with open(path, "w") as f:
            json.dump({
                "dataset": dataset_name,
                "pipeline_version": self.pipeline_version,
                "total_samples": len(self.results),
                "timestamp": datetime.now().isoformat(),
                "results": self.results,
            }, f, indent=2)
        logger.info("Results saved to %s", path)

        # Remove checkpoint
        checkpoint = self.output_dir / f"{dataset_name}_checkpoint.json"
        if checkpoint.exists():
            checkpoint.unlink()
