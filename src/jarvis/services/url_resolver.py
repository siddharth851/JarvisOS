"""URL Resolver Service.

Resolves a raw destination string (URL, domain, website name, or natural
language phrase) into a fully-qualified ``https://`` URL.

Resolution priority
-------------------
1. Full URL  (already has http:// or https:// scheme)
2. Bare domain  (e.g. ``github.com``, ``reddit.com``)
3. Known website name  (e.g. "GitHub", "Reddit", "ChatGPT")
4. Google search fallback  (e.g. ``https://www.google.com/search?q=…``)

The resolver is intentionally decoupled from the BrowserTool so that new
destination mappings can be added here without touching any other module.
"""

from __future__ import annotations

import re
from urllib.parse import quote_plus


# ---------------------------------------------------------------------------
# Well-known website name → canonical URL mapping.
# Add new entries here to extend coverage.  Keys are lower-cased for matching.
# ---------------------------------------------------------------------------
_KNOWN_SITES: dict[str, str] = {
    # Search / AI
    "google": "https://www.google.com",
    "bing": "https://www.bing.com",
    "duckduckgo": "https://duckduckgo.com",
    "chatgpt": "https://chat.openai.com",
    "openai": "https://openai.com",
    "claude": "https://claude.ai",
    "gemini": "https://gemini.google.com",
    "perplexity": "https://www.perplexity.ai",
    # Social / community
    "reddit": "https://www.reddit.com",
    "twitter": "https://twitter.com",
    "x": "https://x.com",
    "facebook": "https://www.facebook.com",
    "instagram": "https://www.instagram.com",
    "linkedin": "https://www.linkedin.com",
    "tiktok": "https://www.tiktok.com",
    "pinterest": "https://www.pinterest.com",
    "snapchat": "https://www.snapchat.com",
    "discord": "https://discord.com",
    "slack": "https://slack.com",
    "telegram": "https://web.telegram.org",
    "whatsapp": "https://web.whatsapp.com",
    # Developer / tech
    "github": "https://github.com",
    "gitlab": "https://gitlab.com",
    "bitbucket": "https://bitbucket.org",
    "stackoverflow": "https://stackoverflow.com",
    "stack overflow": "https://stackoverflow.com",
    "npm": "https://www.npmjs.com",
    "pypi": "https://pypi.org",
    "docker": "https://hub.docker.com",
    "jira": "https://www.atlassian.com/software/jira",
    "confluence": "https://www.atlassian.com/software/confluence",
    "notion": "https://www.notion.so",
    "figma": "https://www.figma.com",
    "vercel": "https://vercel.com",
    "netlify": "https://www.netlify.com",
    "heroku": "https://www.heroku.com",
    # Design / creativity
    "canva": "https://www.canva.com",
    "adobe": "https://www.adobe.com",
    "dribbble": "https://dribbble.com",
    "behance": "https://www.behance.net",
    "unsplash": "https://unsplash.com",
    "pexels": "https://www.pexels.com",
    # Productivity / cloud
    "gmail": "https://mail.google.com",
    "outlook": "https://outlook.live.com",
    "calendar": "https://calendar.google.com",
    "drive": "https://drive.google.com",
    "google drive": "https://drive.google.com",
    "dropbox": "https://www.dropbox.com",
    "onedrive": "https://onedrive.live.com",
    "trello": "https://trello.com",
    "asana": "https://app.asana.com",
    "airtable": "https://airtable.com",
    "linear": "https://linear.app",
    "monday": "https://monday.com",
    # Video / streaming
    "youtube": "https://www.youtube.com",
    "twitch": "https://www.twitch.tv",
    "netflix": "https://www.netflix.com",
    "spotify": "https://open.spotify.com",
    "vimeo": "https://vimeo.com",
    # E-commerce / finance
    "amazon": "https://www.amazon.com",
    "ebay": "https://www.ebay.com",
    "shopify": "https://www.shopify.com",
    "paypal": "https://www.paypal.com",
    # News / reference
    "wikipedia": "https://www.wikipedia.org",
    "medium": "https://medium.com",
    "hackernews": "https://news.ycombinator.com",
    "hacker news": "https://news.ycombinator.com",
    "hn": "https://news.ycombinator.com",
    "bbc": "https://www.bbc.com",
    "cnn": "https://www.cnn.com",
}

# Regex: bare domain like "github.com" or "sub.example.co.uk"
_DOMAIN_RE = re.compile(
    r"^(?:[a-z0-9](?:[a-z0-9\-]{0,61}[a-z0-9])?\.)+[a-z]{2,}$",
    re.IGNORECASE,
)


class URLResolver:
    """Resolves a raw destination string to a fully-qualified URL.

    The resolver is stateless and can be used as a singleton.  Extend
    ``_KNOWN_SITES`` to add new website → URL mappings without changing
    this class or the BrowserTool.
    """

    def resolve(self, destination: str) -> str:
        """Resolve *destination* to a fully-qualified URL.

        Args:
            destination: Raw string from user input, e.g. ``"GitHub"``,
                         ``"github.com"``, ``"https://github.com"``, or
                         ``"open GitHub in my browser"``.

        Returns:
            A fully-qualified ``http://`` or ``https://`` URL.

        Raises:
            ValueError: If *destination* is empty or whitespace-only.
        """
        raw = (destination or "").strip()
        if not raw:
            raise ValueError("destination cannot be empty")

        # 1. Already a full URL.
        if raw.startswith("http://") or raw.startswith("https://"):
            return raw

        # 2. Bare domain (e.g. "github.com").
        if _DOMAIN_RE.match(raw):
            return f"https://{raw}"

        # 3. Known website name — normalise to lower-case for lookup.
        normalised = raw.lower().strip()
        if normalised in _KNOWN_SITES:
            return _KNOWN_SITES[normalised]

        # 4. Google search fallback.
        return f"https://www.google.com/search?q={quote_plus(raw)}"


# ---------------------------------------------------------------------------
# Module-level singleton (avoids re-instantiation on every call).
# ---------------------------------------------------------------------------
_default_resolver = URLResolver()


def get_url_resolver() -> URLResolver:
    """Return the default :class:`URLResolver` singleton."""
    return _default_resolver
