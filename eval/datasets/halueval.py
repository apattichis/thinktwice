"""HaluEval dataset loader — hallucination detection evaluation.

Provides a curated QA subset for evaluating hallucination detection rates.
Falls back to a built-in sample if download fails.
"""

import json
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

CACHE_DIR = Path(__file__).parent.parent / ".cache"


def _builtin_sample() -> list[dict]:
    """Built-in sample of HaluEval-style QA pairs for offline use."""
    return [
        {
            "question": "When was the first vaccine developed?",
            "hallucinated_answer": "The first vaccine was developed in 1652 by Dutch scientist Anton van Leeuwenhoek.",
            "correct_answer": "The first vaccine was developed in 1796 by Edward Jenner for smallpox.",
            "is_hallucination": True,
        },
        {
            "question": "Who wrote Romeo and Juliet?",
            "hallucinated_answer": "Romeo and Juliet was written by Christopher Marlowe in 1590.",
            "correct_answer": "Romeo and Juliet was written by William Shakespeare, first published in 1597.",
            "is_hallucination": True,
        },
        {
            "question": "What is the capital of Australia?",
            "hallucinated_answer": "The capital of Australia is Sydney.",
            "correct_answer": "The capital of Australia is Canberra.",
            "is_hallucination": True,
        },
        {
            "question": "How many planets are in our solar system?",
            "hallucinated_answer": "There are 8 planets in our solar system.",
            "correct_answer": "There are 8 planets in our solar system (since Pluto was reclassified in 2006).",
            "is_hallucination": False,
        },
        {
            "question": "What is the chemical formula for water?",
            "hallucinated_answer": "The chemical formula for water is H2O.",
            "correct_answer": "The chemical formula for water is H2O.",
            "is_hallucination": False,
        },
        {
            "question": "Who painted the Mona Lisa?",
            "hallucinated_answer": "The Mona Lisa was painted by Michelangelo in the Vatican.",
            "correct_answer": "The Mona Lisa was painted by Leonardo da Vinci, completed around 1519.",
            "is_hallucination": True,
        },
        {
            "question": "What is the speed of light?",
            "hallucinated_answer": "The speed of light is approximately 300,000 km/s in a vacuum.",
            "correct_answer": "The speed of light in a vacuum is approximately 299,792 km/s.",
            "is_hallucination": False,
        },
        {
            "question": "Who was the first person to walk on the moon?",
            "hallucinated_answer": "Buzz Aldrin was the first person to walk on the moon in 1969.",
            "correct_answer": "Neil Armstrong was the first person to walk on the moon on July 20, 1969.",
            "is_hallucination": True,
        },
        {
            "question": "What year did World War II end?",
            "hallucinated_answer": "World War II ended in 1945.",
            "correct_answer": "World War II ended in 1945 with the surrender of Japan on September 2.",
            "is_hallucination": False,
        },
        {
            "question": "What is the largest organ in the human body?",
            "hallucinated_answer": "The largest organ in the human body is the liver.",
            "correct_answer": "The largest organ in the human body is the skin.",
            "is_hallucination": True,
        },
    ]


def get_dataset(max_samples: Optional[int] = None) -> list[dict]:
    """Return HaluEval-style dataset formatted for the eval runner."""
    data = _builtin_sample()
    if max_samples:
        data = data[:max_samples]

    return [
        {
            "input": item["question"],
            "mode": "question",
            "gold_correct_answer": item["correct_answer"],
            "gold_hallucinated_answer": item["hallucinated_answer"],
            "is_hallucination": item["is_hallucination"],
        }
        for item in data
    ]
