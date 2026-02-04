"""Drafter module - generates initial response."""

from services.llm import LLMService
from models.schemas import InputMode


# System prompts for each mode
DRAFTER_PROMPTS = {
    InputMode.QUESTION: """You are a knowledgeable assistant. Answer the user's question thoroughly and directly.
Do NOT hedge excessively or add unnecessary caveats. Give your best, most complete answer.
This is a first draft — it will be reviewed and refined, so prioritize completeness over caution.""",
    InputMode.CLAIM: """You are analyzing a factual claim. Restate what the claim asserts, provide context,
and give your initial assessment of its accuracy based on your knowledge.
Be specific about which parts seem accurate and which seem questionable.""",
    InputMode.URL: """You are analyzing an article. Summarize the key points and identify the main factual claims made.
List each distinct factual claim that could be independently verified.
Focus on claims of fact, not opinions or analysis.""",
}


class Drafter:
    """Generates initial draft response based on input mode."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def generate(self, user_input: str, mode: InputMode) -> str:
        """Generate initial draft response."""
        system_prompt = DRAFTER_PROMPTS.get(mode, DRAFTER_PROMPTS[InputMode.QUESTION])
        return await self.llm.generate(system=system_prompt, user=user_input)

    async def stream(self, user_input: str, mode: InputMode):
        """Stream draft response token by token."""
        system_prompt = DRAFTER_PROMPTS.get(mode, DRAFTER_PROMPTS[InputMode.QUESTION])
        async for token in self.llm.stream(system=system_prompt, user=user_input):
            yield token
