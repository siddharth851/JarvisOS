import os
import tempfile

from jarvis.services.file_resolver import FileResolver, FileResolutionError


def test_discover_and_resolve_file():
    with tempfile.TemporaryDirectory() as td:
        fpath = os.path.join(td, "resume.pdf")
        with open(fpath, "w") as f:
            f.write("dummy")

        resolver = FileResolver(search_paths=[td])
        cand = resolver.resolve("resume.pdf")
        assert cand.display_name == "resume.pdf"
        assert cand.identifier.endswith("resume.pdf")
        assert cand.confidence >= 0.9


def test_fuzzy_match():
    with tempfile.TemporaryDirectory() as td:
        os.makedirs(os.path.join(td, "Projects"))
        resolver = FileResolver(search_paths=[td])
        cand = resolver.resolve("project")
        assert cand.display_name.lower().startswith("projects")


def test_no_match_raises():
    with tempfile.TemporaryDirectory() as td:
        resolver = FileResolver(search_paths=[td])
        try:
            resolver.resolve("missingfile.txt")
            assert False, "expected FileResolutionError"
        except FileResolutionError as exc:
            assert "no suitable" in str(exc) or exc.details
