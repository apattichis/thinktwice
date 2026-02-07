"""Drafter module - generates initial response."""

from services.llm import LLMService


DRAFTER_PROMPT = """You are a knowledgeable assistant. Answer the user's question thoroughly and directly.
Do NOT hedge excessively or add unnecessary caveats. Give your best, most complete answer.
This is a first draft — it will be reviewed and refined, so prioritize completeness over caution."""


class Drafter:
    """Generates initial draft response."""

    def __init__(self, llm: LLMService):
        self.llm = llm

    async def generate(self, user_input: str) -> str:
        """Generate initial draft response."""
        return await self.llm.generate(system=DRAFTER_PROMPT, user=user_input)

    async def stream(self, user_input: str):
        """Stream draft response token by token."""
        async for token in self.llm.stream(system=DRAFTER_PROMPT, user=user_input):
            yield token
