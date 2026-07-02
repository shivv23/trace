import logging
from duckduckgo_search import DDGS

logger = logging.getLogger(__name__)


def search_web(query: str, max_results: int = 5) -> list[dict]:
    try:
        ddgs = DDGS()
        raw = list(ddgs.text(query, max_results=max_results))
        results = []
        for r in raw:
            results.append({
                "title": r.get("title", ""),
                "href": r.get("href", ""),
                "body": r.get("body", ""),
                "source_type": "web",
            })
        return results
    except Exception as e:
        logger.warning(f"Web search failed: {e}")
        return []


def format_web_results(results: list[dict]) -> str:
    if not results:
        return ""
    parts = []
    for i, r in enumerate(results):
        parts.append(f"[Web {i + 1}] {r['title']}\n{r['body']}\nSource: {r['href']}")
    return "\n\n".join(parts)
