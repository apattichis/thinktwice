"""IFEval dataset loader -- Instruction-Following Evaluation.

Downloads IFEval from HuggingFace (google/IFEval) and formats prompts
for the pipeline. Evaluates using deterministic instruction verifiers.

IFEval tests constraint-following: can the model produce output that
satisfies specific formatting, content, and structural instructions?
This maps to ThinkTwice's Decompose -> Gate -> Critique -> Refine loop.
"""

import json
import logging
import random
from collections import Counter
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DATASET_URL = "https://huggingface.co/datasets/google/IFEval/resolve/main/data/train-00000-of-00001.parquet"
DATASET_URL_JSON = "https://huggingface.co/api/datasets/google/IFEval/parquet/default/train"
CACHE_DIR = Path(__file__).parent.parent / ".cache"


def download_dataset() -> list[dict]:
    """Download and parse IFEval dataset from HuggingFace.

    Tries JSON API first, falls back to parquet, then built-in sample.
    """
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / "ifeval.json"

    if cache_file.exists():
        with open(cache_file) as f:
            return json.load(f)

    # Try HuggingFace datasets server API (paginated JSON rows)
    try:
        import urllib.request

        logger.info("Downloading IFEval dataset from HuggingFace...")

        data = []
        page_size = 100
        offset = 0

        while True:
            api_url = f"https://datasets-server.huggingface.co/rows?dataset=google%2FIFEval&config=default&split=train&offset={offset}&length={page_size}"
            req = urllib.request.Request(api_url, headers={"User-Agent": "ThinkTwice-Eval/1.0"})
            with urllib.request.urlopen(req, timeout=30) as resp:
                api_data = json.loads(resp.read().decode("utf-8"))

            rows = api_data.get("rows", [])
            if not rows:
                break

            for row_wrapper in rows:
                row = row_wrapper.get("row", row_wrapper)
                data.append({
                    "prompt": row.get("prompt", ""),
                    "key": row.get("key", ""),
                    "instruction_id_list": row.get("instruction_id_list", []),
                    "kwargs": row.get("kwargs", []),
                })

            offset += page_size
            if len(rows) < page_size:
                break

        if data:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Downloaded %d IFEval prompts", len(data))
            return data

    except Exception as e:
        logger.warning("HuggingFace API download failed: %s", e)

    # Try direct parquet download
    try:
        import urllib.request
        parquet_path = CACHE_DIR / "ifeval.parquet"
        logger.info("Trying parquet download...")
        urllib.request.urlretrieve(DATASET_URL, str(parquet_path))

        try:
            import pyarrow.parquet as pq
            table = pq.read_table(str(parquet_path))
            df = table.to_pydict()
            data = []
            for i in range(len(df.get("prompt", []))):
                data.append({
                    "prompt": df["prompt"][i],
                    "key": df.get("key", [""])[i] if "key" in df else "",
                    "instruction_id_list": json.loads(df["instruction_id_list"][i]) if isinstance(df["instruction_id_list"][i], str) else df["instruction_id_list"][i],
                    "kwargs": json.loads(df["kwargs"][i]) if isinstance(df["kwargs"][i], str) else df["kwargs"][i],
                })

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.info("Downloaded %d IFEval prompts from parquet", len(data))
            return data
        except ImportError:
            logger.warning("pyarrow not installed, cannot read parquet")

    except Exception as e:
        logger.warning("Parquet download failed: %s", e)

    logger.warning("Using built-in IFEval sample (5 prompts)")
    return _builtin_sample()


def _builtin_sample() -> list[dict]:
    """Built-in sample for offline testing."""
    return [
        {
            "prompt": "Write a short poem about the ocean. Your poem must have exactly 4 lines. Each line must contain at least 8 words.",
            "key": "builtin_1",
            "instruction_id_list": ["length_constraints:number_sentences", "length_constraints:number_words"],
            "kwargs": [{"relation": "at least", "num_sentences": 4}, {"relation": "at least", "num_words": 32}],
        },
        {
            "prompt": "Give me a summary of World War 2 in exactly 3 paragraphs. The response must be in all lowercase.",
            "key": "builtin_2",
            "instruction_id_list": ["length_constraints:number_paragraphs", "change_case:english_lowercase"],
            "kwargs": [{"num_paragraphs": 3}, {}],
        },
        {
            "prompt": "List 5 benefits of exercise. Your answer must include the keywords 'health', 'energy', and 'mental'. Use bullet points for each benefit.",
            "key": "builtin_3",
            "instruction_id_list": ["keywords:existence", "detectable_format:number_bullet_lists"],
            "kwargs": [{"keywords": ["health", "energy", "mental"]}, {"num_bullets": 5}],
        },
        {
            "prompt": "Explain photosynthesis. Your response must end with the exact phrase 'This is how plants create energy.'",
            "key": "builtin_4",
            "instruction_id_list": ["startend:end_checker"],
            "kwargs": [{"end_phrase": "This is how plants create energy."}],
        },
        {
            "prompt": "Write a JSON object that describes a cat with fields for name, age, and color. Do not use any commas in your response outside of the JSON.",
            "key": "builtin_5",
            "instruction_id_list": ["detectable_format:json_format"],
            "kwargs": [{}],
        },
    ]


def _stratified_sample(data: list[dict], n: int = 120, seed: int = 42) -> list[dict]:
    """Stratified sampling by instruction count and instruction type coverage.

    Ensures representation of 1-instruction, 2-instruction, and 3+-instruction
    prompts, while maximizing coverage of the 25 instruction types.
    """
    if len(data) <= n:
        return data

    rng = random.Random(seed)

    # Group by instruction count
    by_count = {1: [], 2: [], 3: []}  # 3 means 3+
    for item in data:
        count = len(item.get("instruction_id_list", []))
        bucket = min(count, 3)
        if bucket >= 1:
            by_count[bucket].append(item)

    # Proportional allocation (keeping original ratios)
    total = sum(len(v) for v in by_count.values())
    allocation = {}
    remaining = n
    for bucket in sorted(by_count.keys()):
        if bucket == max(by_count.keys()):
            allocation[bucket] = remaining
        else:
            alloc = round(n * len(by_count[bucket]) / total)
            allocation[bucket] = min(alloc, len(by_count[bucket]))
            remaining -= allocation[bucket]

    # Sample from each bucket, prioritizing type coverage
    sampled = []
    for bucket, count in allocation.items():
        pool = by_count[bucket]
        if len(pool) <= count:
            sampled.extend(pool)
        else:
            # Score by instruction type rarity to maximize coverage
            type_counts = Counter()
            for item in pool:
                for iid in item.get("instruction_id_list", []):
                    type_counts[iid] += 1

            def rarity_score(item):
                ids = item.get("instruction_id_list", [])
                if not ids:
                    return 0
                return sum(1 / type_counts.get(iid, 1) for iid in ids)

            # Sort by rarity (rarest types first), then shuffle within score tiers
            pool_scored = [(rarity_score(item), rng.random(), item) for item in pool]
            pool_scored.sort(key=lambda x: (-x[0], x[1]))
            sampled.extend(item for _, _, item in pool_scored[:count])

    rng.shuffle(sampled)
    return sampled


def get_dataset(max_samples: int | None = None) -> list[dict]:
    """Return IFEval formatted for the eval runner."""
    raw = download_dataset()

    # Apply stratified sampling
    target = max_samples or 120
    sampled = _stratified_sample(raw, n=target)

    return [
        {
            "input": item["prompt"],
            "mode": "question",
            "ifeval_key": item.get("key", ""),
            "instruction_id_list": item.get("instruction_id_list", []),
            "instruction_kwargs": item.get("kwargs", []),
            "instruction_count": len(item.get("instruction_id_list", [])),
        }
        for item in sampled
    ]
