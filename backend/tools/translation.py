import json
from uuid import uuid4

import httpx
from langchain_core.tools import tool

from backend.config import get_settings


TRANSLATOR_URL = "https://api.cognitive.microsofttranslator.com/translate"


@tool("translation")
async def translation(text: str, target_language: str) -> str:
    """Translate text into a target language code such as es, fr, hi, or ja."""
    settings = get_settings()
    if not settings.azure_translator_key or not settings.azure_translator_region:
        return "Translation is not configured. Set AZURE_TRANSLATOR_KEY and AZURE_TRANSLATOR_REGION."

    if not text.strip():
        return "Translation error: text is empty."
    if not target_language.strip():
        return "Translation error: target language is empty."

    headers = {
        "Ocp-Apim-Subscription-Key": settings.azure_translator_key,
        "Ocp-Apim-Subscription-Region": settings.azure_translator_region,
        "Content-type": "application/json",
        "X-ClientTraceId": str(uuid4()),
    }
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                TRANSLATOR_URL,
                params={"api-version": "3.0", "to": target_language},
                headers=headers,
                json=[{"text": text}],
            )
        response.raise_for_status()
    except httpx.HTTPError as exc:
        return f"Translation error: {exc}"

    payload = response.json()
    translated_text = payload[0]["translations"][0]["text"]
    return json.dumps({"translated_text": translated_text}, ensure_ascii=True)
