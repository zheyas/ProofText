# articles/external_search.py
import logging

from ddgs import DDGS
from ddgs.exceptions import DDGSException

from .decorators import cached_search

logger = logging.getLogger(__name__)


class SearchUnavailableError(Exception):
    """DuckDuckGo не ответил или ограничил частоту запросов."""


@cached_search
def search_fragment(query):
    """
    Ищет фрагмент текста в DuckDuckGo и возвращает результаты.

    Официального API у DuckDuckGo нет: при частых запросах он отвечает
    пустой страницей, и это неотличимо от «ничего не найдено». Поэтому
    пустой ответ считается ошибкой и не попадает в кэш.
    """
    try:
        items = DDGS(timeout=10).text(
            query, region="ru-ru", max_results=5, backend="duckduckgo"
        )
    except DDGSException as e:
        logger.warning(f"[DuckDuckGo] Поиск недоступен: {e}")
        raise SearchUnavailableError(str(e)) from e

    results = [
        {
            "title": item.get("title"),
            "url": item.get("href"),
            "snippet": item.get("body"),
        }
        for item in items
    ]

    logger.info(f"[DuckDuckGo] Найдено совпадений: {len(results)}")
    return results
