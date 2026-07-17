"""Application Resolver Service.

Discovers installed applications and resolves a natural-language name
to the best matching installed application. Designed to be extensible
and platform-agnostic; discovery is configurable to make testing
deterministic.
"""
from __future__ import annotations

import os
import time
import re
from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import List, Optional


@dataclass
class ApplicationCandidate:
    resource_type: str
    display_name: str
    identifier: str
    confidence: float
    running_state: bool
    executable_path: Optional[str] = None


class ApplicationResolutionError(Exception):
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(message)
        self.details = details or {}


class ApplicationResolver:
    """Discover and resolve desktop applications.

    The resolver performs lightweight discovery of applications by
    scanning a list of filesystem paths for application bundles (macOS
    ``.app``) and executables. Matching is fuzzy and returns a
    confidence score in [0.0, 1.0].
    """

    DEFAULT_APP_DIRS = [
        "/Applications",
        os.path.expanduser("~/Applications"),
        "/usr/local/bin",
        "/usr/bin",
    ]

    _NORMALISE_RE = re.compile(r"[^a-z0-9]+")

    def __init__(self, discovery_paths: Optional[List[str]] = None):
        self._paths = discovery_paths or self.DEFAULT_APP_DIRS

    # ------------------ Discovery ---------------------------------
    def discover(self) -> List[dict]:
        """Return a list of discovered applications.

        Each entry is a dict with keys: display_name, identifier, executable_path.
        """
        apps: List[dict] = []
        for base in self._paths:
            if not base:
                continue
            if not os.path.exists(base):
                continue

            try:
                for entry in os.listdir(base):
                    full = os.path.join(base, entry)
                    # macOS .app bundles
                    if entry.lower().endswith(".app") and os.path.isdir(full):
                        display = entry[:-4]
                        apps.append({
                            "display_name": display,
                            "identifier": full,
                            "executable_path": full,
                        })
                    # executable files in bin paths
                    elif os.path.isfile(full) and os.access(full, os.X_OK):
                        display = os.path.basename(full)
                        apps.append({
                            "display_name": display,
                            "identifier": full,
                            "executable_path": full,
                        })
            except PermissionError:
                # skip unreadable directories
                continue

        return apps

    # ------------------ Matching ----------------------------------
    @classmethod
    def _normalise(cls, text: str) -> str:
        t = (text or "").lower().strip()
        # remove common command words
        for token in ("open", "launch", "start", "run", "please", "app", "application"):
            t = t.replace(token, " ")
        t = cls._NORMALISE_RE.sub(" ", t).strip()
        return t

    @staticmethod
    def _similarity(a: str, b: str) -> float:
        if not a or not b:
            return 0.0
        return SequenceMatcher(None, a, b).ratio()

    def resolve(self, name: str, min_confidence: float = 0.35) -> ApplicationCandidate:
        """Resolve a natural-language *name* to an installed application.

        Raises:
            ApplicationResolutionError: when no match meets the threshold.
        """
        start = time.time()
        if not (name or "").strip():
            raise ApplicationResolutionError("name cannot be empty")

        normalized = self._normalise(name)
        candidates = self.discover()
        if not candidates:
            raise ApplicationResolutionError("no applications discovered")

        best = None
        best_score = 0.0

        for c in candidates:
            cand_name = self._normalise(c.get("display_name", ""))
            # combine name similarity with path similarity
            name_score = self._similarity(normalized, cand_name)
            path_score = self._similarity(normalized, c.get("executable_path", "") or "")
            score = max(name_score, path_score)

            # boost exact matches
            if normalized == cand_name and normalized:
                score = max(score, 0.95)

            if score > best_score:
                best_score = score
                best = c

        if best is None or best_score < min_confidence:
            raise ApplicationResolutionError(
                "no suitable application match",
                details={"query": name, "best_score": best_score},
            )

        # naive running-state detection: check if executable path exists
        running = False
        exe = best.get("executable_path")
        # the resolver does not attempt to determine running state by process list;
        # ApplicationManager is responsible for run-state detection. Here we set False.

        candidate = ApplicationCandidate(
            resource_type="application",
            display_name=best.get("display_name"),
            identifier=best.get("identifier"),
            confidence=round(float(best_score), 3),
            running_state=running,
            executable_path=exe,
        )

        return candidate


# Module-level singleton
_default_resolver: Optional[ApplicationResolver] = None


def get_application_resolver() -> ApplicationResolver:
    """Return singleton ApplicationResolver instance."""
    global _default_resolver
    if _default_resolver is None:
        _default_resolver = ApplicationResolver()
    return _default_resolver
