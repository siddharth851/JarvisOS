"""AI OS command pipeline orchestration.

Intent detection -> Entity extraction -> Planner decision.
No tool execution happens here.
"""

from __future__ import annotations

from dataclasses import dataclass

from jarvis.services.entity_extraction import ExtractedEntities, PatternEntityExtractor
from jarvis.services.intent_detection import DetectedIntent, PatternIntentDetector
from jarvis.services.planner import CommandPlanner, PlannedCommand


@dataclass(frozen=True)
class PipelineResult:
    """Pipeline output: either CHAT or TOOL plan."""

    planned: PlannedCommand


class AIOSCommandPipeline:
    """Orchestrates detection/extraction/planning."""

    def __init__(
        self,
        intent_detector: PatternIntentDetector | None = None,
        entity_extractor: PatternEntityExtractor | None = None,
        planner: CommandPlanner | None = None,
    ) -> None:
        self._intent_detector = intent_detector or PatternIntentDetector()
        self._entity_extractor = entity_extractor or PatternEntityExtractor()
        self._planner = planner or CommandPlanner()

    def process(
        self,
        message: str,
        *,
        min_confidence: float = 0.75,
    ) -> PipelineResult:
        detected = self._intent_detector.detect(message)
        extracted: ExtractedEntities
        if detected is None:
            extracted = ExtractedEntities(entities={})
        else:
            extracted = self._entity_extractor.extract(message, detected.intent)

        planned = self._planner.plan(
            detected,
            extracted,
            min_confidence=min_confidence,
        )
        return PipelineResult(planned=planned)
