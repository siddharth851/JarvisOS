import subprocess

from jarvis.services.application_manager import ApplicationManager


class DummyCompleted:
    def __init__(self, returncode=0):
        self.returncode = returncode


def test_launch_app_calls_open(monkeypatch):
    manager = ApplicationManager()

    calls = {}

    def fake_run(cmd, check=True, **kwargs):
        calls['run'] = cmd
        return DummyCompleted(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    resp = manager.launch("/Applications/Calculator.app")
    assert resp['status'] == 'success'
    assert 'open' in calls['run']


def test_launch_executable_uses_popen(monkeypatch):
    manager = ApplicationManager()

    popen_calls = {}

    class DummyPopen:
        def __init__(self, cmd):
            popen_calls['cmd'] = cmd

    monkeypatch.setattr(subprocess, "Popen", DummyPopen)

    resp = manager.launch("/usr/local/bin/mytool")
    assert resp['status'] == 'success'
    assert popen_calls['cmd'][0].endswith('mytool')


def test_close_tries_osascript_then_pkill(monkeypatch):
    manager = ApplicationManager()

    calls = []

    def fake_run(cmd, check=True, **kwargs):
        calls.append(cmd)
        # first call (osascript) should fail
        if 'osascript' in cmd:
            raise subprocess.CalledProcessError(1, cmd)
        return DummyCompleted(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    resp = manager.close("/Applications/Fake.app")
    assert resp['status'] == 'success'
    # ensure pkill was invoked as fallback
    assert any('pkill' in c for c in calls)


def test_focus_calls_osascript(monkeypatch):
    manager = ApplicationManager()

    called = {}

    def fake_run(cmd, check=True, **kwargs):
        called['cmd'] = cmd
        return DummyCompleted(0)

    monkeypatch.setattr(subprocess, "run", fake_run)

    resp = manager.focus("/Applications/Calculator.app")
    assert resp['status'] == 'success'
    assert 'osascript' in called['cmd']


def test_is_running_true_and_false(monkeypatch):
    manager = ApplicationManager()

    def fake_run_true(cmd, check=False, capture_output=True):
        return DummyCompleted(0)

    def fake_run_false(cmd, check=False, capture_output=True):
        return DummyCompleted(1)

    monkeypatch.setattr(subprocess, "run", fake_run_true)
    assert manager.is_running("myapp") is True

    monkeypatch.setattr(subprocess, "run", fake_run_false)
    assert manager.is_running("myapp") is False
