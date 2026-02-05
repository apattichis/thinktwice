# ThinkTwice

AI fact-verification pipeline with self-correction. Drafts answers, decomposes constraints, gates confident outputs, iteratively critiques and verifies against live sources, then trust-ranks the best response — all streamed in real time.

## Screenshots

<p align="center">
  <img src="docs/screenshots/home.png" alt="Home" width="800">
</p>

<p align="center">
  <img src="docs/screenshots/pipeline.png" alt="Pipeline in action" width="800">
</p>

## Features

- **Three input modes**: Ask questions, verify claims, or analyze URLs
- **Two pipeline versions**: V1 (linear 4-step) and V2 (research-inspired self-correction)
- **V2 pipeline**: Decompose → Draft → Gate → [Critique → Verify → Refine → Converge]×N → Trust & Rank
- **Constraint decomposition**: Breaks inputs into atomic verifiable constraints (DeCRIM-inspired)
- **Intelligent gating**: Confident drafts skip refinement, saving latency (ART-inspired)
- **Dual verification**: Web search + self-verification for higher accuracy (ReVISE-inspired)
- **Iterative refinement**: Converges through multiple critique-verify-refine cycles
- **Trust ranking**: Compares original draft vs refined output, picks the best
- **Real-time streaming**: Watch every pipeline phase via SSE events
- **Evaluation framework**: Built-in benchmarks (FactCheck50, TruthfulQA, HaluEval) with ablation studies

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 16, React 19, TypeScript, Tailwind CSS v4, Framer Motion |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SSE-Starlette |
| AI | Anthropic Claude API (tool use for structured outputs) |
| Search | Brave Search API / Tavily API |
| Eval | matplotlib, scipy (optional, for charts and stats) |

## Architecture

### V1 Pipeline (Linear)

```
Input → Draft → Critique → Verify → Refine → Output
```

### V2 Pipeline (Self-Correcting)

```
                    ┌─────────────────────────────────────────────┐
                    │            V2 Pipeline Flow                  │
                    │                                              │
  Input ──→ Decompose ──→ Draft ──→ Gate ──┬──→ Fast Path ──→ Output
                                           │
                                    Needs Work
                                           │
                              ┌─────────── ▼ ───────────┐
                              │   Refinement Loop (×N)   │
                              │                          │
                              │  Critique (per-constraint)│
                              │       │                  │
                              │       ▼                  │
                              │  Verify (web + self)     │
                              │       │                  │
                              │       ▼                  │
                              │  Refine (selective)      │
                              │       │                  │
                              │       ▼                  │
                              │  Converge? ──No──→ Loop  │
                              │       │                  │
                              │      Yes                 │
                              └───────┼──────────────────┘
                                      ▼
                              Trust & Rank
                              (draft vs refined)
                                      │
                                      ▼
                                   Output
```

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 20+
- Anthropic API key

### Setup

```bash
# Clone
git clone https://github.com/apattichis/thinktwice.git
cd thinktwice

# Configure
cp .env.example .env
# Add your ANTHROPIC_API_KEY to .env

# Backend
cd backend
pip install -r requirements.txt
python main.py

# Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Docker

```bash
docker-compose up --build
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | Yes | — | Anthropic API key |
| `BRAVE_SEARCH_API_KEY` | No | — | Brave Search for fact verification |
| `TAVILY_API_KEY` | No | — | Tavily API (fallback search) |
| `GATE_THRESHOLD` | No | `85` | Confidence threshold for gate fast-path (0–100) |
| `GATE_MIN_PASS_RATE` | No | `1.0` | Min sub-question pass rate for gate (0.0–1.0) |
| `MAX_ITERATIONS` | No | `3` | Max refinement loop iterations |
| `CONVERGENCE_THRESHOLD` | No | `80` | Convergence confidence threshold (0–100) |
| `SELF_VERIFY_ENABLED` | No | `true` | Enable self-verification track |
| `SELF_VERIFY_PARALLEL` | No | `true` | Run web + self verification in parallel |
| `TRUST_BLEND_ENABLED` | No | `true` | Enable trust comparison (draft vs refined) |

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/think?version=v2` | Pipeline execution (SSE stream). Version: `v1` or `v2` |
| POST | `/api/think/single-shot` | Single LLM call without pipeline (baseline) |
| GET | `/api/examples` | Example prompts |
| GET | `/api/health` | Health check |

### V2 Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `version` | `v1` \| `v2` | Pipeline version (default: `v2`) |
| `max_iterations` | int (1–10) | Override max refinement iterations |
| `gate_threshold` | int (0–100) | Override gate confidence threshold |

### SSE Event Types

**V1 Events**: `step_start`, `step_stream`, `step_complete`, `verify_claim`, `pipeline_complete`

**V2 Additional Events**: `decompose_complete`, `gate_decision`, `constraint_verdict`, `self_verify_claim`, `iteration_start`, `iteration_complete`, `trust_decision`

## Evaluation

Built-in evaluation framework for benchmarking pipeline accuracy and ablation studies.

```bash
# Run V2 on FactCheck50
python eval/run_eval.py --dataset factcheck50 --pipeline v2

# Compare all baselines (single-shot, V1, V2)
python eval/run_eval.py --dataset factcheck50 --pipeline all

# Run ablation study
python eval/run_eval.py --ablation --dataset factcheck50

# Limit samples for quick testing
python eval/run_eval.py --dataset truthfulqa --pipeline all --samples 20

# Generate report from existing results
python eval/run_eval.py --report --input results/
```

### Datasets

| Dataset | Size | Type |
|---------|------|------|
| FactCheck50 | 50 claims | Curated fact-check claims across 6 domains |
| TruthfulQA | ~800 questions | Common misconceptions (auto-downloaded) |
| HaluEval | 10 samples | Hallucination detection |

### Ablation Configurations

| Config | Description |
|--------|-------------|
| `single_shot` | Raw Claude call, no pipeline (control) |
| `v1_baseline` | V1 linear 4-step pipeline |
| `v2_full` | V2 with all components enabled |
| `v2_no_gate` | V2 without gating (always refine) |
| `v2_no_self_verify` | V2 without self-verification track |
| `v2_no_loop` | V2 with single iteration only |
| `v2_no_trust` | V2 without trust comparison |
| `v2_gate_only` | V2 with aggressive gating |

## Testing

```bash
cd backend
pip install pytest pytest-asyncio
pytest tests/ -v
```

## License

MIT
