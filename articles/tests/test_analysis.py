# articles/tests/test_analysis.py
from unittest.mock import patch

import pytest
from ddgs.exceptions import DDGSException

from articles import cache_utils
from articles.ai_detection import detect_ai
from articles.external_search import SearchUnavailableError, search_fragment
from articles.use_cases import analyze_text_fragments


def test_cache_set_and_get(tmp_path, monkeypatch):
    test_query = "sample fragment"
    test_results = [{"title": "Test",
                     "url": "http://example.com", "snippet": "text"}]

    cache_file = tmp_path / "test_cache.json"
    monkeypatch.setattr(cache_utils, "CACHE_FILE", str(cache_file))

    cache_utils.set_cached_result(test_query, test_results)
    cached = cache_utils.get_cached_result(test_query)

    assert cached == test_results


@patch("articles.decorators.get_cached_result")
@patch("articles.decorators.set_cached_result")
@patch("articles.external_search.DDGS")
def test_search_fragment_uses_duckduckgo(mock_ddgs,
                                         mock_set_cache,
                                         mock_get_cache):
    mock_get_cache.return_value = None

    mock_ddgs.return_value.text.return_value = [
        {"title": "Test Result",
         "href": "http://example.com", "body": "snippet"}
    ]

    result = search_fragment("unit test example")

    assert isinstance(result, list)
    assert result[0] == {"title": "Test Result",
                         "url": "http://example.com", "snippet": "snippet"}
    assert mock_set_cache.called


@patch("articles.decorators.get_cached_result")
@patch("articles.decorators.set_cached_result")
@patch("articles.external_search.DDGS")
def test_search_fragment_blocked_is_not_cached(mock_ddgs,
                                               mock_set_cache,
                                               mock_get_cache):
    mock_get_cache.return_value = None
    mock_ddgs.return_value.text.side_effect = DDGSException(
        "No results found.")

    with pytest.raises(SearchUnavailableError):
        search_fragment("unit test example")

    assert not mock_set_cache.called


@patch("articles.use_cases.search_fragment")
def test_originality_unknown_when_search_unavailable(mock_search):
    mock_search.side_effect = SearchUnavailableError

    originality, matches = analyze_text_fragments("слово " * 100)

    assert originality is None
    assert matches == []
    # После первой блокировки поиск больше не дёргаем
    assert mock_search.call_count == 1


def test_detect_ai_probability_range():
    result = detect_ai("This is an example "
                       "academic abstract about psychology.")
    assert 0 <= result <= 100
