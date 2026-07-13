"""Tests for entity extraction, especially browser search queries."""

import pytest

from jarvis.services.entity_extraction import PatternEntityExtractor


@pytest.fixture
def extractor() -> PatternEntityExtractor:
    return PatternEntityExtractor()


@pytest.mark.parametrize(
    ("message", "expected_query"),
    [
        ("Open Google and search ChatGPT", "ChatGPT"),
        ("Search latest AI news", "latest AI news"),
        ("Can you search FastAPI tutorial?", "FastAPI tutorial"),
        ("search google for Python tutorials", "Python tutorials"),
        ("search on google for weather today", "weather today"),
        ("google search machine learning basics", "machine learning basics"),
        ("search for docker compose guide", "docker compose guide"),
        ("look up FastAPI dependency injection", "FastAPI dependency injection"),
        ("find best python IDE 2026", "best python IDE 2026"),
        ("please search React hooks examples", "React hooks examples"),
    ],
)
def test_extract_search_query(
    extractor: PatternEntityExtractor,
    message: str,
    expected_query: str,
) -> None:
    result = extractor.extract(message, "BROWSER_SEARCH_GOOGLE")
    assert result.entities["query"] == expected_query


def test_extract_search_query_empty_fallback(extractor: PatternEntityExtractor) -> None:
    result = extractor.extract("search", "BROWSER_SEARCH_GOOGLE")
    assert result.entities["query"] == ""


def test_extract_destination_strips_verbs(extractor: PatternEntityExtractor) -> None:
    result = extractor.extract("open GitHub", "BROWSER_OPEN_DESTINATION")
    assert result.entities["destination"] == "github"


def test_extract_new_tab_url(extractor: PatternEntityExtractor) -> None:
    result = extractor.extract(
        "open new tab https://example.com",
        "BROWSER_OPEN_NEW_TAB",
    )
    assert result.entities["url"] == "https://example.com"


def test_paramless_browser_intents_return_empty_entities(
    extractor: PatternEntityExtractor,
) -> None:
    for intent in (
        "BROWSER_GO_BACK",
        "BROWSER_READ_PAGE",
        "BROWSER_SUMMARIZE_PAGE",
    ):
        result = extractor.extract("go back", intent)
        assert result.entities == {}
