from jarvis.services.command_router import CommandRouter, RoutingResult


def test_router_chat_fallback() -> None:
    router = CommandRouter()
    
    # Conversational messages
    assert router.route("What is AI?").type == "CHAT"
    assert router.route("hello there").type == "CHAT"
    assert router.route("tell me a joke").type == "CHAT"

    # None/empty inputs
    assert router.route("").type == "CHAT"
    assert router.route(None).type == "CHAT"  # type: ignore[arg-type]


def test_router_browser_actions() -> None:
    router = CommandRouter()

    # Open Google
    res = router.route("Open Google")
    assert res.type == "TOOL"
    assert res.tool == "browser"
    assert res.action == "open_google"
    assert res.arguments == {}

    # Open Website
    res = router.route("open website https://example.com")
    assert res.type == "TOOL"
    assert res.tool == "browser"
    assert res.action == "open_url"
    assert res.arguments == {"url": "https://example.com"}

    # Open URL
    res = router.route("open url https://google.com")
    assert res.type == "TOOL"
    assert res.tool == "browser"
    assert res.action == "open_url"
    assert res.arguments == {"url": "https://google.com"}


def test_router_browser_search_actions() -> None:
    router = CommandRouter()

    res = router.route("Open Google and search ChatGPT")
    assert res.type == "TOOL"
    assert res.tool == "browser"
    assert res.action == "search_google"
    assert res.arguments == {"query": "ChatGPT"}

    res = router.route("Search latest AI news")
    assert res.type == "TOOL"
    assert res.action == "search_google"
    assert res.arguments == {"query": "latest AI news"}

    res = router.route("Can you search FastAPI tutorial?")
    assert res.type == "TOOL"
    assert res.action == "search_google"
    assert res.arguments == {"query": "FastAPI tutorial"}


def test_router_browser_navigation_actions() -> None:
    router = CommandRouter()

    res = router.route("go back")
    assert res.type == "TOOL"
    assert res.action == "go_back"
    assert res.arguments == {}

    res = router.route("go forward")
    assert res.type == "TOOL"
    assert res.action == "go_forward"

    res = router.route("refresh the page")
    assert res.type == "TOOL"
    assert res.action == "refresh"

    res = router.route("open first result")
    assert res.type == "TOOL"
    assert res.action == "open_first_result"

    res = router.route("open new tab")
    assert res.type == "TOOL"
    assert res.action == "open_new_tab"

    res = router.route("close the current tab")
    assert res.type == "TOOL"
    assert res.action == "close_tab"


def test_router_browser_page_reader_actions() -> None:
    router = CommandRouter()

    res = router.route("read the current page")
    assert res.type == "TOOL"
    assert res.action == "read_page"

    res = router.route("get the page title")
    assert res.type == "TOOL"
    assert res.action == "get_page_title"

    res = router.route("extract visible text from the page")
    assert res.type == "TOOL"
    assert res.action == "get_page_text"

    res = router.route("summarize the webpage")
    assert res.type == "TOOL"
    assert res.action == "summarize_page"


def test_router_file_actions() -> None:
    router = CommandRouter()

    # Create Folder
    res = router.route("create folder my_project")
    assert res.type == "TOOL"
    assert res.tool == "file"
    assert res.action == "create_folder"
    assert res.arguments == {"path": "my_project"}

    # Create File
    res = router.route("create file main.py")
    assert res.type == "TOOL"
    assert res.tool == "file"
    assert res.action == "create_file"
    assert res.arguments == {"path": "main.py"}

    # Read File
    res = router.route("read file main.py")
    assert res.type == "TOOL"
    assert res.tool == "file"
    assert res.action == "read_file"
    assert res.arguments == {"path": "main.py"}

    # Write File with content
    res = router.route("write file test.txt Hello Jarvis")
    assert res.type == "TOOL"
    assert res.tool == "file"
    assert res.action == "write_file"
    assert res.arguments == {"path": "test.txt", "content": "Hello Jarvis"}

    # Write File empty content
    res = router.route("write file test.txt")
    assert res.type == "TOOL"
    assert res.tool == "file"
    assert res.action == "write_file"
    assert res.arguments == {"path": "test.txt", "content": ""}

    # Delete File
    res = router.route("delete file temp.log")
    assert res.type == "TOOL"
    assert res.tool == "file"
    assert res.action == "delete_file"
    assert res.arguments == {"path": "temp.log"}

    # List Directory
    res = router.route("list directory src/jarvis")
    assert res.type == "TOOL"
    assert res.tool == "file"
    assert res.action == "list_directory"
    assert res.arguments == {"path": "src/jarvis"}


def test_router_terminal_actions() -> None:
    router = CommandRouter()

    # Run command
    res = router.route("run ls -la")
    assert res.type == "TOOL"
    assert res.tool == "terminal"
    assert res.action == "run"
    assert res.arguments == {"command": "ls -la"}

    # Execute command
    res = router.route("execute python -V")
    assert res.type == "TOOL"
    assert res.tool == "terminal"
    assert res.action == "run"
    assert res.arguments == {"command": "python -V"}

    # Terminal command
    res = router.route("terminal pwd")
    assert res.type == "TOOL"
    assert res.tool == "terminal"
    assert res.action == "run"
    assert res.arguments == {"command": "pwd"}


def test_router_prefix_matching_safety() -> None:
    router = CommandRouter()

    # Prefix match should not false positive match similar words
    # e.g. "running" contains "run" prefix but is not followed by a space
    assert router.route("running command").type == "CHAT"
    assert router.route("execute_all").type == "CHAT"
    assert router.route("terminal_velocity").type == "CHAT"
    assert router.route("create folder").type == "TOOL"  # complete match is allowed
