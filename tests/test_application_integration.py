from unittest.mock import patch

from jarvis.services.command_router import CommandRouter
from jarvis.services.tool_executor import ToolExecutor
from jarvis.services.application_resolver import ApplicationCandidate


def _make_candidate() -> ApplicationCandidate:
    return ApplicationCandidate(
        resource_type="application",
        display_name="Calculator",
        identifier="/Applications/Calculator.app",
        confidence=0.95,
        running_state=False,
        executable_path="/Applications/Calculator.app",
    )


@patch("jarvis.services.application_manager.get_application_manager")
@patch("jarvis.services.application_resolver.get_application_resolver")
def test_application_launch_full_flow(mock_get_resolver, mock_get_manager):
    candidate = _make_candidate()
    mock_get_resolver.return_value.resolve = lambda application: candidate
    mock_get_manager.return_value.launch = lambda identifier: {
        "action": "launch",
        "target": identifier,
        "status": "success",
        "message": "launched",
        "execution_time": 0.0,
        "data": {},
    }

    router = CommandRouter()
    routing = router.route("open calculator")
    assert routing.type == "TOOL"
    assert routing.tool == "application"
    assert routing.action == "launch"
    assert routing.arguments["application"] == "calculator"

    executor = ToolExecutor()
    result = executor.execute(routing)

    assert result["success"] is True
    assert result["tool"] == "application"
    assert result["result"]["status"] == "success"
    assert result["result"]["data"]["resolved_application"]["display_name"] == "Calculator"


@patch("jarvis.services.application_manager.get_application_manager")
@patch("jarvis.services.application_resolver.get_application_resolver")
def test_application_close_full_flow(mock_get_resolver, mock_get_manager):
    candidate = _make_candidate()
    mock_get_resolver.return_value.resolve = lambda application: candidate
    mock_get_manager.return_value.close = lambda identifier: {
        "action": "close",
        "target": identifier,
        "status": "success",
        "message": "closed",
        "execution_time": 0.0,
        "data": {},
    }

    router = CommandRouter()
    routing = router.route("quit calculator")
    assert routing.type == "TOOL"
    assert routing.action == "close"

    executor = ToolExecutor()
    result = executor.execute(routing)

    assert result["success"] is True
    assert result["result"]["action"] == "close"
    assert result["result"]["target"] == "/Applications/Calculator.app"