"""Entity extraction from free-form text.

This module is intentionally lightweight and pattern-based.
It provides extracted entities/parameters for the planner.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ExtractedEntities:
    """Container for extracted entities/parameters."""

    entities: dict[str, Any]


class PatternEntityExtractor:
    """Extracts parameters dynamically based on intent hints.

    Notes:
      - No hardcoded filenames/commands/websites.
      - Uses regex to capture variable parts like URLs, paths, and commands.
    """

    def extract(self, message: str, intent_hint: str) -> ExtractedEntities:
        text = (message or "").strip()
        norm = re.sub(r"\s+", " ", text)

        # Browser automation: search_google — extract search query
        if intent_hint == "BROWSER_SEARCH_GOOGLE":
            query = self._extract_search_query(norm)
            return ExtractedEntities(entities={"query": query})

        # Browser automation: open_new_tab — optionally extract a URL
        if intent_hint == "BROWSER_OPEN_NEW_TAB":
            url = self._extract_url(norm)
            return ExtractedEntities(entities={"url": url or ""})

        # Browser automation: parameter-less actions
        for _no_param_intent in (
            "BROWSER_GO_BACK",
            "BROWSER_GO_FORWARD",
            "BROWSER_REFRESH",
            "BROWSER_CLOSE_TAB",
            "BROWSER_OPEN_FIRST_RESULT",
            "BROWSER_READ_PAGE",
            "BROWSER_GET_PAGE_TITLE",
            "BROWSER_GET_PAGE_TEXT",
            "BROWSER_SUMMARIZE_PAGE",
        ):
            if intent_hint == _no_param_intent:
                return ExtractedEntities(entities={})

        # Browser open_destination: resolve site name / domain / URL dynamically.
        if intent_hint == "BROWSER_OPEN_DESTINATION":
            destination = self._extract_destination(norm)
            return ExtractedEntities(entities={"destination": destination})

        # Browser open_url: try to capture an URL anywhere.
        if intent_hint == "BROWSER_OPEN_URL":
            url = self._extract_url(norm)
            if url:
                return ExtractedEntities(entities={"url": url})
            # Fallback: treat the remainder as a URL-ish target.
            # e.g., "open example.com" => url="https://example.com"
            remainder = self._strip_leading_verbs(norm)
            if remainder:
                maybe = remainder
                if not maybe.startswith("http://") and not maybe.startswith("https://"):
                    maybe = f"https://{maybe}"
                return ExtractedEntities(entities={"url": maybe})

        # Browser open_google: no parameter needed (tool will decide).
        if intent_hint == "BROWSER_OPEN_GOOGLE":
            return ExtractedEntities(entities={})

        # File: create folder <path>
        if intent_hint == "FILE_CREATE_FOLDER":
            # capture everything after folder/directory keyword
            path = self._after_keyword(norm, ["folder", "directory", "dir"])
            return ExtractedEntities(entities={"path": path})

        # File: create file <path>
        if intent_hint == "FILE_CREATE_FILE":
            # Expected: "create file <path>" or "make file <path>"
            # Extract everything after the first "file" keyword.
            m = re.search(r"\bfile\b\s*(.+)$", norm, flags=re.IGNORECASE)
            if not m:
                return ExtractedEntities(entities={"path": ""})
            path = m.group(1).strip()
            return ExtractedEntities(entities={"path": path})

        # File: write/read/delete/list
        if intent_hint == "FILE_WRITE_FILE":
            # Expected forms:
            # - "write file test.txt Hello Jarvis"
            # - "write file test.txt"
            # Extract first token after "file" as path, rest as content.
            # Note: avoid fragile whole-keyword parsing.
            after_file = self._after_keyword(norm, ["file"])
            if not after_file:
                return ExtractedEntities(entities={"path": "", "content": ""})

            parts = after_file.split(maxsplit=1)
            path = parts[0] if parts else ""
            content = parts[1] if len(parts) > 1 else ""
            return ExtractedEntities(entities={"path": path, "content": content})

        if intent_hint == "FILE_READ_FILE":
            path = self._after_keyword(norm, ["file"])
            return ExtractedEntities(entities={"path": path})

        if intent_hint == "FILE_DELETE_FILE":
            path = self._after_keyword(norm, ["file"])
            return ExtractedEntities(entities={"path": path})

        if intent_hint == "FILE_LIST_DIRECTORY":
            path = self._after_keyword(norm, ["directory", "folder"])
            return ExtractedEntities(entities={"path": path})

        # Terminal: run <command>
        if intent_hint == "TERMINAL_RUN":
            command = self._strip_terminal_prefix(norm)
            return ExtractedEntities(entities={"command": command})

        return ExtractedEntities(entities={})

    def _normalize_spaces(self, s: str) -> str:
        return re.sub(r"\s+", " ", s).strip()

    def _extract_url(self, text: str) -> str | None:
        # Basic URL extraction.
        m = re.search(r"(https?://[^\s]+)", text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
        # Bare domains like example.com
        m = re.search(r"\b([a-z0-9-]+\.[a-z]{2,})(/[^\s]*)?\b", text, flags=re.IGNORECASE)
        if m:
            host = m.group(1)
            return f"https://{host}"
        return None

    def _strip_leading_verbs(self, text: str) -> str:
        t = text.lower()
        # Handle multi-word nav phrases first.
        t = re.sub(r"^(go\s+to|navigate\s+to)\s+", "", t)
        t = re.sub(r"^(open|visit|launch)\s+", "", t).strip()
        return t or ""

    def _extract_destination(self, text: str) -> str:
        """Extract raw destination string for BROWSER_OPEN_DESTINATION intent.

        Returns the text after stripping navigation verbs.  The URLResolver
        will handle actual resolution (full URL / domain / site name / search).
        """
        # If there is already a full URL, return it verbatim.
        m = re.search(r"(https?://[^\s]+)", text, flags=re.IGNORECASE)
        if m:
            return m.group(1)
        # Otherwise strip nav verbs and return whatever remains.
        return self._strip_leading_verbs(text)

    def _after_keyword(self, text: str, keywords: list[str]) -> str:
        """Return text after the first occurrence of any keyword."""
        for kw in keywords:
            # match kw as a whole word
            m = re.search(rf"\b{re.escape(kw)}\b\s*(.+)$", text, flags=re.IGNORECASE)
            if m:
                return m.group(1).strip()
        return ""

    def _after_first_path(self, full: str, path: str) -> str:
        if not path:
            return ""
        # Remove everything up to and including the path occurrence
        # then treat remainder as content.
        idx = full.lower().find(path.lower())
        if idx == -1:
            return ""
        remainder = full[idx + len(path):]
        return remainder.strip()

    def _strip_terminal_prefix(self, text: str) -> str:
        # Remove common terminal prefixes.
        t = re.sub(r"^(run|execute|terminal)\s+", "", text.strip(), flags=re.IGNORECASE)
        return t.strip()

    def _extract_search_query(self, text: str) -> str:
        """Extract the meaningful search query from natural language."""
        t = self._normalize_spaces(text)
        t = t.rstrip("?.!").strip()

        # Strip polite / filler prefixes.
        t = re.sub(
            r"^(?:can you|could you|please|would you|i want to|i'd like to)\s+",
            "",
            t,
            flags=re.IGNORECASE,
        ).strip()

        # Compound: "open Google and search ChatGPT"
        compound = re.search(
            r"(?:open|go to|visit)\s+(?:google|the web)\s+and\s+search(?:\s+for)?\s+(.+)$",
            t,
            flags=re.IGNORECASE,
        )
        if compound:
            return compound.group(1).strip()

        # Ordered patterns — most specific first.
        patterns = [
            r"^search(?:\s+on)?\s+google(?:\s+for)?\s+(.+)$",
            r"^google\s+search(?:\s+for)?\s+(.+)$",
            r"^search(?:\s+for)?\s+(.+)$",
            r"^look up\s+(.+)$",
            r"^find\s+(.+)$",
        ]
        for pattern in patterns:
            match = re.match(pattern, t, flags=re.IGNORECASE)
            if match:
                query = match.group(1).strip()
                query = re.sub(r"\s+on\s+google$", "", query, flags=re.IGNORECASE).strip()
                return query

        # Fallback: strip known leading tokens in sequence.
        t = re.sub(r"^search\s+", "", t, flags=re.IGNORECASE).strip()
        t = re.sub(r"^(?:on\s+)?google\s+", "", t, flags=re.IGNORECASE).strip()
        t = re.sub(r"^for\s+", "", t, flags=re.IGNORECASE).strip()
        if t.lower() in {"search", "google", "for"}:
            return ""
        return t
