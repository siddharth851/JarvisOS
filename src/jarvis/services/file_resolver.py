"""File Resolver Service.

Discovers files and folders and resolves natural language names to the
best matching filesystem path with a confidence score.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional


@dataclass
class FileCandidate:
    resource_type: str  # 'file' or 'folder'
    display_name: str
    identifier: str  # absolute path
    confidence: float
    executable_path: Optional[str] = None


class FileResolutionError(Exception):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details or {}


class FileResolver:
    DEFAULT_SEARCH_PATHS = [
        os.getcwd(),
        os.path.expanduser("~"),
        os.path.join(os.path.expanduser("~"), "Downloads"),
        os.path.join(os.path.expanduser("~"), "Documents"),
    ]

    _NORMALISE_RE = re.compile(r"[^a-z0-9]+")

    def __init__(self, search_paths: Optional[List[str]] = None):
        self._paths = [p for p in (search_paths or self.DEFAULT_SEARCH_PATHS) if p]

    def discover(self) -> List[dict]:
        """Discover files and folders under configured search paths.

        Returns a list of dicts with display_name and identifier (abs path).
        """
        items: List[dict] = []
        seen = set()
        for base in self._paths:
            if not os.path.exists(base):
                continue
            for root, dirs, files in os.walk(base):
                # include directories
                for d in dirs:
                    path = os.path.join(root, d)
                    key = os.path.abspath(path)
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append({
                        "display_name": d,
                        "identifier": key,
                        "type": "folder",
                    })
                for f in files:
                    path = os.path.join(root, f)
                    key = os.path.abspath(path)
                    if key in seen:
                        continue
                    seen.add(key)
                    items.append({
                        "display_name": f,
                        "identifier": key,
                        "type": "file",
                    })
        return items

    @classmethod
    def _normalise(cls, s: str) -> str:
        t = (s or "").lower().strip()
        t = re.sub(r"\b(open|please|the|a|an|file|folder|directory)\b", " ", t)
        t = cls._NORMALISE_RE.sub(" ", t).strip()
        return t

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def resolve(self, name: str, min_confidence: float = 0.35) -> FileCandidate:
        if not (name or "").strip():
            raise FileResolutionError("name cannot be empty")

        norm = self._normalise(name)
        candidates = self.discover()
        if not candidates:
            raise FileResolutionError("no suitable file match", details={"query": name, "best_score": 0.0})

        best = None
        best_score = 0.0
        for c in candidates:
            cand = self._normalise(c.get("display_name", ""))
            name_score = self._similarity(norm, cand)
            path_score = self._similarity(norm, c.get("identifier", ""))
            score = max(name_score, path_score)
            if norm == cand and norm:
                score = max(score, 0.99)
            if score > best_score:
                best_score = score
                best = c

        if best is None or best_score < min_confidence:
            raise FileResolutionError("no suitable file match", details={"query": name, "best_score": best_score})

        cand = FileCandidate(
            resource_type=best.get("type", "file"),
            display_name=best.get("display_name"),
            identifier=best.get("identifier"),
            confidence=round(float(best_score), 3),
            executable_path=best.get("identifier"),
        )
        return cand


# singleton
_default: Optional[FileResolver] = None


def get_file_resolver() -> FileResolver:
    global _default
    if _default is None:
        _default = FileResolver()
    return _default
