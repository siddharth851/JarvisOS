"""Tool Registry Adapter.

Bridges the planner output into the existing CommandRouter RoutingResult shape
(expected by ToolExecutor).
"""

from __future__ import annotations

from typing import Any

from jarvis.services.planner import PlannedCommand


class ToolRegistryAdapter:
    """Converts a PlannedCommand into RoutingResult compatible with ToolExecutor.

    Implemented with a local import to avoid circular imports with `command_router`.
    """

    def to_routing_result(self, planned: PlannedCommand):
        # Local import breaks circular dependency at module import time.
        from jarvis.services.command_router import RoutingResult

        if planned.type != "TOOL":
            return RoutingResult(type="CHAT")

        return RoutingResult(
            type="TOOL",
            tool=planned.tool,
            action=planned.action,
            arguments=planned.arguments or {},
        )
