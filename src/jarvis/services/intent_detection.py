"""Intent detection (pattern-based, confidence-scored)."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DetectedIntent:
    """Result of intent detection."""

    intent: str
    confidence: float
    # free-form extracted hint; used by entity extraction
    hint: Optional[str] = None


class PatternIntentDetector:
    """Detects intents using regex, normalization and token-based heuristics."""

    def detect(self, message: str) -> DetectedIntent | None:
        if not message or not isinstance(message, str):
            return None

        text = message.strip()
        norm = self._normalize(text)

        # Tool: browser
        if re.search(r"\b(go\s+to|navigate\s+to)\b", norm):
            # "go to GitHub", "navigate to reddit.com"
            return DetectedIntent(intent="BROWSER_OPEN_DESTINATION", confidence=0.95, hint=text)

        if re.search(r"\b(open|visit|launch)\b", norm):
            # "open google" intent should only trigger when no URL/domain is present.
            if re.fullmatch(r"(open|visit|launch)\s+google", norm.strip()):
                return DetectedIntent(intent="BROWSER_OPEN_GOOGLE", confidence=0.95)

            # "open website <url>" or "open url <url>"
            if re.search(r"\bopen\s+(website|url)\b", norm):
                return DetectedIntent(intent="BROWSER_OPEN_URL", confidence=0.9, hint=text)

            # If user says "open <something>" treat as open_destination
            # (the resolver will handle URL, domain, or site-name lookup).
            return DetectedIntent(intent="BROWSER_OPEN_DESTINATION", confidence=0.85, hint=text)

        if re.search(r"\b(search)\b", norm):
            # future: map to browser search tool
            return DetectedIntent(intent="BROWSER_SEARCH", confidence=0.6, hint=text)

        # Tool: file system
        if re.search(r"\b(create|make)\b", norm):
            # Precedence: if it's clearly about "file", prefer create_file.
            if re.search(r"\bfile\b", norm):
                return DetectedIntent(intent="FILE_CREATE_FILE", confidence=0.85, hint=text)

            # Otherwise, only treat as folder creation if folder/directory is explicit.
            if re.search(r"\bfolder|directory\b", norm):
                return DetectedIntent(intent="FILE_CREATE_FOLDER", confidence=0.8, hint=text)

        if re.search(r"\b(write|update|append)\b", norm) and re.search(r"\bfile\b", norm):
            return DetectedIntent(intent="FILE_WRITE_FILE", confidence=0.85, hint=text)

        if re.search(r"\b(read|open)\b", norm) and re.search(r"\bfile\b", norm):
            return DetectedIntent(intent="FILE_READ_FILE", confidence=0.75, hint=text)

        if re.search(r"\b(delete|remove)\b", norm) and re.search(r"\bfile\b", norm):
            return DetectedIntent(intent="FILE_DELETE_FILE", confidence=0.75, hint=text)

        # Explicit: "list directory <path>" / "list folder <path>"
        if re.search(r"\blist\s+(directory|folder)\b", norm):
            return DetectedIntent(intent="FILE_LIST_DIRECTORY", confidence=0.9, hint=text)

        # Tool: terminal
        if re.search(r"\b(run|execute|terminal)\b", norm):
            return DetectedIntent(intent="TERMINAL_RUN", confidence=0.9, hint=text)

        return None

    def _normalize(self, text: str) -> str:
        # Lowercase, collapse whitespace
        return re.sub(r"\s+", " ", text.lower()).strip()
