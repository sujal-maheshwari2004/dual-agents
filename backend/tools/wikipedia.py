import json
from urllib.parse import quote

import httpx
from langchain_core.tools import tool


@tool("wikipedia")
async def wikipedia(topic: str) -> str:
    """Fetch a concise summary paragraph for a Wikipedia topic."""
    topic = topic.strip()
    if not topic:
        return "Wikipedia error: topic is empty."

    url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(topic)}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                url,
                headers={
                    "accept": "application/json",
                    "User-Agent": "dual-agents/1.0 (https://bot-street.web.app)",
                },
            )

        if response.status_code == 404:
            return f"No Wikipedia page found for {topic}."
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Wikipedia error: {exc}"

    payload = response.json()
    result = {
        "title": payload.get("title", topic),
        "summary": payload.get("extract", ""),
        "url": payload.get("content_urls", {}).get("desktop", {}).get("page"),
    }
    return json.dumps(result, ensure_ascii=True)