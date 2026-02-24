# Week 3 — Finnhub MCP Server

A Model Context Protocol (MCP) server that wraps the [Finnhub](https://finnhub.io) financial data API, exposing stock market data as tools for AI agents. Supports both **STDIO** (local) and **HTTP** (remote) transports.

## Prerequisites

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management
- A free Finnhub API key (register at [finnhub.io](https://finnhub.io))

## Setup

### 1. Install dependencies

From the project root directory:

```bash
poetry install
```

### 2. Configure environment

Create a `.env` file in the **project root** (or `week3/server/` directory):

```env
FINNHUB_API_KEY=your_api_key_here
```

Alternatively, export the environment variable directly:

```bash
export FINNHUB_API_KEY=your_api_key_here
```

### 3. Run tests

```bash
poetry run python -m pytest week3/tests/ -v
```

## Running the Server

### Local mode (STDIO)

```bash
poetry run python -m week3.server.main
```

This starts the MCP server in STDIO mode, suitable for Claude Desktop or Cursor IDE integration.

### Remote mode (HTTP) — Extra Credit

```bash
poetry run python -m week3.server.main --http
```

This starts the server with Streamable HTTP transport, accessible over the network.

## Client Configuration

### Claude Desktop (STDIO)

Add the following to your Claude Desktop configuration (`claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "finnhub": {
      "command": "poetry",
      "args": ["run", "python", "-m", "week3.server.main"],
      "cwd": "/path/to/modern-software-dev-assignments",
      "env": {
        "FINNHUB_API_KEY": "your_api_key_here"
      }
    }
  }
}
```

### Cursor IDE (STDIO)

In Cursor settings, add the MCP server with:
- **Command**: `poetry run python -m week3.server.main`
- **Working directory**: project root
- **Environment**: `FINNHUB_API_KEY=your_api_key_here`

## Tool Reference

### `get_stock_quote`

Get real-time stock quote for a given ticker symbol.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol`  | str  | Yes      | Stock ticker symbol (e.g., "AAPL", "GOOGL") |

**Example input:**
```
get_stock_quote(symbol="AAPL")
```

**Example output:**
```
Stock Quote for AAPL
========================================
Current Price:  $178.72
Change:         +1.25 (+0.70%)
Day High:       $179.50
Day Low:        $176.80
Open:           $177.50
Previous Close: $177.47
```

---

### `get_company_profile`

Get company profile and fundamentals for a given ticker symbol.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `symbol`  | str  | Yes      | Stock ticker symbol (e.g., "AAPL") |

**Example input:**
```
get_company_profile(symbol="AAPL")
```

**Example output:**
```
Company Profile: Apple Inc (AAPL)
========================================
Industry:   Technology
Country:    US
Currency:   USD
Exchange:   NASDAQ NMS - GLOBAL MARKET
Market Cap: $2.50T
IPO Date:   1980-12-12
Website:    https://www.apple.com/
Phone:      14089961010
Logo:       https://static2.finnhub.io/file/publicdatany/finnhubimage/stock_logo/AAPL.png
```

---

### `get_company_news`

Get recent news articles for a given company.

| Parameter   | Type | Required | Description |
|-------------|------|----------|-------------|
| `symbol`    | str  | Yes      | Stock ticker symbol (e.g., "AAPL") |
| `from_date` | str  | Yes      | Start date in YYYY-MM-DD format |
| `to_date`   | str  | Yes      | End date in YYYY-MM-DD format |

**Example input:**
```
get_company_news(symbol="AAPL", from_date="2024-01-01", to_date="2024-01-31")
```

**Example output:**
```
News for AAPL (2024-01-01 to 2024-01-31)
========================================

1. Apple Reports Record Revenue
   Source: Reuters | Date: 2024-01-25 14:30
   Apple Inc reported record quarterly revenue of $119.6 billion...
   URL: https://example.com/article

2. Apple Launches Vision Pro
   Source: Bloomberg | Date: 2024-01-20 09:15
   Apple officially launched its Vision Pro headset...
   URL: https://example.com/article2
```

---

### `search_symbol`

Search for stock ticker symbols by company name or keyword.

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `query`   | str  | Yes      | Search query (e.g., "Apple", "Tesla") |

**Example input:**
```
search_symbol(query="Apple")
```

**Example output:**
```
Symbol Search Results for 'Apple'
========================================
        AAPL  |  APPLE INC  (Common Stock)
        APLE  |  APPLE HOSPITALITY REIT INC  (Common Stock)
```

## Error Handling

All tools handle errors gracefully and return human-readable error messages instead of crashing:

- **Invalid symbol**: `Error: No data found for symbol: INVALID`
- **Rate limit exceeded**: `Error: Rate limit exceeded. Please wait before making more requests.`
- **Network timeout**: `Error: Request timed out`
- **Invalid date format**: `Error: Invalid date format: '01-01-2024'. Expected YYYY-MM-DD.`

## Architecture

```
week3/
  server/
    __init__.py
    main.py              # FastMCP entry point + 4 tool handlers
    config.py            # Pydantic Settings (env var management)
    finnhub_client.py    # Async Finnhub API client with error handling
    rate_limiter.py      # Token bucket rate limiter (60 req/min)
  tests/
    __init__.py
    conftest.py          # Shared fixtures and sample data
    test_rate_limiter.py # Rate limiter unit tests
    test_finnhub_client.py # API client unit tests
    test_tools.py        # MCP tool integration tests
  design_doc.md          # Design document
  README.md              # This file
```

## Rate Limiting

The server implements a token bucket rate limiter to respect Finnhub's free-tier limit of **60 requests per minute**. When the limit is reached, tools return a descriptive error message asking the user to wait.
