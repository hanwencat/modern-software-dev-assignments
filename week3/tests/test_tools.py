"""Integration tests for MCP tool functions.

These test the tool handler functions directly (not via MCP protocol),
mocking the FinnhubClient layer underneath.
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from week3.server.finnhub_client import FinnhubAPIError


@pytest.mark.asyncio
async def test_get_stock_quote_tool_success():
    """Tool should return formatted quote string on success."""
    mock_client = AsyncMock()
    mock_client.get_quote.return_value = {
        "current_price": 150.25,
        "change": 2.50,
        "percent_change": 1.69,
        "high": 151.00,
        "low": 148.50,
        "open": 149.00,
        "previous_close": 147.75,
        "timestamp": 1700000000,
    }

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import get_stock_quote

        result = await get_stock_quote("AAPL")
        assert "150.25" in result
        assert "AAPL" in result


@pytest.mark.asyncio
async def test_get_stock_quote_tool_error():
    """Tool should return error message string, not raise."""
    mock_client = AsyncMock()
    mock_client.get_quote.side_effect = FinnhubAPIError("No data found for symbol: INVALID")

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import get_stock_quote

        result = await get_stock_quote("INVALID")
        assert "error" in result.lower() or "Error" in result


@pytest.mark.asyncio
async def test_get_company_profile_tool_success():
    """Tool should return formatted profile string on success."""
    mock_client = AsyncMock()
    mock_client.get_company_profile.return_value = {
        "name": "Apple Inc",
        "ticker": "AAPL",
        "country": "US",
        "currency": "USD",
        "exchange": "NASDAQ",
        "industry": "Technology",
        "market_capitalization": 2500000,
        "ipo": "1980-12-12",
        "logo": "https://example.com/logo.png",
        "phone": "14089961010",
        "weburl": "https://www.apple.com/",
    }

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import get_company_profile

        result = await get_company_profile("AAPL")
        assert "Apple Inc" in result
        assert "Technology" in result


@pytest.mark.asyncio
async def test_get_company_profile_tool_error():
    """Tool should handle errors gracefully."""
    mock_client = AsyncMock()
    mock_client.get_company_profile.side_effect = FinnhubAPIError("No data found")

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import get_company_profile

        result = await get_company_profile("INVALID")
        assert "error" in result.lower() or "Error" in result


@pytest.mark.asyncio
async def test_get_company_news_tool_success():
    """Tool should return formatted news list string on success."""
    mock_client = AsyncMock()
    mock_client.get_company_news.return_value = [
        {
            "headline": "Apple Reports Record Revenue",
            "summary": "Apple Inc reported record quarterly revenue...",
            "source": "Reuters",
            "url": "https://example.com/article",
            "datetime": 1700000000,
        },
    ]

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import get_company_news

        result = await get_company_news("AAPL", "2024-01-01", "2024-01-31")
        assert "Apple Reports Record Revenue" in result
        assert "Reuters" in result


@pytest.mark.asyncio
async def test_get_company_news_tool_error():
    """Tool should handle errors gracefully."""
    mock_client = AsyncMock()
    mock_client.get_company_news.side_effect = FinnhubAPIError("No news found")

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import get_company_news

        result = await get_company_news("AAPL", "2024-01-01", "2024-01-31")
        assert "error" in result.lower() or "Error" in result


@pytest.mark.asyncio
async def test_search_symbol_tool_success():
    """Tool should return formatted search results string on success."""
    mock_client = AsyncMock()
    mock_client.search_symbol.return_value = [
        {"symbol": "AAPL", "description": "APPLE INC", "type": "Common Stock"},
        {"symbol": "APLE", "description": "APPLE HOSPITALITY REIT INC", "type": "Common Stock"},
    ]

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import search_symbol

        result = await search_symbol("Apple")
        assert "AAPL" in result
        assert "APPLE INC" in result


@pytest.mark.asyncio
async def test_search_symbol_tool_error():
    """Tool should handle errors gracefully."""
    mock_client = AsyncMock()
    mock_client.search_symbol.side_effect = FinnhubAPIError("No results found")

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import search_symbol

        result = await search_symbol("xyznonexistent")
        assert "error" in result.lower() or "Error" in result


@pytest.mark.asyncio
async def test_get_stock_quote_tool_empty_symbol():
    """Tool should handle empty symbol input."""
    mock_client = AsyncMock()
    mock_client.get_quote.side_effect = FinnhubAPIError("Symbol cannot be empty")

    with patch("week3.server.main._get_client", return_value=mock_client):
        from week3.server.main import get_stock_quote

        result = await get_stock_quote("")
        assert "error" in result.lower() or "Error" in result
