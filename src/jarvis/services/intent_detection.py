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

        # Tool: browser automation — specific actions checked BEFORE generic open/search

        # Page reading / content extraction
        if re.search(r"\b(summarize|summarise)\b", norm) and re.search(
            r"\b(page|website|site|webpage)\b", norm
        ):
            return DetectedIntent(intent="BROWSER_SUMMARIZE_PAGE", confidence=0.95, hint=text)

        if re.search(r"\bread\b", norm) and re.search(
            r"\b(page|website|site|webpage|current)\b", norm
        ):
            return DetectedIntent(intent="BROWSER_READ_PAGE", confidence=0.9, hint=text)

        if re.search(r"\b(extract|get|show|what.?s)\b", norm) and re.search(
            r"\b(title)\b", norm
        ):
            return DetectedIntent(intent="BROWSER_GET_PAGE_TITLE", confidence=0.9, hint=text)

        if re.search(r"\b(extract|get|show)\b", norm) and re.search(
            r"\b(text|content|visible)\b", norm
        ) and re.search(r"\b(page|website|site)\b", norm):
            return DetectedIntent(intent="BROWSER_GET_PAGE_TEXT", confidence=0.9, hint=text)

        # Navigation controls
        if re.search(r"\bgo\s+back\b", norm) or re.search(r"\bnavigate\s+back\b", norm):
            return DetectedIntent(intent="BROWSER_GO_BACK", confidence=0.97)

        if re.search(r"\bgo\s+forward\b", norm) or re.search(r"\bnavigate\s+forward\b", norm):
            return DetectedIntent(intent="BROWSER_GO_FORWARD", confidence=0.97)

        if re.search(r"\b(refresh|reload)\b", norm) and re.search(
            r"\b(page|browser|tab|site)\b", norm
        ):
            return DetectedIntent(intent="BROWSER_REFRESH", confidence=0.95)

        if re.search(r"\bopen\s+(a\s+)?new\s+tab\b", norm) or re.search(
            r"\bnew\s+tab\b", norm
        ):
            return DetectedIntent(intent="BROWSER_OPEN_NEW_TAB", confidence=0.95, hint=text)

        if re.search(r"\bclose\s+(the\s+)?(current\s+)?tab\b", norm):
            return DetectedIntent(intent="BROWSER_CLOSE_TAB", confidence=0.95)

        # First search result
        if re.search(r"\b(open|click|visit)\b", norm) and re.search(
            r"\b(first|top)\b", norm
        ) and re.search(r"\b(result|link)\b", norm):
            return DetectedIntent(intent="BROWSER_OPEN_FIRST_RESULT", confidence=0.95)

        # Compound: "open Google and search X"
        if re.search(r"\b(open|go to|visit)\b", norm) and re.search(
            r"\bgoogle\b", norm
        ) and re.search(r"\band\s+search\b", norm):
            return DetectedIntent(intent="BROWSER_SEARCH_GOOGLE", confidence=0.95, hint=text)

        # Google search — explicit patterns
        if re.search(r"\bsearch\b", norm) and re.search(
            r"\b(google|for|on)\b", norm
        ):
            return DetectedIntent(intent="BROWSER_SEARCH_GOOGLE", confidence=0.9, hint=text)

        if re.search(r"\bsearch(?:\s+for)?\s+\S", norm):
            return DetectedIntent(intent="BROWSER_SEARCH_GOOGLE", confidence=0.9, hint=text)

        if re.search(r"\b(look up|find)\b", norm):
            return DetectedIntent(intent="BROWSER_SEARCH_GOOGLE", confidence=0.85, hint=text)

        if re.search(r"\b(search)\b", norm):
            return DetectedIntent(intent="BROWSER_SEARCH_GOOGLE", confidence=0.7, hint=text)

        # (duplicate removed; handled earlier)

        # Application lifecycle commands
        if re.search(r"\b(open|launch|start)\b", norm) and not re.search(
            r"\b(website|site|url|webpage|browser|search|google|file|folder|directory|tab|page)\b",
            norm,
        ) and not re.search(r"\.(?:txt|pdf|docx|md|csv|json|pptx|xlsx)\b", norm):
            return DetectedIntent(intent="APP_LAUNCH", confidence=0.9, hint=text)

        if re.search(r"\b(close|quit|exit)\b", norm) and not re.search(
            r"\b(tab|page|browser|window|site|website)\b",
            norm,
        ):
            return DetectedIntent(intent="APP_CLOSE", confidence=0.9, hint=text)

        if re.search(r"\bfocus\b", norm) and not re.search(
            r"\b(tab|page|browser|window|site|website)\b",
            norm,
        ):
            return DetectedIntent(intent="APP_FOCUS", confidence=0.9, hint=text)

        # Generic open/navigate
        if re.search(r"\b(go\s+to|navigate\s+to)\b", norm):
            return DetectedIntent(intent="BROWSER_OPEN_DESTINATION", confidence=0.95, hint=text)

        if re.search(r"\b(open|visit|launch)\b", norm) and not re.search(r"\.(?:txt|pdf|docx|md|csv|json|pptx|xlsx)\b", norm):
            if re.fullmatch(r"(open|visit|launch)\s+google", norm.strip()):
                return DetectedIntent(intent="BROWSER_OPEN_GOOGLE", confidence=0.95)

            if re.search(r"\bopen\s+(website|url)\b", norm):
                return DetectedIntent(intent="BROWSER_OPEN_URL", confidence=0.9, hint=text)

            return DetectedIntent(intent="BROWSER_OPEN_DESTINATION", confidence=0.85, hint=text)

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

        # File system commands without explicit 'file' token, e.g. "open Resume.pdf"
        if re.search(r"\b(open|create|make|delete|remove|rename|move|copy|quit)\b", norm) and re.search(r"\w+\.(?:txt|pdf|docx|md|csv|json|pptx|xlsx)\b", norm):
            # prefer specific file actions
            if re.search(r"\brename\b", norm):
                return DetectedIntent(intent="FILE_RENAME", confidence=0.95, hint=text)
            if re.search(r"\b(move)\b", norm):
                return DetectedIntent(intent="FILE_MOVE", confidence=0.95, hint=text)
            if re.search(r"\b(copy)\b", norm):
                return DetectedIntent(intent="FILE_COPY", confidence=0.95, hint=text)
            if re.search(r"\b(delete|remove)\b", norm):
                return DetectedIntent(intent="FILE_DELETE_FILE", confidence=0.95, hint=text)
            if re.search(r"\b(create|make)\b", norm):
                return DetectedIntent(intent="FILE_CREATE_FILE", confidence=0.9, hint=text)
            # fallback to open/read
            return DetectedIntent(intent="FILE_READ_FILE", confidence=0.9, hint=text)

        # Open folders like 'open Downloads' or 'open Documents'
        if re.search(r"\b(open|show)\b", norm) and re.search(r"\b(documents|downloads|desktop|pictures|music|videos)\b", norm):
            return DetectedIntent(intent="FILE_OPEN_FOLDER", confidence=0.9, hint=text)

        return None

    def _normalize(self, text: str) -> str:
        # Lowercase, collapse whitespace
        return re.sub(r"\s+", " ", text.lower()).strip()
