from functools import lru_cache

from langchain_core.tools import BaseTool

from backend.tools.calculator import calculator
from backend.tools.search import web_search
from backend.tools.translation import translation
from backend.tools.wikipedia import wikipedia


@lru_cache
def get_langchain_tools() -> tuple[BaseTool, ...]:
    return (
        calculator,
        web_search,
        wikipedia,
        translation,
    )
