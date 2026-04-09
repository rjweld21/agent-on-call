"""Tests for web search and fetch tools."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from agent_on_call.web_tools import (
    WebSearchTool,
    html_to_text,
    truncate_content,
)


class TestHtmlToText:
    """Test HTML-to-text extraction."""

    def test_strips_script_and_style_tags(self):
        html = "<html><head><style>body{}</style></head><body><script>alert(1)</script><p>Hello</p></body></html>"
        text = html_to_text(html)
        assert "alert" not in text
        assert "body{}" not in text
        assert "Hello" in text

    def test_strips_all_html_tags(self):
        html = "<div><h1>Title</h1><p>Paragraph with <b>bold</b> text.</p></div>"
        text = html_to_text(html)
        assert "<" not in text
        assert "Title" in text
        assert "bold" in text

    def test_decodes_html_entities(self):
        html = "<p>A &amp; B &lt; C &gt; D &quot;E&quot;</p>"
        text = html_to_text(html)
        assert "A & B" in text
        assert "< C >" in text

    def test_collapses_whitespace(self):
        html = "<p>  too   many    spaces  </p><p>  and   more  </p>"
        text = html_to_text(html)
        # Should not have runs of 3+ spaces
        assert "   " not in text

    def test_handles_empty_string(self):
        assert html_to_text("") == ""

    def test_handles_plain_text(self):
        text = html_to_text("Just plain text, no HTML.")
        assert "Just plain text" in text


class TestTruncateContent:
    """Test content truncation."""

    def test_no_truncation_when_under_limit(self):
        content = "Short content"
        result = truncate_content(content, max_bytes=1000)
        assert result == content

    def test_truncates_with_notice_when_over_limit(self):
        content = "x" * 2000
        result = truncate_content(content, max_bytes=500)
        assert len(result.encode()) <= 600  # some overhead for truncation notice
        assert "[truncated" in result.lower()

    def test_preserves_beginning_of_content(self):
        content = "IMPORTANT_START " + "x" * 2000
        result = truncate_content(content, max_bytes=500)
        assert "IMPORTANT_START" in result


class TestWebSearchTool:
    """Test web_search function_tool."""

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        tool = WebSearchTool()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Python Tutorial",
                    "url": "https://python.org",
                    "content": "Learn Python programming",
                },
                {
                    "title": "Python Docs",
                    "url": "https://docs.python.org",
                    "content": "Official documentation",
                },
            ]
        }

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
            with patch("agent_on_call.web_tools.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client_cls.return_value = mock_client

                result = await tool.search("python tutorial")

        assert "Python Tutorial" in result
        assert "https://python.org" in result

    @pytest.mark.asyncio
    async def test_search_no_api_key(self):
        tool = WebSearchTool()
        with patch.dict("os.environ", {}, clear=True):
            result = await tool.search("test query")
        assert "error" in result.lower() or "api key" in result.lower()

    @pytest.mark.asyncio
    async def test_search_rate_limited(self):
        tool = WebSearchTool()
        tool._search_count = 5  # At the limit

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
            result = await tool.search("test query")
        assert "rate limit" in result.lower() or "limit" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self):
        tool = WebSearchTool()

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
            with patch("agent_on_call.web_tools.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
                mock_client_cls.return_value = mock_client

                result = await tool.search("test query")

        assert "error" in result.lower() or "timeout" in result.lower()

    @pytest.mark.asyncio
    async def test_search_handles_non_200(self):
        tool = WebSearchTool()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 429
        mock_response.text = "Rate limited"

        with patch.dict("os.environ", {"TAVILY_API_KEY": "test-key"}):
            with patch("agent_on_call.web_tools.httpx.AsyncClient") as mock_client_cls:
                mock_client = AsyncMock()
                mock_client.__aenter__ = AsyncMock(return_value=mock_client)
                mock_client.__aexit__ = AsyncMock(return_value=False)
                mock_client.post = AsyncMock(return_value=mock_response)
                mock_client_cls.return_value = mock_client

                result = await tool.search("test query")

        assert "error" in result.lower()


class TestWebFetchTool:
    """Test web_fetch function_tool."""

    @pytest.mark.asyncio
    async def test_fetch_returns_text(self):
        tool = WebSearchTool()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = "<html><body><p>Hello World</p></body></html>"
        mock_response.headers = {"content-type": "text/html"}

        with patch("agent_on_call.web_tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await tool.fetch("https://example.com")

        assert "Hello World" in result
        assert "<p>" not in result  # HTML tags stripped

    @pytest.mark.asyncio
    async def test_fetch_invalid_url(self):
        tool = WebSearchTool()
        result = await tool.fetch("not-a-url")
        assert "error" in result.lower() or "invalid" in result.lower()

    @pytest.mark.asyncio
    async def test_fetch_rate_limited(self):
        tool = WebSearchTool()
        tool._fetch_count = 10  # At the limit

        result = await tool.fetch("https://example.com")
        assert "rate limit" in result.lower() or "limit" in result.lower()

    @pytest.mark.asyncio
    async def test_fetch_handles_timeout(self):
        tool = WebSearchTool()

        with patch("agent_on_call.web_tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client_cls.return_value = mock_client

            result = await tool.fetch("https://example.com")

        assert "error" in result.lower() or "timeout" in result.lower()

    @pytest.mark.asyncio
    async def test_fetch_handles_404(self):
        tool = WebSearchTool()
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 404
        mock_response.text = "Not Found"

        with patch("agent_on_call.web_tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await tool.fetch("https://example.com/missing")

        assert "error" in result.lower() or "404" in result

    @pytest.mark.asyncio
    async def test_fetch_truncates_large_content(self):
        tool = WebSearchTool()
        large_body = "<html><body>" + "<p>A</p>" * 5000 + "</body></html>"
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.text = large_body
        mock_response.headers = {"content-type": "text/html"}

        with patch("agent_on_call.web_tools.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            result = await tool.fetch("https://example.com")

        assert len(result) <= 12000  # ~10KB + truncation notice
        assert "[truncated" in result.lower()
