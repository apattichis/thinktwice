# ThinkTwice

AI reasoning pipeline that drafts, self-critiques, fact-checks against live sources, and refines answers with full transparency.

## Screenshots

<p align="center">
  <img src="docs/screenshots/home.png" alt="Home" width="800">
</p>

<p align="center">
  <img src="docs/screenshots/pipeline.png" alt="Pipeline in action" width="800">
</p>

## Features

- **Three input modes**: Ask questions, verify claims, or analyze URLs
- **4-stage reasoning pipeline**: Draft → Critique → Verify → Refine
- **Real-time streaming**: Watch the AI think step by step
- **Source verification**: Claims checked against live web sources
- **Confidence tracking**: See how verification improves answer quality

## Tech Stack

| Layer | Technology |
|-------|------------|
| Frontend | Next.js 15, React 19, TypeScript, Tailwind CSS, Framer Motion |
| Backend | Python 3.11+, FastAPI, Pydantic v2, SSE-Starlette |
| AI | Anthropic Claude API |
| Search | Brave Search API / Tavily API |

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

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `BRAVE_SEARCH_API_KEY` | No | Brave Search for fact verification |
| `TAVILY_API_KEY` | No | Tavily API (fallback search) |

## Architecture

```
┌──────────────────────────────────────────────────────────┐
│                      Next.js Frontend                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Input   │→ │  Draft   │→ │ Critique │→ │  Verify  │ │
│  │   Area   │  │   View   │  │   View   │  │   View   │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
└───────────────────────┬──────────────────────────────────┘
                        │ SSE Stream
                        ▼
┌──────────────────────────────────────────────────────────┐
│                     FastAPI Backend                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Drafter │→ │  Critic  │→ │ Verifier │→ │  Refiner │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘ │
│                        │                                  │
│              ┌─────────┴─────────┐                       │
│              │   Search Service  │                       │
│              │ Brave → Tavily →  │                       │
│              │   AI Fallback     │                       │
│              └───────────────────┘                       │
└──────────────────────────────────────────────────────────┘
```

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/think` | Pipeline execution (SSE stream) |
| GET | `/api/examples` | Example prompts |
| GET | `/api/health` | Health check |

## License

MIT
