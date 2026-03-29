"""Web search and fetch tools for the agent."""

import html
import logging
import os
import re

import httpx

logger = logging.getLogger(__name__)

# Rate limits per session
MAX_SEARCHES_PER_SESSION = 5
MAX_FETCHES_PER_SESSION = 10
FETCH_TIMEOUT_SECONDS = 10
MAX_CONTENT_BYTES = 10_000  # ~10KB for LLM context budget


def html_to_text(raw_html: str) -> str:
    """Convert HTML to plain text by stripping tags and decoding entities.

    Removes script/style blocks, strips all HTML tags, decodes HTML entities,
    and collapses excessive whitespace.
    """
    if not raw_html:
        return ""

    text = raw_html

    # Remove script and style blocks (including content)
    text = re.sub(r"<script[^>]*>.*?</script>", " ", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", " ", text, flags=re.DOTALL | re.IGNORECASE)

    # Replace block-level tags with newlines for readability
    text = re.sub(r"<(?:br|p|div|h[1-6]|li|tr)[^>]*>", "\n", text, flags=re.IGNORECASE)

    # Strip all remaining HTML tags
    text = re.sub(r"<[^>]+>", " ", text)

    # Decode HTML entities
    text = html.unescape(text)

    # Collapse multiple whitespace (but preserve single newlines)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n[ \t]+", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def truncate_content(content: str, max_bytes: int = MAX_CONTENT_BYTES) -> str:
    """Truncate content to fit within a byte limit, adding a notice if truncated."""
    encoded = content.encode("utf-8", errors="replace")
    if len(encoded) <= max_bytes:
        return content

    # Truncate to max_bytes and decode safely
    truncated = encoded[:max_bytes].decode("utf-8", errors="ignore")
    return truncated + f"\n\n[Truncated — original was {len(encoded):,} bytes, showing first {max_bytes:,} bytes]"


class WebSearchTool:
    """Provides web search and fetch capabilities for the agent.

    Manages per-session rate limiting and provides search via Tavily API
    and page fetching via httpx with HTML-to-text extraction.
    """

    def __init__(self) -> None:
        self._search_count = 0
        self._fetch_count = 0

    async def search(self, query: str) -> str:
        """Search the web using Tavily API.

        Args:
            query: The search query string.

        Returns:
            Formatted search results or an error message.
        """
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            return "Error: TAVILY_API_KEY not configured. Add it to your environment to enable web search."

        if self._search_count >= MAX_SEARCHES_PER_SESSION:
            return (
                f"Error: Search rate limit reached ({MAX_SEARCHES_PER_SESSION} searches per session). "
                "Please use web_fetch on specific URLs instead."
            )

        self._search_count += 1
        logger.info("Web search [%d/%d]: %s", self._search_count, MAX_SEARCHES_PER_SESSION, query[:100])

        try:
            async with httpx.AsyncClient(timeout=FETCH_TIMEOUT_SECONDS) as client:
                resp = await client.post(
                    "https://api.tavily.com/search",
                    json={
                        "api_key": api_key,
                        "query": query,
                        "max_results": 5,
                        "include_answer": False,
                    },
                )

            if resp.status_code != 200:
                return f"Error: Search API returned HTTP {resp.status_code}. {resp.text[:200]}"

            data = resp.json()
            results = data.get("results", [])
            if not results:
                return "No results found for your query."

            lines = []
            for i, r in enumerate(results[:5], 1):
                title = r.get("title", "Untitled")
                url = r.get("url", "")
                snippet = r.get("content", "")[:200]
                lines.append(f"{i}. **{title}**\n   URL: {url}\n   {snippet}")

            return "\n\n".join(lines)

        except httpx.TimeoutException:
            return "Error: Search request timed out. Try again or use a more specific query."
        except httpx.HTTPError as e:
            return f"Error: Search request failed — {e}"
        except Exception as e:
            logger.error("Unexpected error in web search: %s", e)
            return f"Error: Search failed — {e}"

    async def fetch(self, url: str) -> str:
        """Fetch a web page and return its text content.

        Args:
            url: The URL to fetch.

        Returns:
            Extracted text content or an error message.
        """
        # Basic URL validation
        if not url or not url.startswith(("http://", "https://")):
            return "Error: Invalid URL. Please provide a full URL starting with http:// or https://."

        if self._fetch_count >= MAX_FETCHES_PER_SESSION:
            return (
                f"Error: Fetch rate limit reached ({MAX_FETCHES_PER_SESSION} fetches per session). "
                "Summarize what you have so far."
            )

        self._fetch_count += 1
        logger.info("Web fetch [%d/%d]: %s", self._fetch_count, MAX_FETCHES_PER_SESSION, url[:100])

        try:
            async with httpx.AsyncClient(
                timeout=FETCH_TIMEOUT_SECONDS,
                follow_redirects=True,
                headers={"User-Agent": "AgentOnCall/1.0 (bot; +https://github.com/rjweld21/agent-on-call)"},
            ) as client:
                resp = await client.get(url)

            if resp.status_code != 200:
                return f"Error: HTTP {resp.status_code} fetching {url}."

            content_type = resp.headers.get("content-type", "")
            raw_text = resp.text

            # Extract text from HTML
            if "html" in content_type.lower() or raw_text.strip().startswith("<"):
                text = html_to_text(raw_text)
            else:
                text = raw_text

            return truncate_content(text, MAX_CONTENT_BYTES)

        except httpx.TimeoutException:
            return f"Error: Request to {url} timed out after {FETCH_TIMEOUT_SECONDS}s."
        except httpx.HTTPError as e:
            return f"Error: Failed to fetch {url} — {e}"
        except Exception as e:
            logger.error("Unexpected error fetching %s: %s", url, e)
            return f"Error: Failed to fetch URL — {e}"
