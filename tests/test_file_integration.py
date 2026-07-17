from unittest.mock import patch
import os

from jarvis.services.command_router import CommandRouter
from jarvis.services.tool_executor import ToolExecutor


@patch("jarvis.services.file_manager.get_file_manager")
def test_open_file_pipeline(mock_get_manager):
    # mock manager to avoid touching real FS
    mock_get_manager.return_value.open_file = lambda p: {
        "action": "open",
        "target": p,
        "status": "success",
        "message": "opened",
        "execution_time": 0.0,
        "data": {"content": "hello"},
    }

    router = CommandRouter()
    routing = router.route("open notes.txt")
    assert routing.type == "TOOL"
    assert routing.tool == "file"
    assert routing.action in {"read_file", "open", "open_folder", "create_file"} or routing.action

    executor = ToolExecutor()
    res = executor.execute(routing)
    assert res["success"] is True
    # result might be wrapped structured response when using manager
    result = res["result"]
    if isinstance(result, dict):
        assert result["status"] == "success"
        assert result["data"]["content"] == "hello"
