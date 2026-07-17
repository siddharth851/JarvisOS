import os
import tempfile

from jarvis.services.application_resolver import ApplicationResolver, ApplicationResolutionError


def _make_app_bundle(base: str, name: str):
    path = os.path.join(base, f"{name}.app")
    os.makedirs(path, exist_ok=True)
    # create a dummy executable inside bundle for realism
    binpath = os.path.join(path, "Contents", "MacOS")
    os.makedirs(binpath, exist_ok=True)
    with open(os.path.join(binpath, name), "w") as f:
        f.write("#!/bin/sh\necho hi")
    return path


def test_discover_and_resolve_exact():
    with tempfile.TemporaryDirectory() as td:
        apps_dir = os.path.join(td, "Applications")
        os.makedirs(apps_dir)
        _make_app_bundle(apps_dir, "Calculator")

        resolver = ApplicationResolver(discovery_paths=[apps_dir])
        candidate = resolver.resolve("open calculator")

        assert candidate.display_name.lower() == "calculator"
        assert candidate.resource_type == "application"
        assert candidate.confidence >= 0.9


def test_fuzzy_match():
    with tempfile.TemporaryDirectory() as td:
        apps_dir = os.path.join(td, "Applications")
        os.makedirs(apps_dir)
        _make_app_bundle(apps_dir, "Notes")

        resolver = ApplicationResolver(discovery_paths=[apps_dir])
        cand = resolver.resolve("note")
        assert cand.display_name.lower() == "notes"
        assert cand.confidence > 0.3


def test_no_discovered_apps_raises():
    with tempfile.TemporaryDirectory() as td:
        resolver = ApplicationResolver(discovery_paths=[os.path.join(td, "empty")])
        try:
            resolver.resolve("something")
            assert False, "expected ApplicationResolutionError"
        except ApplicationResolutionError as exc:
            assert "no applications discovered" in str(exc) or exc.details
