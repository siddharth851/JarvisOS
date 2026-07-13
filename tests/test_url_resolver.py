"""Unit tests for the URLResolver service.

Covers all resolution priority tiers:
1. Full URL passthrough
2. Bare domain upgrade
3. Known website name lookup
4. Unknown website / natural-language → Google search fallback
"""

from __future__ import annotations

import pytest
from urllib.parse import quote_plus

from jarvis.services.url_resolver import URLResolver, get_url_resolver


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def resolver() -> URLResolver:
    return URLResolver()


# ---------------------------------------------------------------------------
# 1. Full URL passthrough
# ---------------------------------------------------------------------------


class TestFullURL:
    def test_https_url_returned_verbatim(self, resolver: URLResolver) -> None:
        url = "https://example.com"
        assert resolver.resolve(url) == url

    def test_http_url_returned_verbatim(self, resolver: URLResolver) -> None:
        url = "http://example.com"
        assert resolver.resolve(url) == url

    def test_https_url_with_path(self, resolver: URLResolver) -> None:
        url = "https://github.com/user/repo"
        assert resolver.resolve(url) == url

    def test_https_url_with_query(self, resolver: URLResolver) -> None:
        url = "https://www.google.com/search?q=hello+world"
        assert resolver.resolve(url) == url


# ---------------------------------------------------------------------------
# 2. Bare domain upgrade
# ---------------------------------------------------------------------------


class TestBareDomain:
    def test_simple_domain_gets_https_prefix(self, resolver: URLResolver) -> None:
        assert resolver.resolve("github.com") == "https://github.com"

    def test_domain_with_path(self, resolver: URLResolver) -> None:
        assert resolver.resolve("reddit.com") == "https://reddit.com"

    def test_subdomain(self, resolver: URLResolver) -> None:
        assert resolver.resolve("chat.openai.com") == "https://chat.openai.com"

    def test_domain_co_uk(self, resolver: URLResolver) -> None:
        assert resolver.resolve("bbc.co.uk") == "https://bbc.co.uk"


# ---------------------------------------------------------------------------
# 3. Known website name lookup
# ---------------------------------------------------------------------------


class TestKnownWebsiteName:
    @pytest.mark.parametrize(
        "name,expected_url",
        [
            ("GitHub", "https://github.com"),
            ("github", "https://github.com"),
            ("GITHUB", "https://github.com"),
            ("Canva", "https://www.canva.com"),
            ("ChatGPT", "https://chat.openai.com"),
            ("Reddit", "https://www.reddit.com"),
            ("YouTube", "https://www.youtube.com"),
            ("LinkedIn", "https://www.linkedin.com"),
            ("Notion", "https://www.notion.so"),
            ("Figma", "https://www.figma.com"),
            ("Twitter", "https://twitter.com"),
            ("Stack Overflow", "https://stackoverflow.com"),
            ("Hacker News", "https://news.ycombinator.com"),
            ("Google Drive", "https://drive.google.com"),
        ],
    )
    def test_known_site(
        self, resolver: URLResolver, name: str, expected_url: str
    ) -> None:
        assert resolver.resolve(name) == expected_url

    def test_case_insensitive_lookup(self, resolver: URLResolver) -> None:
        assert resolver.resolve("canva") == resolver.resolve("Canva")
        assert resolver.resolve("REDDIT") == resolver.resolve("reddit")


# ---------------------------------------------------------------------------
# 4. Unknown website / natural language → Google search fallback
# ---------------------------------------------------------------------------


class TestUnknownWebsite:
    def test_unknown_name_falls_back_to_google_search(self, resolver: URLResolver) -> None:
        result = resolver.resolve("SomeRandomUnknownSite")
        assert result.startswith("https://www.google.com/search?q=")

    def test_natural_language_phrase(self, resolver: URLResolver) -> None:
        query = "best python tutorials"
        result = resolver.resolve(query)
        expected = f"https://www.google.com/search?q={quote_plus(query)}"
        assert result == expected

    def test_partial_site_name_goes_to_search(self, resolver: URLResolver) -> None:
        # "git" alone is not in the mapping → search
        result = resolver.resolve("git")
        assert result.startswith("https://www.google.com/search?q=")

    def test_spaces_encoded_correctly(self, resolver: URLResolver) -> None:
        query = "open source projects"
        result = resolver.resolve(query)
        # quote_plus encodes spaces as '+'
        assert "+" in result or "%20" in result


# ---------------------------------------------------------------------------
# 5. Natural language request — end-to-end through resolver only
# ---------------------------------------------------------------------------


class TestNaturalLanguageRequest:
    """Simulate what the pipeline sends after entity extraction strips verbs."""

    def test_open_github(self, resolver: URLResolver) -> None:
        # After stripping "open", entity_extractor yields "github"
        assert resolver.resolve("github") == "https://github.com"

    def test_go_to_chatgpt(self, resolver: URLResolver) -> None:
        # After stripping "go to", entity_extractor yields "chatgpt"
        assert resolver.resolve("chatgpt") == "https://chat.openai.com"

    def test_launch_reddit(self, resolver: URLResolver) -> None:
        assert resolver.resolve("reddit") == "https://www.reddit.com"

    def test_open_full_url(self, resolver: URLResolver) -> None:
        assert resolver.resolve("https://example.com") == "https://example.com"

    def test_open_domain(self, resolver: URLResolver) -> None:
        assert resolver.resolve("example.com") == "https://example.com"

    def test_unknown_destination_google_search(self, resolver: URLResolver) -> None:
        dest = "some obscure site"
        result = resolver.resolve(dest)
        assert result == f"https://www.google.com/search?q={quote_plus(dest)}"


# ---------------------------------------------------------------------------
# 6. Edge cases / error handling
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_string_raises_value_error(self, resolver: URLResolver) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            resolver.resolve("")

    def test_whitespace_only_raises_value_error(self, resolver: URLResolver) -> None:
        with pytest.raises(ValueError, match="cannot be empty"):
            resolver.resolve("   ")

    def test_singleton_returns_same_instance(self) -> None:
        r1 = get_url_resolver()
        r2 = get_url_resolver()
        assert r1 is r2


# ---------------------------------------------------------------------------
# 7. BrowserTool.open_destination integration (mocked webbrowser)
# ---------------------------------------------------------------------------


class TestBrowserToolOpenDestination:
    """Verify BrowserTool.open_destination correctly integrates with URLResolver."""

    def test_open_destination_known_site(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import webbrowser
        from jarvis.tools.browser import BrowserTool

        opened_urls: list[str] = []
        monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url) or True)

        tool = BrowserTool()
        result = tool.open_destination("GitHub")
        assert result is True
        assert opened_urls == ["https://github.com"]

    def test_open_destination_full_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import webbrowser
        from jarvis.tools.browser import BrowserTool

        opened_urls: list[str] = []
        monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url) or True)

        tool = BrowserTool()
        tool.open_destination("https://example.com")
        assert opened_urls == ["https://example.com"]

    def test_open_destination_domain(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import webbrowser
        from jarvis.tools.browser import BrowserTool

        opened_urls: list[str] = []
        monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url) or True)

        tool = BrowserTool()
        tool.open_destination("reddit.com")
        assert opened_urls == ["https://reddit.com"]

    def test_open_destination_unknown_goes_to_google(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        import webbrowser
        from jarvis.tools.browser import BrowserTool

        opened_urls: list[str] = []
        monkeypatch.setattr(webbrowser, "open", lambda url: opened_urls.append(url) or True)

        tool = BrowserTool()
        tool.open_destination("totally unknown site xyz")
        assert len(opened_urls) == 1
        assert opened_urls[0].startswith("https://www.google.com/search?q=")

    def test_execute_open_destination_action(self, monkeypatch: pytest.MonkeyPatch) -> None:
        import webbrowser
        from jarvis.tools.browser import BrowserTool

        monkeypatch.setattr(webbrowser, "open", lambda url: True)

        tool = BrowserTool()
        result = tool.execute(action="open_destination", destination="Canva")
        assert result is True

    def test_execute_open_destination_missing_param_raises(self) -> None:
        from jarvis.tools import ToolError
        from jarvis.tools.browser import BrowserTool

        tool = BrowserTool()
        with pytest.raises(ToolError, match="Missing 'destination' parameter"):
            tool.execute(action="open_destination")

    def test_open_destination_empty_raises_tool_error(self) -> None:
        from jarvis.tools import ToolError
        from jarvis.tools.browser import BrowserTool

        tool = BrowserTool()
        with pytest.raises(ToolError, match="destination cannot be empty"):
            tool.open_destination("")
