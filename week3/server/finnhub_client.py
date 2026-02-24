import logging
import re
from datetime import datetime

import httpx

from week3.server.config import Settings
from week3.server.rate_limiter import TokenBucketRateLimiter

logger = logging.getLogger(__name__)

_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class FinnhubAPIError(Exception):
    """Raised when Finnhub API returns an error or request fails."""

    def __init__(self, message: str, status_code: int | None = None):
        super().__init__(message)
        self.status_code = status_code


class FinnhubClient:
    """Async wrapper around Finnhub REST API with rate limiting."""

    def __init__(self, settings: Settings, rate_limiter: TokenBucketRateLimiter):
        self._settings = settings
        self._rate_limiter = rate_limiter
        self._http_client = httpx.AsyncClient(
            base_url=settings.finnhub_base_url,
            timeout=settings.request_timeout,
            params={"token": settings.finnhub_api_key},
        )

    async def _request(self, endpoint: str, params: dict | None = None) -> dict | list:
        """Make a rate-limited GET request to Finnhub.

        Raises FinnhubAPIError on rate limit, HTTP errors, or timeouts.
        """
        if not await self._rate_limiter.acquire():
            raise FinnhubAPIError(
                "Rate limit exceeded. Please wait before making more requests."
            )

        try:
            response = await self._http_client.get(endpoint, params=params or {})
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            logger.error("Finnhub HTTP %d on %s", status, endpoint)
            if status == 429:
                raise FinnhubAPIError(
                    "Finnhub rate limit reached. Please try again later.", status_code=429
                ) from exc
            raise FinnhubAPIError(
                f"HTTP {status}: {exc.response.text[:200]}", status_code=status
            ) from exc
        except httpx.TimeoutException as exc:
            logger.error("Finnhub request timed out for %s", endpoint)
            raise FinnhubAPIError("Request timed out") from exc
        except httpx.ConnectError as exc:
            logger.error("Finnhub connection error for %s: %s", endpoint, exc)
            raise FinnhubAPIError("Could not connect to Finnhub API") from exc

    async def get_quote(self, symbol: str) -> dict:
        """Get real-time stock quote.

        Returns dict with keys: current_price, change, percent_change,
        high, low, open, previous_close, timestamp.
        """
        symbol = symbol.strip().upper()
        if not symbol:
            raise FinnhubAPIError("Symbol cannot be empty")

        data = await self._request("/quote", params={"symbol": symbol})

        if data.get("c", 0) == 0 and data.get("h", 0) == 0:
            raise FinnhubAPIError(f"No data found for symbol: {symbol}")

        return {
            "current_price": data["c"],
            "change": data["d"],
            "percent_change": data["dp"],
            "high": data["h"],
            "low": data["l"],
            "open": data["o"],
            "previous_close": data["pc"],
            "timestamp": data["t"],
        }

    async def get_company_profile(self, symbol: str) -> dict:
        """Get company profile and fundamentals.

        Returns dict with keys: name, ticker, country, currency, exchange,
        industry, market_capitalization, ipo, logo, phone, weburl.
        """
        symbol = symbol.strip().upper()
        if not symbol:
            raise FinnhubAPIError("Symbol cannot be empty")

        data = await self._request("/stock/profile2", params={"symbol": symbol})

        if not data or not data.get("name"):
            raise FinnhubAPIError(f"No data found for symbol: {symbol}")

        return {
            "name": data.get("name", ""),
            "ticker": data.get("ticker", ""),
            "country": data.get("country", ""),
            "currency": data.get("currency", ""),
            "exchange": data.get("exchange", ""),
            "industry": data.get("finnhubIndustry", ""),
            "market_capitalization": data.get("marketCapitalization", 0),
            "ipo": data.get("ipo", ""),
            "logo": data.get("logo", ""),
            "phone": data.get("phone", ""),
            "weburl": data.get("weburl", ""),
        }

    async def get_company_news(
        self, symbol: str, from_date: str, to_date: str
    ) -> list[dict]:
        """Get company news articles.

        Returns list of dicts with keys: headline, summary, source, url,
        datetime, category, image.
        """
        symbol = symbol.strip().upper()
        if not symbol:
            raise FinnhubAPIError("Symbol cannot be empty")

        for date_str in (from_date, to_date):
            if not _DATE_PATTERN.match(date_str):
                raise FinnhubAPIError(
                    f"Invalid date format: '{date_str}'. Expected YYYY-MM-DD."
                )

        data = await self._request(
            "/company-news",
            params={"symbol": symbol, "from": from_date, "to": to_date},
        )

        if not data:
            raise FinnhubAPIError(
                f"No news found for {symbol} between {from_date} and {to_date}"
            )

        return [
            {
                "headline": article.get("headline", ""),
                "summary": article.get("summary", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "datetime": article.get("datetime", 0),
                "category": article.get("category", ""),
                "image": article.get("image", ""),
            }
            for article in data
        ]

    async def search_symbol(self, query: str) -> list[dict]:
        """Search for stock ticker symbols.

        Returns list of dicts with keys: symbol, description, type.
        """
        query = query.strip()
        if not query:
            raise FinnhubAPIError("Search query cannot be empty")

        data = await self._request("/search", params={"q": query})

        results = data.get("result", [])
        if not results:
            raise FinnhubAPIError(f"No results found for query: '{query}'")

        return [
            {
                "symbol": item.get("symbol", ""),
                "description": item.get("description", ""),
                "type": item.get("type", ""),
            }
            for item in results
        ]

    async def close(self) -> None:
        """Close the underlying httpx client."""
        await self._http_client.aclose()
