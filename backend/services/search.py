"""Search service with Brave -> Tavily -> None fallback."""

import httpx

from models.schemas import SearchResult


class SearchService:
    """Web search service with fallback chain: Brave -> Tavily -> None."""

    def __init__(
        self,
        brave_key: str | None = None,
        tavily_key: str | None = None,
    ):
        self.brave_key = brave_key
        self.tavily_key = tavily_key
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-initialize HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client

    @property
    def has_search(self) -> bool:
        """Check if any search API is available."""
        return bool(self.brave_key or self.tavily_key)

    @property
    def provider(self) -> str | None:
        """Get the current search provider name."""
        if self.brave_key:
            return "brave"
        if self.tavily_key:
            return "tavily"
        return None

    async def query(self, q: str, num_results: int = 3) -> list[SearchResult] | None:
        """
        Search for a query, returning results or None if no search API available.

        Tries Brave first, then Tavily, then returns None for Claude fallback.
        """
        if self.brave_key:
            try:
                return await self._brave_search(q, num_results)
            except Exception:
                # Fall through to Tavily
                pass

        if self.tavily_key:
            try:
                return await self._tavily_search(q, num_results)
            except Exception:
                pass

        return None

    async def _brave_search(self, q: str, n: int) -> list[SearchResult]:
        """Search using Brave Search API."""
        resp = await self.client.get(
            "https://api.search.brave.com/res/v1/web/search",
            params={"q": q, "count": n},
            headers={"X-Subscription-Token": self.brave_key},
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("web", {}).get("results", [])[:n]:
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("description", ""),
                )
            )
        return results

    async def _tavily_search(self, q: str, n: int) -> list[SearchResult]:
        """Search using Tavily API."""
        resp = await self.client.post(
            "https://api.tavily.com/search",
            json={
                "query": q,
                "max_results": n,
                "api_key": self.tavily_key,
            },
        )
        resp.raise_for_status()
        data = resp.json()

        results = []
        for r in data.get("results", [])[:n]:
            results.append(
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("content", ""),
                )
            )
        return results

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
