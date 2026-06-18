"""Live web search via the Tavily API.

Tavily is purpose-built for AI agents/RAG: it returns cleaned, structured
page content (instead of raw HTML/links) plus an optional synthesized quick
answer, which makes it a good fit for feeding a verification LLM call.
"""
from tavily import TavilyClient

from . import config

_client = None


def get_client() -> TavilyClient:
    global _client
    if _client is None:
        if not config.TAVILY_API_KEY:
            raise RuntimeError(
                "TAVILY_API_KEY is not set. Add it to .streamlit/secrets.toml "
                "locally, or to your app's Secrets in Streamlit Community Cloud."
            )
        _client = TavilyClient(api_key=config.TAVILY_API_KEY)
    return _client


def search_claim(claim_text: str) -> dict:
    """Run a live web search for a single claim.

    Returns a compact payload: Tavily's synthesized quick answer (if any)
    plus a handful of source snippets (title, url, truncated content).
    """
    client = get_client()
    response = client.search(
        query=claim_text,
        search_depth=config.TAVILY_SEARCH_DEPTH,
        max_results=config.TAVILY_MAX_RESULTS,
        include_answer=True,
    )

    sources = [
        {
            "title": r.get("title", ""),
            "url": r.get("url", ""),
            "content": (r.get("content", "") or "")[:1200],
        }
        for r in response.get("results", [])
    ]

    return {
        "tavily_answer": response.get("answer", "") or "",
        "sources": sources,
    }
