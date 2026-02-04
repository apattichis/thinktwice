# 🧠 ThinkTwice — AI That Catches Its Own Mistakes

> A real-time agentic reasoning pipeline that drafts, self-critiques, fact-checks against live sources, and refines answers — with full transparency into every step.

---

## What This Actually Does (Concrete Use Case)

ThinkTwice is NOT a generic chatbot. It solves the **#1 problem in AI right now: hallucination and blind trust**.

The user has THREE input modes:

### Mode 1: Question → Verified Answer
User types a question. The system drafts, critiques, fact-checks against live web sources, and delivers a refined answer with sources.

**Example:** "Is intermittent fasting safe for people with diabetes?"
- Draft gives a general answer
- Critic flags: "Claim about insulin sensitivity needs medical source verification"
- Verifier: Searches PubMed/medical sources, finds nuance about Type 1 vs Type 2
- Refined answer: Corrected, sourced, with clear caveats

### Mode 2: Claim → Fact-Check
User pastes a claim or statement. The system verifies it.

**Example:** "OpenAI was founded in 2016 by Sam Altman and Elon Musk"
- Draft: Acknowledges the claim
- Critic: "Founding year needs verification. Founding team was larger than stated."
- Verifier: ✅ Elon Musk co-founded → VERIFIED. ❌ Founded in 2016 → REFUTED (2015). ⚠️ "By Sam Altman and Elon Musk" → PARTIALLY TRUE (there were other co-founders)
- Refined: Corrected statement with full context

### Mode 3: URL → Analysis
User pastes an article URL. The system reads it, identifies key claims, and fact-checks them.

**Example:** Paste a news article URL
- Draft: Summarizes the article
- Critic: Identifies 5 factual claims worth verifying
- Verifier: Checks each claim against independent sources
- Refined: "3 claims verified, 1 partially true, 1 could not be verified"

---

## Why This Matters in 2026

The agentic AI market is projected to hit $52B by 2030. Gartner predicts 40% of enterprise apps will embed AI agents by end of 2026. But the #1 blocker to adoption is trust — organizations can't deploy AI that hallucinates.

ThinkTwice demonstrates:
- **Agentic architecture** — not a chatbot loop, a real multi-step pipeline with specialized stages
- **Bounded autonomy** — the AI operates within defined steps, each with clear scope
- **Audit trail** — every reasoning step is visible and inspectable (the "glass box" pattern enterprises demand)
- **Tool use** — the agent calls external APIs (web search) to ground its reasoning in reality
- **Graceful degradation** — works with just an LLM key, gets better with search APIs

This is the pattern enterprise AI is moving toward. Building it as a portfolio project proves you understand the architecture, not just the buzzwords.

---

## Tech Stack

### Backend
- **Python 3.11+** with **FastAPI**
- **Anthropic Claude API** (claude-sonnet-4-20250514) as the reasoning engine
- **httpx** for async HTTP requests
- **Server-Sent Events (SSE)** via `sse-starlette` for real-time streaming
- **Pydantic v2** for data validation
- **BeautifulSoup4** for URL content extraction (Mode 3)
- **uvicorn** as ASGI server

### Frontend
- **React 18** (Vite + TypeScript)
- **Tailwind CSS v3**
- **Framer Motion** for animations
- **Lucide React** for icons
- **React Markdown** for rendering markdown responses

### External APIs
- **Anthropic Claude** (required) — powers all reasoning steps
- **Brave Search API** (optional, free tier: 2000 queries/month) — fact verification
- **Tavily API** (optional fallback, free tier: 1000 queries/month) — alternative search
- If neither search key provided: system uses Claude's own knowledge with a visible disclaimer

---

## Project Structure

```
thinktwice/
├── README.md
├── docker-compose.yml
├── .env.example
├── .gitignore
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                  # FastAPI app entry point, CORS, lifespan
│   ├── config.py                # Settings via pydantic-settings, env loading
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── pipeline.py          # Main orchestrator — runs all 4 steps, yields SSE events
│   │   ├── drafter.py           # Step 1: Generate initial response
│   │   ├── critic.py            # Step 2: Self-critique with structured JSON output
│   │   ├── verifier.py          # Step 3: Fact-check claims via web search
│   │   └── refiner.py           # Step 4: Produce final refined answer
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm.py               # Anthropic API wrapper (async, with retries)
│   │   ├── search.py            # Brave/Tavily/fallback search service
│   │   └── scraper.py           # URL content extractor for Mode 3
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py           # All Pydantic models
│   │
│   └── api/
│       ├── __init__.py
│       └── routes.py            # API endpoints
│
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── tsconfig.json
    ├── vite.config.ts
    ├── tailwind.config.js
    ├── index.html
    │
    ├── public/
    │   └── favicon.svg          # Brain icon
    │
    └── src/
        ├── main.tsx
        ├── App.tsx
        ├── index.css
        │
        ├── components/
        │   ├── Layout.tsx
        │   ├── InputArea.tsx        # Tabbed input: Question | Claim | URL
        │   ├── PipelineStepper.tsx   # Horizontal step progress indicator
        │   ├── StepCard.tsx          # Individual step card with expand/collapse
        │   ├── DraftStep.tsx         # Draft-specific rendering
        │   ├── CritiqueStep.tsx      # Issues with severity badges
        │   ├── VerifyStep.tsx        # Claim verdicts with source links
        │   ├── RefineStep.tsx        # Final answer with confidence
        │   ├── MetricsBar.tsx        # Summary stats bar
        │   ├── ExamplePrompts.tsx    # Curated starter prompts
        │   └── Header.tsx
        │
        ├── hooks/
        │   ├── useSSE.ts
        │   └── usePipeline.ts
        │
        ├── types/
        │   └── index.ts
        │
        └── utils/
            └── api.ts
```

---

## API Design

### `POST /api/think`

Main endpoint. Returns an SSE stream.

**Request:**
```json
{
  "input": "Is intermittent fasting safe for diabetics?",
  "mode": "question",      // "question" | "claim" | "url"
  "run_single_shot": false  // optional: also run single-shot for comparison
}
```

**SSE Event Types:**

```
event: step_start
data: {"step": "draft", "status": "running", "label": "Drafting initial response..."}

event: step_stream
data: {"step": "draft", "token": "Inter"}
// Token-by-token streaming for draft and refine steps

event: step_complete
data: {"step": "draft", "status": "complete", "duration_ms": 2340, "content": "...full text..."}

event: step_start
data: {"step": "critique", "status": "running", "label": "Self-critiquing..."}

event: step_complete
data: {
  "step": "critique",
  "status": "complete",
  "duration_ms": 1870,
  "content": {
    "issues": [
      {"description": "Claim about insulin sensitivity lacks source", "severity": "high", "quote": "..."},
      {"description": "Missing distinction between Type 1 and Type 2", "severity": "high", "quote": "..."},
      {"description": "Could mention consulting a doctor caveat", "severity": "low", "quote": "..."}
    ],
    "strengths": ["Correctly identifies time-restricted eating patterns", "Mentions autophagy benefits"],
    "claims_to_verify": [
      "Intermittent fasting improves insulin sensitivity",
      "16:8 is the most studied fasting protocol",
      "Fasting can cause dangerous hypoglycemia in diabetics"
    ],
    "confidence": 58
  }
}

event: step_start
data: {"step": "verify", "status": "running", "label": "Fact-checking 3 claims..."}

event: verify_claim
data: {
  "claim": "Intermittent fasting improves insulin sensitivity",
  "verdict": "verified",
  "source": "https://pubmed.ncbi.nlm.nih.gov/...",
  "source_title": "Effects of intermittent fasting on health... - PubMed",
  "explanation": "Multiple systematic reviews confirm improved insulin sensitivity in Type 2 diabetes patients"
}

event: verify_claim
data: {
  "claim": "16:8 is the most studied fasting protocol",
  "verdict": "unclear",
  "source": null,
  "explanation": "Several protocols are well-studied; 16:8 is popular but 'most studied' is debatable"
}

event: verify_claim
data: {
  "claim": "Fasting can cause dangerous hypoglycemia in diabetics",
  "verdict": "verified",
  "source": "https://diabetes.org/...",
  "source_title": "American Diabetes Association",
  "explanation": "ADA guidelines warn about hypoglycemia risk, especially for those on insulin or sulfonylureas"
}

event: step_complete
data: {"step": "verify", "status": "complete", "duration_ms": 4200, "verified": 2, "refuted": 0, "unclear": 1, "web_verified": true}

event: step_start
data: {"step": "refine", "status": "running", "label": "Refining with corrections..."}

event: step_stream
data: {"step": "refine", "token": "Based"}

event: step_complete
data: {
  "step": "refine",
  "status": "complete",
  "duration_ms": 2800,
  "content": "...refined answer...",
  "confidence": 87,
  "changes_made": [
    "Added Type 1 vs Type 2 distinction",
    "Softened 'most studied' claim to 'one of the most popular'",
    "Added ADA warning about hypoglycemia risk with specific medications",
    "Added recommendation to consult healthcare provider"
  ]
}

event: pipeline_complete
data: {
  "total_duration_ms": 11210,
  "confidence_before": 58,
  "confidence_after": 87,
  "issues_found": 3,
  "issues_addressed": 3,
  "claims_checked": 3,
  "claims_verified": 2,
  "claims_refuted": 0,
  "claims_unclear": 1,
  "web_verified": true
}
```

### `POST /api/think/single-shot`
Runs just a single LLM call (no pipeline) for comparison purposes.

### `GET /api/health`
Health check.

### `GET /api/examples`
Returns curated example prompts organized by mode.

---

## Backend Implementation Spec

### Pipeline Orchestrator (`core/pipeline.py`)

```python
import time
from typing import AsyncGenerator
from models.schemas import ThinkRequest, SSEEvent, PipelineMetrics
from core.drafter import Drafter
from core.critic import Critic
from core.verifier import Verifier
from core.refiner import Refiner

class ThinkTwicePipeline:
    def __init__(self, llm, search, scraper):
        self.drafter = Drafter(llm)
        self.critic = Critic(llm)
        self.verifier = Verifier(llm, search)
        self.refiner = Refiner(llm)
        self.scraper = scraper

    async def execute(self, request: ThinkRequest) -> AsyncGenerator[str, None]:
        start = time.monotonic()

        # Pre-process: if URL mode, extract content first
        user_input = request.input
        if request.mode == "url":
            extracted = await self.scraper.extract(request.input)
            user_input = f"Analyze and fact-check this article:\n\n{extracted}"

        # Step 1: Draft
        yield self._sse("step_start", {"step": "draft", "status": "running"})
        draft = await self.drafter.generate(user_input, request.mode)
        yield self._sse("step_complete", {"step": "draft", "status": "complete", "content": draft})

        # Step 2: Critique
        yield self._sse("step_start", {"step": "critique", "status": "running"})
        critique = await self.critic.analyze(user_input, draft, request.mode)
        yield self._sse("step_complete", {"step": "critique", "status": "complete", "content": critique.model_dump()})

        # Step 3: Verify
        yield self._sse("step_start", {"step": "verify", "status": "running"})
        async for event in self.verifier.check_claims(critique.claims_to_verify):
            yield self._sse("verify_claim", event.model_dump())
        verification_results = self.verifier.get_results()
        yield self._sse("step_complete", {"step": "verify", "status": "complete"})

        # Step 4: Refine
        yield self._sse("step_start", {"step": "refine", "status": "running"})
        refined = await self.refiner.produce(user_input, draft, critique, verification_results, request.mode)
        yield self._sse("step_complete", {"step": "refine", "status": "complete", "content": refined.model_dump()})

        # Final metrics
        yield self._sse("pipeline_complete", {
            "total_duration_ms": int((time.monotonic() - start) * 1000),
            "confidence_before": critique.confidence,
            "confidence_after": refined.confidence,
            # ... other metrics
        })

    def _sse(self, event: str, data: dict) -> str:
        import json
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"
```

### Drafter System Prompts (per mode)

**Question mode:**
```
You are a knowledgeable assistant. Answer the user's question thoroughly and directly.
Do NOT hedge excessively or add unnecessary caveats. Give your best, most complete answer.
This is a first draft — it will be reviewed and refined, so prioritize completeness over caution.
```

**Claim mode:**
```
You are analyzing a factual claim. Restate what the claim asserts, provide context,
and give your initial assessment of its accuracy based on your knowledge.
Be specific about which parts seem accurate and which seem questionable.
```

**URL mode:**
```
You are analyzing an article. Summarize the key points and identify the main factual claims made.
List each distinct factual claim that could be independently verified.
Focus on claims of fact, not opinions or analysis.
```

### Critic (`core/critic.py`)

Uses Claude's tool_use to enforce structured JSON output:

```python
CRITIC_TOOLS = [{
    "name": "submit_critique",
    "description": "Submit a structured critique of the draft response",
    "input_schema": {
        "type": "object",
        "properties": {
            "issues": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "description": {"type": "string"},
                        "severity": {"type": "string", "enum": ["low", "medium", "high"]},
                        "quote": {"type": "string", "description": "The specific part of the draft this refers to"}
                    },
                    "required": ["description", "severity"]
                }
            },
            "strengths": {
                "type": "array",
                "items": {"type": "string"}
            },
            "claims_to_verify": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Specific factual claims that should be checked against external sources. Extract exact claims, not vague topics."
            },
            "confidence": {
                "type": "integer",
                "minimum": 0,
                "maximum": 100,
                "description": "How confident you are in the draft's overall accuracy"
            }
        },
        "required": ["issues", "strengths", "claims_to_verify", "confidence"]
    }
}]

CRITIC_SYSTEM_PROMPT = """You are a rigorous, adversarial critic. Your job is to find EVERYTHING wrong
with the draft response before it reaches the user.

Analyze for:
- Factual errors or unsupported claims
- Logical fallacies or reasoning gaps
- Missing important nuance or context
- Overconfident statements presented as fact
- Potential hallucinations (specific numbers, dates, names that could be fabricated)
- Bias or one-sidedness

Also identify what the draft got RIGHT — the strengths that should be preserved.

Extract SPECIFIC factual claims that can be independently verified. These should be concrete,
checkable statements — not vague topics. For example:
  ✅ "The Treaty of Versailles was signed in 1919"
  ❌ "Something about World War I treaties"

Be thorough. Be harsh. The next step will verify your claims against real sources.
You MUST use the submit_critique tool to provide your analysis."""
```

### Verifier (`core/verifier.py`)

```python
class Verifier:
    async def check_claims(self, claims: list[str]) -> AsyncGenerator[VerificationResult, None]:
        for claim in claims:
            # 1. Search for the claim
            search_results = await self.search.query(claim)

            if search_results:
                # 2. Ask Claude to evaluate claim against search results
                verdict = await self.llm.generate(
                    system=VERIFY_SYSTEM_PROMPT,
                    user=f"Claim: {claim}\n\nSearch Results:\n{self._format_results(search_results)}"
                )
                yield VerificationResult(
                    claim=claim,
                    verdict=verdict.verdict,  # "verified" | "refuted" | "unclear"
                    source=search_results[0].url,
                    source_title=search_results[0].title,
                    explanation=verdict.explanation,
                    web_verified=True
                )
            else:
                # Fallback: use Claude's knowledge
                verdict = await self.llm.generate(
                    system=VERIFY_FALLBACK_PROMPT,
                    user=f"Claim: {claim}"
                )
                yield VerificationResult(
                    claim=claim,
                    verdict=verdict.verdict,
                    source=None,
                    source_title=None,
                    explanation=verdict.explanation + " (verified against AI knowledge only, not web sources)",
                    web_verified=False
                )
```

### Search Service Priority (`services/search.py`)

```python
class SearchService:
    """Tries Brave → Tavily → Claude fallback"""

    def __init__(self, brave_key: str | None, tavily_key: str | None):
        self.brave_key = brave_key
        self.tavily_key = tavily_key

    async def query(self, q: str, num_results: int = 3) -> list[SearchResult] | None:
        if self.brave_key:
            return await self._brave_search(q, num_results)
        if self.tavily_key:
            return await self._tavily_search(q, num_results)
        return None  # triggers Claude-knowledge fallback

    async def _brave_search(self, q: str, n: int) -> list[SearchResult]:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
                params={"q": q, "count": n},
                headers={"X-Subscription-Token": self.brave_key}
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                SearchResult(title=r["title"], url=r["url"], snippet=r["description"])
                for r in data.get("web", {}).get("results", [])[:n]
            ]

    async def _tavily_search(self, q: str, n: int) -> list[SearchResult]:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.tavily.com/search",
                json={"query": q, "max_results": n, "api_key": self.tavily_key}
            )
            resp.raise_for_status()
            data = resp.json()
            return [
                SearchResult(title=r["title"], url=r["url"], snippet=r["content"])
                for r in data.get("results", [])[:n]
            ]
```

### Pydantic Schemas (`models/schemas.py`)

```python
from pydantic import BaseModel, Field
from typing import Literal
from enum import Enum

class InputMode(str, Enum):
    QUESTION = "question"
    CLAIM = "claim"
    URL = "url"

class ThinkRequest(BaseModel):
    input: str = Field(..., min_length=1, max_length=5000)
    mode: InputMode = InputMode.QUESTION
    run_single_shot: bool = False

class CritiqueIssue(BaseModel):
    description: str
    severity: Literal["low", "medium", "high"]
    quote: str | None = None

class Critique(BaseModel):
    issues: list[CritiqueIssue]
    strengths: list[str]
    claims_to_verify: list[str]
    confidence: int = Field(ge=0, le=100)

class VerificationResult(BaseModel):
    claim: str
    verdict: Literal["verified", "refuted", "unclear"]
    source: str | None
    source_title: str | None
    explanation: str
    web_verified: bool

class RefinedResponse(BaseModel):
    content: str
    confidence: int = Field(ge=0, le=100)
    changes_made: list[str]

class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
```

---

## Frontend Design Spec

### Design Direction: Dark Mission Control

Think: you're watching an AI investigate a claim in real time. Each step reveals more. Dark, technical, premium — like a Bloomberg terminal meets a research dashboard.

### Color System
```css
:root {
  --bg-base: #09090B;           /* zinc-950 */
  --bg-card: #18181B;           /* zinc-900 */
  --bg-elevated: #27272A;       /* zinc-800 */
  --border: #3F3F46;            /* zinc-700 */

  --text-primary: #FAFAFA;      /* zinc-50 */
  --text-secondary: #A1A1AA;    /* zinc-400 */
  --text-muted: #71717A;        /* zinc-500 */

  /* Step colors — each pipeline step has its own identity */
  --draft: #3B82F6;             /* blue-500 */
  --critique: #F59E0B;          /* amber-500 */
  --verify: #8B5CF6;            /* violet-500 */
  --refine: #10B981;            /* emerald-500 */

  /* Verdict colors */
  --verified: #10B981;          /* emerald */
  --refuted: #EF4444;           /* red */
  --unclear: #F59E0B;           /* amber */
}
```

### Typography
- **Headings / Monospace**: `"JetBrains Mono", "Fira Code", monospace` — via Google Fonts
- **Body**: `"DM Sans", system-ui, sans-serif` — via Google Fonts
- **Step labels**: All caps, letter-spacing: 0.1em, font-weight: 600

### Key UI Behaviors

**1. Tabbed Input Area**
Three tabs at the top of the input: `Question` | `Fact-Check` | `Analyze URL`
- Question tab: textarea with placeholder "What would you like me to think twice about?"
- Fact-Check tab: textarea with placeholder "Paste a claim to verify..."
- URL tab: URL input field with placeholder "https://example.com/article"

**2. Pipeline Stepper**
Horizontal bar showing: `Draft → Critique → Verify → Refine`
- Inactive steps: gray, muted
- Active step: glowing pulse animation in step color, label shows "Running..."
- Complete step: solid color, checkmark icon, shows duration (e.g., "2.3s")

**3. Step Cards**
Each step renders as an expandable card:
- Header: Step name, duration, status icon
- Body: Step-specific content (see below)
- Default: all expanded while running, collapsible after pipeline completes

**Draft card:** Rendered markdown text

**Critique card:**
- Issues listed with severity badges (🔴 HIGH / 🟡 MEDIUM / 🟢 LOW)
- Strengths listed with ✓ marks
- Claims queued for verification listed with 🔍 icon
- Confidence bar: colored bar showing percentage (e.g., "Confidence: ████████░░ 58%")

**Verify card:**
- Each claim appears as a row:
  - ✅ Claim text → VERIFIED (source link) — explanation
  - ❌ Claim text → REFUTED (source link) — explanation
  - ⚠️ Claim text → UNCLEAR — explanation
- If web_verified=false, show gray banner: "Verified against AI knowledge only. Add a search API key for web verification."

**Refine card:**
- Rendered markdown final answer
- "Changes made" section listing what was fixed
- Confidence bar: shows increase with delta (e.g., "58% → 87% (+29)")

**4. Metrics Bar (bottom)**
Horizontal bar after pipeline completes:
```
⏱ 11.2s  |  📊 58% → 87%  |  🔍 3 claims checked  |  ✅ 2 verified  |  ❌ 0 refuted  |  ⚠️ 1 unclear
```

**5. Animations (Framer Motion)**
- Steps slide in from bottom with stagger (0.1s between steps)
- Verification results animate in one-by-one as they stream
- Confidence bars animate from 0 to target value
- Active step has a subtle breathing glow effect
- Pipeline stepper connections animate as each step completes

### Example Prompts (Curated, organized by mode)

**Questions:**
- "Is intermittent fasting safe for people with diabetes?"
- "Explain how mRNA vaccines work. Are there long-term risks?"
- "What causes the northern lights and how far south can they be seen?"

**Claims to Fact-Check:**
- "Humans only use 10% of their brain"
- "The Great Wall of China is visible from space"
- "Coffee stunts your growth"

**URLs:** (show as empty — user provides their own)

---

## Environment Variables

```env
# REQUIRED — powers all reasoning steps
ANTHROPIC_API_KEY=sk-ant-...

# OPTIONAL — enables real web-based fact checking
# Get free key at: https://brave.com/search/api/
BRAVE_SEARCH_API_KEY=

# OPTIONAL — alternative to Brave
# Get free key at: https://tavily.com
TAVILY_API_KEY=

# SERVER
HOST=0.0.0.0
PORT=8000
FRONTEND_URL=http://localhost:5173
```

---

## Implementation Checklist

### Phase 1: Core (MUST complete)
- [ ] Backend: FastAPI skeleton with CORS, health check, lifespan
- [ ] Backend: Config loading from env
- [ ] Backend: LLM service (Anthropic async wrapper with error handling)
- [ ] Backend: Search service (Brave → Tavily → None fallback chain)
- [ ] Backend: Drafter module (3 mode-specific system prompts)
- [ ] Backend: Critic module (tool_use for structured JSON, mode-aware)
- [ ] Backend: Verifier module (search + evaluate per claim, async generator)
- [ ] Backend: Refiner module (full context synthesis)
- [ ] Backend: Pipeline orchestrator with SSE streaming
- [ ] Backend: `/api/think` SSE endpoint
- [ ] Backend: `/api/examples` endpoint
- [ ] Backend: URL scraper service for Mode 3
- [ ] Frontend: Vite + React + TypeScript + Tailwind setup
- [ ] Frontend: Dark theme with design system (colors, fonts)
- [ ] Frontend: Layout shell and Header
- [ ] Frontend: Tabbed InputArea (Question | Claim | URL)
- [ ] Frontend: useSSE hook for EventSource streaming
- [ ] Frontend: usePipeline hook for state management
- [ ] Frontend: PipelineStepper (horizontal progress)
- [ ] Frontend: StepCard with expand/collapse
- [ ] Frontend: DraftStep renderer (markdown)
- [ ] Frontend: CritiqueStep renderer (issues, strengths, claims, confidence)
- [ ] Frontend: VerifyStep renderer (verdicts with sources)
- [ ] Frontend: RefineStep renderer (final answer, changes, confidence delta)
- [ ] Frontend: MetricsBar
- [ ] Frontend: ExamplePrompts
- [ ] Frontend: Loading / streaming states
- [ ] Frontend: Error handling (API down, invalid URL, etc.)
- [ ] Docker: backend Dockerfile
- [ ] Docker: frontend Dockerfile
- [ ] Docker: docker-compose.yml
- [ ] .env.example with comments
- [ ] README.md with setup instructions, screenshots section, tech stack

### Phase 2: Polish
- [ ] Frontend: Framer Motion animations (step slide-in, confidence bar, glow)
- [ ] Frontend: Mobile responsive layout (vertical stepper, stacked cards)
- [ ] Frontend: Keyboard shortcuts (Enter to submit, Escape to cancel)
- [ ] Backend: Token-by-token streaming for draft and refine steps
- [ ] Backend: Request timeout handling
- [ ] Backend: Rate limiting (basic, per-IP)
- [ ] Frontend: "No search API" banner when web_verified=false

### Phase 3: Stretch
- [ ] Comparison view: single-shot vs ThinkTwice side-by-side
- [ ] Export reasoning trail as markdown
- [ ] History (localStorage)
- [ ] PWA support

---

## Quality Standards

1. **TypeScript strict mode** — no `any` types
2. **Python type hints everywhere** — mypy compatible
3. **Error boundaries** — frontend catches render errors gracefully
4. **Retry logic** — LLM calls retry once on timeout
5. **Clean git history** — atomic commits with conventional commit messages
6. **No hardcoded values** — everything configurable via env
7. **Production-ready Dockerfiles** — multi-stage builds, non-root user
8. **README that actually helps** — one-command setup, clear prerequisites

---

## Design Decisions Log

| Decision | Rationale |
|---|---|
| SSE over WebSockets | Unidirectional (server→client), simpler, perfect for streaming pipeline events |
| Single model (Sonnet) for all steps | Simpler, faster, cheaper. Each step is differentiated by prompt, not model |
| tool_use for critic output | Forces structured JSON — no regex parsing of free-form text |
| Brave Search as primary | Free tier (2000/mo), fast, good quality. Tavily as fallback |
| Three input modes | Makes the project concrete and useful, not just a demo |
| No database | Stateless demo. Each query is independent. Optional localStorage for history |
| Confidence scores | Gives a tangible metric for "how much did the pipeline help?" |
| BeautifulSoup for URL scraping | Lightweight, no headless browser needed for most articles |
