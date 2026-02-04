# ThinkTwice

> AI reasoning pipeline that drafts, self-critiques, fact-checks against live sources, and refines answers — with full transparency into every step.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-blue.svg)
![React](https://img.shields.io/badge/react-18-blue.svg)
![TypeScript](https://img.shields.io/badge/typescript-5-blue.svg)

## Screenshots

<!-- Add screenshots here -->
*Coming soon*

## Features

**Three Input Modes:**
- **Question Mode** — Ask any question and get a verified, refined answer
- **Fact-Check Mode** — Paste a claim and verify it against real sources
- **URL Mode** — Analyze any article and fact-check its claims

**Transparent Reasoning Pipeline:**
1. **Draft** — Initial response generation with mode-specific prompting
2. **Critique** — Adversarial self-analysis identifying issues, strengths, and claims to verify
3. **Verify** — Fact-check claims against web sources (Brave/Tavily) or AI knowledge
4. **Refine** — Produce final answer incorporating all feedback with confidence scores

**Real-time Streaming:**
- Server-Sent Events for live pipeline progress
- Token-by-token streaming for draft and refine steps
- Animated progress indicators and confidence bars

## Tech Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **Anthropic Claude API** (claude-sonnet-4-20250514)
- **httpx** for async HTTP
- **SSE-Starlette** for Server-Sent Events
- **Pydantic v2** for data validation
- **BeautifulSoup4** for URL content extraction

### Frontend
- **React 18** with **TypeScript**
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **Framer Motion** for animations
- **Lucide React** for icons
- **React Markdown** for rendering

### External APIs
- **Anthropic Claude** (required) — powers all reasoning steps
- **Brave Search** (optional) — fact verification
- **Tavily** (optional fallback) — alternative search

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Anthropic API key

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/apattichis/thinktwice.git
   cd thinktwice
   ```

2. **Set up environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

3. **Start the backend**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   python main.py
   ```

4. **Start the frontend** (in a new terminal)
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

5. **Open** http://localhost:5173

### Docker

```bash
# Build and run with Docker Compose
docker-compose up --build

# Access at http://localhost
```

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Your Anthropic API key |
| `BRAVE_SEARCH_API_KEY` | No | Brave Search API key for web verification |
| `TAVILY_API_KEY` | No | Tavily API key (fallback search) |
| `HOST` | No | Server host (default: 0.0.0.0) |
| `PORT` | No | Server port (default: 8000) |
| `FRONTEND_URL` | No | Frontend URL for CORS (default: http://localhost:5173) |

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  React + TypeScript + Tailwind + Framer Motion              │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Input   │→ │Pipeline │→ │  Step   │→ │ Metrics │        │
│  │  Area   │  │ Stepper │  │  Cards  │  │   Bar   │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
└─────────────────────────┬───────────────────────────────────┘
                          │ SSE Stream
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                        Backend                               │
│  FastAPI + Anthropic + httpx                                │
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐        │
│  │ Drafter │→ │ Critic  │→ │Verifier │→ │ Refiner │        │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘        │
│                               │                              │
│                               ▼                              │
│                    ┌──────────────────┐                     │
│                    │  Search Service  │                     │
│                    │ Brave → Tavily → │                     │
│                    │   AI Fallback    │                     │
│                    └──────────────────┘                     │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/think` | Main pipeline endpoint (SSE stream) |
| POST | `/api/think/single-shot` | Single LLM call for comparison |
| GET | `/api/examples` | Get example prompts |
| GET | `/api/health` | Health check |

## License

MIT
