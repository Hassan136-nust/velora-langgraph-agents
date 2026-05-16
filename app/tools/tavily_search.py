"""
Tavily search tool with retry, exponential backoff, and structured error reporting.
"""

from tavily import TavilyClient
from app.config import TAVILY_API_KEY, MAX_SEARCH_RESULTS
from app.utils.retry import retry_with_backoff, classify_error, make_error_response
from app.utils.logger import log


@retry_with_backoff(max_retries=3, base_delay=1.0)
def _tavily_request(client: TavilyClient, query: str, max_results: int) -> dict:
    """Raw Tavily API call wrapped with retry."""
    return client.search(
        query=query,
        max_results=max_results,
        search_depth="advanced",
        include_answer=False,
    )


def search_tavily(query: str, max_results: int = None) -> list[dict]:
    """
    Search Tavily with retry and error handling.

    Returns a list of result dicts on success, or a list containing
    a single error dict on failure.
    """
    if max_results is None:
        max_results = MAX_SEARCH_RESULTS

    if not TAVILY_API_KEY or TAVILY_API_KEY.startswith("tvly-replace"):
        log("Tavily", "WARNING", "No valid API key configured — returning empty results")
        return []

    try:
        client = TavilyClient(api_key=TAVILY_API_KEY)
        response = _tavily_request(client, query, max_results)

        results = []
        for item in response.get("results", []):
            results.append({
                "title": item.get("title", ""),
                "snippet": item.get("content", ""),
                "url": item.get("url", ""),
                "source": _extract_domain(item.get("url", "")),
                "date": item.get("published_date", ""),
            })

        log("Tavily", "INFO", f"Search for '{query}' returned {len(results)} results")
        return results

    except Exception as exc:
        error_type = classify_error(exc)
        log("Tavily", "ERROR", f"{error_type}: {exc}")

        if error_type == "API_LIMIT":
            fallback = "Tavily API limit reached — using reduced research mode"
        elif error_type == "TIMEOUT":
            fallback = "Tavily request timed out — proceeding with available data"
        elif error_type == "NETWORK_ERROR":
            fallback = "Network error reaching Tavily — proceeding with cached data"
        else:
            fallback = "Tavily search failed — proceeding with available data"

        log("Tavily", "WARNING", fallback)
        return []


def _extract_domain(url: str) -> str:
    try:
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain
    except Exception:
        return url
