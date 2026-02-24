import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from week3.server.finnhub_client import FinnhubClient, FinnhubAPIError
from week3.tests.conftest import (
    SAMPLE_QUOTE_RESPONSE,
    SAMPLE_PROFILE_RESPONSE,
    SAMPLE_NEWS_RESPONSE,
    SAMPLE_SEARCH_RESPONSE,
)


def _mock_response(json_data, status_code=200):
    """Create a mock httpx.Response."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    resp.json.return_value = json_data
    resp.is_success = status_code < 400
    resp.raise_for_status = MagicMock()
    if status_code >= 400:
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            message=f"HTTP {status_code}",
            request=MagicMock(),
            response=resp,
        )
    return resp


# --- get_quote tests ---


@pytest.mark.asyncio
async def test_get_quote_success(finnhub_client):
    """Successful quote request returns parsed price data."""
    with patch.object(
        finnhub_client, "_request", new_callable=AsyncMock, return_value=SAMPLE_QUOTE_RESPONSE
    ):
        result = await finnhub_client.get_quote("AAPL")
        assert result["current_price"] == 150.25
        assert result["change"] == 2.50
        assert result["percent_change"] == 1.69
        assert result["high"] == 151.00
        assert result["low"] == 148.50
        assert result["open"] == 149.00
        assert result["previous_close"] == 147.75


@pytest.mark.asyncio
async def test_get_quote_empty_response(finnhub_client):
    """Quote with all-zero values (invalid symbol) should raise FinnhubAPIError."""
    empty_quote = {"c": 0, "d": None, "dp": None, "h": 0, "l": 0, "o": 0, "pc": 0, "t": 0}
    with patch.object(
        finnhub_client, "_request", new_callable=AsyncMock, return_value=empty_quote
    ):
        with pytest.raises(FinnhubAPIError, match="No data found"):
            await finnhub_client.get_quote("INVALID")


@pytest.mark.asyncio
async def test_get_quote_http_error(finnhub_client):
    """HTTP error should be wrapped in FinnhubAPIError."""
    with patch.object(
        finnhub_client,
        "_request",
        new_callable=AsyncMock,
        side_effect=FinnhubAPIError("HTTP 500: Internal Server Error", status_code=500),
    ):
        with pytest.raises(FinnhubAPIError):
            await finnhub_client.get_quote("AAPL")


@pytest.mark.asyncio
async def test_get_quote_timeout(finnhub_client):
    """Timeout should be wrapped in FinnhubAPIError."""
    with patch.object(
        finnhub_client,
        "_request",
        new_callable=AsyncMock,
        side_effect=FinnhubAPIError("Request timed out"),
    ):
        with pytest.raises(FinnhubAPIError, match="timed out"):
            await finnhub_client.get_quote("AAPL")


# --- get_company_profile tests ---


@pytest.mark.asyncio
async def test_get_company_profile_success(finnhub_client):
    """Successful profile request returns company info."""
    with patch.object(
        finnhub_client, "_request", new_callable=AsyncMock, return_value=SAMPLE_PROFILE_RESPONSE
    ):
        result = await finnhub_client.get_company_profile("AAPL")
        assert result["name"] == "Apple Inc"
        assert result["ticker"] == "AAPL"
        assert result["industry"] == "Technology"
        assert result["market_capitalization"] == 2500000


@pytest.mark.asyncio
async def test_get_company_profile_not_found(finnhub_client):
    """Empty profile response should raise FinnhubAPIError."""
    with patch.object(finnhub_client, "_request", new_callable=AsyncMock, return_value={}):
        with pytest.raises(FinnhubAPIError, match="No data found"):
            await finnhub_client.get_company_profile("INVALID")


# --- get_company_news tests ---


@pytest.mark.asyncio
async def test_get_company_news_success(finnhub_client):
    """Successful news request returns list of articles."""
    with patch.object(
        finnhub_client, "_request", new_callable=AsyncMock, return_value=SAMPLE_NEWS_RESPONSE
    ):
        result = await finnhub_client.get_company_news("AAPL", "2024-01-01", "2024-01-31")
        assert len(result) == 2
        assert result[0]["headline"] == "Apple Reports Record Revenue"
        assert result[1]["source"] == "Bloomberg"


@pytest.mark.asyncio
async def test_get_company_news_empty(finnhub_client):
    """Empty news list should raise FinnhubAPIError."""
    with patch.object(finnhub_client, "_request", new_callable=AsyncMock, return_value=[]):
        with pytest.raises(FinnhubAPIError, match="No news found"):
            await finnhub_client.get_company_news("AAPL", "2024-01-01", "2024-01-31")


@pytest.mark.asyncio
async def test_get_company_news_invalid_date(finnhub_client):
    """Invalid date format should raise FinnhubAPIError."""
    with pytest.raises(FinnhubAPIError, match="Invalid date format"):
        await finnhub_client.get_company_news("AAPL", "01-01-2024", "2024-01-31")


# --- search_symbol tests ---


@pytest.mark.asyncio
async def test_search_symbol_success(finnhub_client):
    """Successful search returns list of matching symbols."""
    with patch.object(
        finnhub_client, "_request", new_callable=AsyncMock, return_value=SAMPLE_SEARCH_RESPONSE
    ):
        result = await finnhub_client.search_symbol("Apple")
        assert len(result) == 2
        assert result[0]["symbol"] == "AAPL"
        assert result[0]["description"] == "APPLE INC"


@pytest.mark.asyncio
async def test_search_symbol_no_results(finnhub_client):
    """Empty search results should raise FinnhubAPIError."""
    with patch.object(
        finnhub_client, "_request", new_callable=AsyncMock, return_value={"count": 0, "result": []}
    ):
        with pytest.raises(FinnhubAPIError, match="No results found"):
            await finnhub_client.search_symbol("xyznonexistent")


# --- rate limiting tests ---


@pytest.mark.asyncio
async def test_request_rate_limited(finnhub_client):
    """When rate limiter is exhausted, requests should raise FinnhubAPIError."""
    finnhub_client._rate_limiter.acquire = AsyncMock(return_value=False)
    with pytest.raises(FinnhubAPIError, match="[Rr]ate limit"):
        await finnhub_client.get_quote("AAPL")
