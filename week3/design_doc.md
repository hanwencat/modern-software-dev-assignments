# Finnhub MCP Server — Design Document

## Current Context
- This is a course assignment (Week 3) requiring a custom MCP (Model Context Protocol) server.
- The server wraps the Finnhub financial data API to expose stock market data to AI agents.
- The project uses Poetry for dependency management; `mcp[cli]` (v1.26.0) has been added alongside existing dependencies like `httpx`, `pydantic`, and `python-dotenv`.
- No existing MCP server code exists in the project yet.

## Requirements

### Functional Requirements
- Expose **4 MCP tools** with typed parameters:
  1. `get_stock_quote(symbol)` — real-time stock price data
  2. `get_company_profile(symbol)` — company fundamentals
  3. `get_company_news(symbol, from_date, to_date)` — recent news articles
  4. `search_symbol(query)` — ticker symbol lookup
- Support **STDIO transport** (default, for Claude Desktop / Cursor integration)
- Support **HTTP transport** (extra credit, for remote agent access)

### Non-Functional Requirements
- **Resilience**: graceful handling of HTTP errors, timeouts, empty results
- **Rate limiting**: respect Finnhub's 60 requests/minute free-tier limit
- **Security**: API key managed via environment variable, never hardcoded
- **Logging**: structured logging via Python `logging` module (stderr for STDIO mode)
- **Performance**: async HTTP calls via `httpx.AsyncClient`; 10s request timeout

## Design Decisions

### 1. MCP SDK: FastMCP High-Level Interface
Will use `mcp.server.fastmcp.FastMCP` because:
- Minimal boilerplate — decorator-based tool registration
- Built-in support for both STDIO and HTTP transports via `mcp.run(transport=...)`
- Type inference from function signatures for tool parameter schemas

### 2. HTTP Client: httpx (async)
Will use `httpx.AsyncClient` because:
- Already a dev dependency in the project
- Native async support pairs well with FastMCP's async tool handlers
- Built-in timeout, retry, and connection pooling support

### 3. Rate Limiting: Token Bucket
Will implement a simple in-memory token bucket because:
- Finnhub's limit is 60 req/min — a sliding window token bucket fits naturally
- No external dependency needed (no Redis, no third-party lib)
- Alternative considered: per-request sleep/backoff — rejected as it blocks the event loop

### 4. Configuration: Pydantic BaseSettings
Will use `pydantic_settings.BaseSettings` because:
- Automatic `.env` file loading + environment variable binding
- Type validation at startup (fail-fast if API key is missing)
- Already have `pydantic` and `python-dotenv` as dependencies

## Technical Design

### 1. Core Components

```python
# week3/server/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    finnhub_api_key: str
    finnhub_base_url: str = "https://finnhub.io/api/v1"
    request_timeout: float = 10.0
    rate_limit_per_minute: int = 60

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}
```

```python
# week3/server/rate_limiter.py
import asyncio
import time

class TokenBucketRateLimiter:
    """Async-safe token bucket rate limiter."""

    def __init__(self, max_tokens: int, refill_period: float):
        """
        Args:
            max_tokens: Maximum tokens (requests) allowed per period.
            refill_period: Period in seconds over which tokens fully refill.
        """
        ...

    async def acquire(self) -> bool:
        """Consume one token. Returns True if acquired, False if rate-limited."""
        ...
```

```python
# week3/server/finnhub_client.py
import httpx

class FinnhubClient:
    """Async wrapper around Finnhub REST API with rate limiting."""

    def __init__(self, settings: Settings, rate_limiter: TokenBucketRateLimiter):
        ...

    async def get_quote(self, symbol: str) -> dict:
        """GET /api/v1/quote?symbol={symbol}
        Returns: {"current_price": float, "change": float, "percent_change": float,
                  "high": float, "low": float, "open": float, "previous_close": float,
                  "timestamp": int}
        Raises: FinnhubAPIError on HTTP/API failures.
        """
        ...

    async def get_company_profile(self, symbol: str) -> dict:
        """GET /api/v1/stock/profile2?symbol={symbol}
        Returns: {"name": str, "ticker": str, "country": str, "currency": str,
                  "exchange": str, "ipo": str, "market_capitalization": float,
                  "industry": str, "logo": str, "phone": str, "weburl": str}
        Raises: FinnhubAPIError on HTTP/API failures.
        """
        ...

    async def get_company_news(self, symbol: str, from_date: str, to_date: str) -> list[dict]:
        """GET /api/v1/company-news?symbol={symbol}&from={from_date}&to={to_date}
        Returns: [{"headline": str, "summary": str, "source": str, "url": str,
                   "datetime": int, "category": str, "image": str}]
        Raises: FinnhubAPIError on HTTP/API failures.
        """
        ...

    async def search_symbol(self, query: str) -> list[dict]:
        """GET /api/v1/search?q={query}
        Returns: [{"symbol": str, "description": str, "type": str}]
        Raises: FinnhubAPIError on HTTP/API failures.
        """
        ...

    async def close(self) -> None:
        """Close the underlying httpx client."""
        ...


class FinnhubAPIError(Exception):
    """Raised when Finnhub API returns an error or request fails."""
    def __init__(self, message: str, status_code: int | None = None):
        ...
```

```python
# week3/server/main.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Finnhub Financial Data")

@mcp.tool()
async def get_stock_quote(symbol: str) -> str:
    """Get real-time stock quote for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL", "MSFT").

    Returns:
        Formatted string with current price, change, and daily range.
    """
    ...

@mcp.tool()
async def get_company_profile(symbol: str) -> str:
    """Get company profile and fundamentals for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL", "MSFT").

    Returns:
        Formatted string with company name, industry, market cap, etc.
    """
    ...

@mcp.tool()
async def get_company_news(symbol: str, from_date: str, to_date: str) -> str:
    """Get recent news articles for a given company.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL").
        from_date: Start date in YYYY-MM-DD format.
        to_date: End date in YYYY-MM-DD format.

    Returns:
        Formatted string listing news headlines, sources, and URLs.
    """
    ...

@mcp.tool()
async def search_symbol(query: str) -> str:
    """Search for stock ticker symbols by company name or keyword.

    Args:
        query: Search query (e.g., "Apple", "Tesla", "semiconductor").

    Returns:
        Formatted string listing matching symbols and descriptions.
    """
    ...
```

### 2. Data Models

The Finnhub API returns JSON. We parse responses into plain dicts and format them
as human-readable strings for the MCP tool return values (since MCP tools return
text content to the LLM). No Pydantic response models needed — validation happens
at the API client layer via status code checks and key presence checks.

### 3. Integration Points

- **Finnhub REST API**: All 4 endpoints authenticated via `token` query parameter.
- **MCP Clients**: Claude Desktop (STDIO), Cursor IDE (STDIO), or any HTTP MCP client.
- **Environment**: `.env` file or shell environment for `FINNHUB_API_KEY`.

### 4. File Changes

New files to create:
- `week3/server/__init__.py`
- `week3/server/main.py`
- `week3/server/config.py`
- `week3/server/finnhub_client.py`
- `week3/server/rate_limiter.py`
- `week3/tests/__init__.py`
- `week3/tests/conftest.py`
- `week3/tests/test_finnhub_client.py`
- `week3/tests/test_tools.py`
- `week3/README.md`

Modified files:
- `pyproject.toml` (already done — added `mcp[cli]`)

## Implementation Plan

1. **Phase 1: Foundation**
   - `config.py` — Settings class with env var binding
   - `rate_limiter.py` — Token bucket implementation

2. **Phase 2: API Client**
   - `finnhub_client.py` — All 4 endpoint methods with error handling

3. **Phase 3: MCP Server**
   - `main.py` — FastMCP instance, tool registration, STDIO + HTTP entrypoint

4. **Phase 4: Docs**
   - `README.md` — Setup, config, tool reference, example invocations

## Testing Strategy

### Unit Tests (`test_finnhub_client.py`)
- Mock `httpx.AsyncClient` responses for each endpoint
- Test successful responses: verify parsed output structure
- Test HTTP error (4xx, 5xx): verify `FinnhubAPIError` raised with message
- Test timeout: verify `FinnhubAPIError` raised
- Test empty/invalid response: verify graceful error message
- Test rate limiter: verify token consumption and rejection

### Integration Tests (`test_tools.py`)
- Mock `FinnhubClient` at the tool level
- Test each MCP tool returns formatted string output
- Test tools handle `FinnhubAPIError` gracefully (return error message, don't crash)
- Test input validation (empty symbol, invalid date format)

### Mock Strategy
- Use `unittest.mock.AsyncMock` and `pytest-asyncio` for async tests
- Mock at the `httpx` transport layer for client tests
- Mock at the `FinnhubClient` layer for tool tests

## Observability

### Logging
- Use Python `logging` module with `stderr` handler (required for STDIO transport)
- Log levels: INFO for successful requests, WARNING for rate limits, ERROR for failures
- Format: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`

## Security Considerations
- `FINNHUB_API_KEY` stored in `.env` file (gitignored) or environment variable
- API key passed as query parameter to Finnhub (their recommended auth method)
- No secrets in source code or logs

## References
- [Finnhub API Docs](https://finnhub.io/docs/api)
- [MCP Python SDK](https://modelcontextprotocol.github.io/python-sdk/)
- [FastMCP Quick Start](https://modelcontextprotocol.io/quickstart/server)
- [MCP Authorization Spec](https://modelcontextprotocol.io/specification/2025-06-18/basic/authorization)
