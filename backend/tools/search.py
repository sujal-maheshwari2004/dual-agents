import json

import httpx
from langchain_core.tools import tool


DUCKDUCKGO_URL = "https://api.duckduckgo.com/"


def _collect_related_topics(items: list[dict], results: list[dict[str, str]]) -> None:
    for item in items:
        if len(results) >= 3:
            return
        if "Topics" in item:
            _collect_related_topics(item["Topics"], results)
            continue
        text = item.get("Text")
        url = item.get("FirstURL")
        if text and url:
            results.append({"title": text.split(" - ")[0], "url": url, "snippet": text})


@tool("web_search")
async def web_search(query: str) -> str:
    """Search the web for a query and return up to three concise DuckDuckGo results."""
    if not query.strip():
        return "Search error: query is empty."

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                DUCKDUCKGO_URL,
                params={
                    "q": query,
                    "format": "json",
                    "no_html": 1,
                    "skip_disambig": 1,
                },
            )
            response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Search error: {exc}"

    payload = response.json()
    results: list[dict[str, str]] = []
    abstract = payload.get("AbstractText")
    abstract_url = payload.get("AbstractURL")
    heading = payload.get("Heading") or query
    if abstract and abstract_url:
        results.append({"title": heading, "url": abstract_url, "snippet": abstract})

    _collect_related_topics(payload.get("RelatedTopics", []), results)
    if not results:
        return "No search results found."
    return json.dumps(results[:3], ensure_ascii=True)
