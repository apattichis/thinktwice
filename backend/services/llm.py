"""LLM service wrapping Anthropic API."""

import anthropic
from anthropic import AsyncAnthropic


class LLMService:
    """Async wrapper for Anthropic Claude API with error handling."""

    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-5-haiku-20241022",
        max_tokens: int = 4096,
        timeout: float = 60.0,
    ):
        self.model = model
        self.max_tokens = max_tokens
        self.timeout = timeout
        self.client = AsyncAnthropic(api_key=api_key, timeout=timeout)

    async def generate(
        self,
        system: str,
        user: str,
        max_tokens: int | None = None,
    ) -> str:
        """Generate a response from the LLM."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text
        except anthropic.APITimeoutError:
            # Retry once on timeout
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
            return response.content[0].text

    async def generate_with_tools(
        self,
        system: str,
        user: str,
        tools: list[dict],
        tool_choice: dict | None = None,
        max_tokens: int | None = None,
    ) -> dict | None:
        """Generate a response using tool calling for structured output."""
        try:
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=tools,
                tool_choice=tool_choice or {"type": "auto"},
            )

            # Extract tool use from response
            for block in response.content:
                if block.type == "tool_use":
                    return block.input
            return None

        except anthropic.APITimeoutError:
            # Retry once on timeout
            response = await self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or self.max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
                tools=tools,
                tool_choice=tool_choice or {"type": "auto"},
            )
            for block in response.content:
                if block.type == "tool_use":
                    return block.input
            return None

    async def stream(
        self,
        system: str,
        user: str,
        max_tokens: int | None = None,
    ):
        """Stream a response token by token."""
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens or self.max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def close(self) -> None:
        """Close the client connection."""
        await self.client.close()
