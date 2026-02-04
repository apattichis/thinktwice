"""URL content scraper service."""

import re

import httpx
from bs4 import BeautifulSoup


class ScraperService:
    """Extracts readable content from URLs using BeautifulSoup."""

    def __init__(self, timeout: float = 30.0, max_content_length: int = 10000):
        self.timeout = timeout
        self.max_content_length = max_content_length
        self._client: httpx.AsyncClient | None = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Lazy-initialize HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
            )
        return self._client

    async def extract(self, url: str) -> str:
        """
        Extract readable text content from a URL.

        Args:
            url: The URL to scrape

        Returns:
            Extracted text content, truncated to max_content_length

        Raises:
            ValueError: If URL is invalid or content cannot be extracted
        """
        # Validate URL
        if not url.startswith(("http://", "https://")):
            raise ValueError("Invalid URL: must start with http:// or https://")

        try:
            response = await self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch URL: {e}")

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type.lower():
            raise ValueError(f"URL does not return HTML content: {content_type}")

        # Parse HTML
        soup = BeautifulSoup(response.text, "lxml")

        # Remove script, style, nav, footer, header elements
        for element in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            element.decompose()

        # Try to find article content
        article = soup.find("article")
        if article:
            text = article.get_text(separator="\n", strip=True)
        else:
            # Fall back to main or body
            main = soup.find("main") or soup.find("body")
            if main:
                text = main.get_text(separator="\n", strip=True)
            else:
                text = soup.get_text(separator="\n", strip=True)

        # Clean up whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        # Extract title
        title = ""
        title_tag = soup.find("title")
        if title_tag:
            title = title_tag.get_text(strip=True)

        # Format output
        result = ""
        if title:
            result = f"Title: {title}\n\n"
        result += text

        # Truncate if needed
        if len(result) > self.max_content_length:
            result = result[: self.max_content_length] + "\n\n[Content truncated...]"

        return result

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None
