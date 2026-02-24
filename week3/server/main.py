import logging
import sys
from datetime import datetime

from mcp.server.fastmcp import FastMCP

from week3.server.config import Settings
from week3.server.finnhub_client import FinnhubClient, FinnhubAPIError
from week3.server.rate_limiter import TokenBucketRateLimiter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)

mcp = FastMCP("Finnhub Financial Data")

_client: FinnhubClient | None = None


def _get_client() -> FinnhubClient:
    global _client
    if _client is None:
        settings = Settings()
        rate_limiter = TokenBucketRateLimiter(
            max_tokens=settings.rate_limit_per_minute,
            refill_period=60.0,
        )
        _client = FinnhubClient(settings=settings, rate_limiter=rate_limiter)
        logger.info("FinnhubClient initialized (base_url=%s)", settings.finnhub_base_url)
    return _client


@mcp.tool()
async def get_stock_quote(symbol: str) -> str:
    """Get real-time stock quote for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL", "MSFT").

    Returns:
        Formatted string with current price, change, and daily range.
    """
    try:
        client = _get_client()
        data = await client.get_quote(symbol)
        sign = "+" if data["change"] >= 0 else ""
        return (
            f"Stock Quote for {symbol.upper()}\n"
            f"{'='*40}\n"
            f"Current Price:  ${data['current_price']:.2f}\n"
            f"Change:         {sign}{data['change']:.2f} ({sign}{data['percent_change']:.2f}%)\n"
            f"Day High:       ${data['high']:.2f}\n"
            f"Day Low:        ${data['low']:.2f}\n"
            f"Open:           ${data['open']:.2f}\n"
            f"Previous Close: ${data['previous_close']:.2f}"
        )
    except FinnhubAPIError as exc:
        logger.warning("get_stock_quote error: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def get_company_profile(symbol: str) -> str:
    """Get company profile and fundamentals for a given ticker symbol.

    Args:
        symbol: Stock ticker symbol (e.g., "AAPL", "GOOGL", "MSFT").

    Returns:
        Formatted string with company name, industry, market cap, etc.
    """
    try:
        client = _get_client()
        data = await client.get_company_profile(symbol)
        mkt_cap = data["market_capitalization"]
        if mkt_cap >= 1_000_000:
            mkt_cap_str = f"${mkt_cap / 1_000_000:.2f}T"
        elif mkt_cap >= 1_000:
            mkt_cap_str = f"${mkt_cap / 1_000:.2f}B"
        else:
            mkt_cap_str = f"${mkt_cap:.2f}M"

        return (
            f"Company Profile: {data['name']} ({data['ticker']})\n"
            f"{'='*40}\n"
            f"Industry:   {data['industry']}\n"
            f"Country:    {data['country']}\n"
            f"Currency:   {data['currency']}\n"
            f"Exchange:   {data['exchange']}\n"
            f"Market Cap: {mkt_cap_str}\n"
            f"IPO Date:   {data['ipo']}\n"
            f"Website:    {data['weburl']}\n"
            f"Phone:      {data['phone']}\n"
            f"Logo:       {data['logo']}"
        )
    except FinnhubAPIError as exc:
        logger.warning("get_company_profile error: %s", exc)
        return f"Error: {exc}"


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
    try:
        client = _get_client()
        articles = await client.get_company_news(symbol, from_date, to_date)
        lines = [f"News for {symbol.upper()} ({from_date} to {to_date})", "=" * 40]
        for i, article in enumerate(articles[:10], 1):
            ts = article.get("datetime", 0)
            date_str = datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M") if ts else "N/A"
            lines.append(
                f"\n{i}. {article['headline']}\n"
                f"   Source: {article['source']} | Date: {date_str}\n"
                f"   {article['summary'][:200]}\n"
                f"   URL: {article['url']}"
            )
        if len(articles) > 10:
            lines.append(f"\n... and {len(articles) - 10} more articles")
        return "\n".join(lines)
    except FinnhubAPIError as exc:
        logger.warning("get_company_news error: %s", exc)
        return f"Error: {exc}"


@mcp.tool()
async def search_symbol(query: str) -> str:
    """Search for stock ticker symbols by company name or keyword.

    Args:
        query: Search query (e.g., "Apple", "Tesla", "semiconductor").

    Returns:
        Formatted string listing matching symbols and descriptions.
    """
    try:
        client = _get_client()
        results = await client.search_symbol(query)
        lines = [f"Symbol Search Results for '{query}'", "=" * 40]
        for item in results[:20]:
            lines.append(f"  {item['symbol']:>10}  |  {item['description']}  ({item['type']})")
        if len(results) > 20:
            lines.append(f"\n... and {len(results) - 20} more results")
        return "\n".join(lines)
    except FinnhubAPIError as exc:
        logger.warning("search_symbol error: %s", exc)
        return f"Error: {exc}"


if __name__ == "__main__":
    transport = "stdio"
    if "--http" in sys.argv:
        transport = "streamable-http"
    mcp.run(transport=transport)
