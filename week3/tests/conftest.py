import pytest
from unittest.mock import AsyncMock, patch

from week3.server.config import Settings
from week3.server.rate_limiter import TokenBucketRateLimiter
from week3.server.finnhub_client import FinnhubClient


@pytest.fixture
def settings():
    return Settings(
        finnhub_api_key="test-api-key-123",
        finnhub_base_url="https://finnhub.io/api/v1",
        request_timeout=5.0,
        rate_limit_per_minute=60,
    )


@pytest.fixture
def rate_limiter():
    return TokenBucketRateLimiter(max_tokens=60, refill_period=60.0)


@pytest.fixture
def finnhub_client(settings, rate_limiter):
    return FinnhubClient(settings=settings, rate_limiter=rate_limiter)


SAMPLE_QUOTE_RESPONSE = {
    "c": 150.25,
    "d": 2.50,
    "dp": 1.69,
    "h": 151.00,
    "l": 148.50,
    "o": 149.00,
    "pc": 147.75,
    "t": 1700000000,
}

SAMPLE_PROFILE_RESPONSE = {
    "country": "US",
    "currency": "USD",
    "exchange": "NASDAQ NMS - GLOBAL MARKET",
    "finnhubIndustry": "Technology",
    "ipo": "1980-12-12",
    "logo": "https://static2.finnhub.io/file/publicdatany/finnhubimage/stock_logo/AAPL.png",
    "marketCapitalization": 2500000,
    "name": "Apple Inc",
    "phone": "14089961010",
    "shareOutstanding": 15700,
    "ticker": "AAPL",
    "weburl": "https://www.apple.com/",
}

SAMPLE_NEWS_RESPONSE = [
    {
        "category": "company",
        "datetime": 1700000000,
        "headline": "Apple Reports Record Revenue",
        "id": 12345,
        "image": "https://example.com/image.jpg",
        "related": "AAPL",
        "source": "Reuters",
        "summary": "Apple Inc reported record quarterly revenue...",
        "url": "https://example.com/article",
    },
    {
        "category": "company",
        "datetime": 1699999000,
        "headline": "Apple Launches New Product",
        "id": 12346,
        "image": "https://example.com/image2.jpg",
        "related": "AAPL",
        "source": "Bloomberg",
        "summary": "Apple unveiled its latest product line...",
        "url": "https://example.com/article2",
    },
]

SAMPLE_SEARCH_RESPONSE = {
    "count": 2,
    "result": [
        {
            "description": "APPLE INC",
            "displaySymbol": "AAPL",
            "symbol": "AAPL",
            "type": "Common Stock",
        },
        {
            "description": "APPLE HOSPITALITY REIT INC",
            "displaySymbol": "APLE",
            "symbol": "APLE",
            "type": "Common Stock",
        },
    ],
}
