from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from quiet_memo.infra import diagnostics

pytestmark = pytest.mark.config


@pytest.fixture(autouse=True)
def close_diagnostics():
    diagnostics.stop_diagnostics()
    yield
    diagnostics.stop_diagnostics()


def read_events(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_chained_error_retains_traceback_and_reason_without_credentials(tmp_path, monkeypatch):
    monkeypatch.setenv("EXAMPLE_API_KEY", "synthetic-credential-123")
    path = diagnostics.start_diagnostics()
    assert path == tmp_path / "logs" / "quiet-memo.log"
    assert diagnostics.start_diagnostics() == path
    try:
        try:
            raise ValueError("api_key=synthetic-inline-456 bearer synthetic-auth-789")
        except ValueError as cause:
            raise RuntimeError("Request failed: synthetic-credential-123") from cause
    except RuntimeError as error:
        diagnostics.record_event("chat.failed", error, busy=True, queued=2,
                                 content="private conversation", follow="private memory")
    diagnostics.stop_diagnostics()
    events = read_events(path)
    assert [event["event"] for event in events] == ["app.start", "chat.failed", "app.stop"]
    detail = events[1]["traceback"]
    assert "ValueError" in detail and "RuntimeError" in detail
    assert "Request failed" in detail and "test_chained_error" in detail
    assert "synthetic-credential-123" not in detail
    assert "synthetic-inline-456" not in detail
    assert "synthetic-auth-789" not in detail
    assert events[1]["state"] == {"busy": True, "queued": 2}
    assert "private conversation" not in path.read_text(encoding="utf-8")


def test_rotation_limits_files_and_keeps_valid_json(tmp_path, monkeypatch):
    path = diagnostics.start_diagnostics()
    diagnostics._handler.maxBytes = 800
    for _ in range(40):
        diagnostics.record_event("reading.changed", follow=False, scroll_y=20)
    diagnostics.stop_diagnostics()
    files = list(path.parent.glob("quiet-memo.log*"))
    assert len(files) == 4
    assert all(file.stat().st_size < 800 for file in files)
    assert all(read_events(file) for file in files)
    assert read_events(path)[-1]["event"] == "app.stop"


def test_threaded_events_drain_at_shutdown():
    path = diagnostics.start_diagnostics()
    with ThreadPoolExecutor(max_workers=4) as pool:
        list(pool.map(lambda _: diagnostics.record_event("chat.failed"), range(100)))
    diagnostics.stop_diagnostics()
    assert len(read_events(path)) == 102


def test_unavailable_file_does_not_break_application(monkeypatch):
    def denied(*args, **kwargs):
        raise PermissionError("synthetic denial")

    monkeypatch.setattr(diagnostics, "_QuietFileHandler", denied)
    assert diagnostics.start_diagnostics() is None
    diagnostics.record_event("chat.failed", RuntimeError("ignored"))
    diagnostics.stop_diagnostics()


def test_unknown_events_and_unconfigured_logging_are_ignored():
    diagnostics.record_event("chat.failed")
    path = diagnostics.start_diagnostics()
    diagnostics.record_event("arbitrary user text")
    diagnostics.stop_diagnostics()
    assert len(read_events(path)) == 2


def test_full_queue_does_not_block_producer(monkeypatch):
    from queue import Full

    path = diagnostics.start_diagnostics()

    def full(*args, **kwargs):
        raise Full

    with monkeypatch.context() as patch:
        patch.setattr(diagnostics._queue, "put_nowait", full)
        diagnostics.record_event("reading.changed", follow=False)
    diagnostics.stop_diagnostics()
    assert len(read_events(path)) == 2


def test_cli_entrypoint_logs_unhandled_error(monkeypatch):
    from quiet_memo.app import cli

    def fail():
        raise RuntimeError("synthetic command failure")

    monkeypatch.setattr(cli, "app", fail)
    with pytest.raises(RuntimeError, match="synthetic command failure"):
        cli.main()
    path = diagnostics.default_config_path().parent / "logs" / "quiet-memo.log"
    events = read_events(path)
    assert [event["event"] for event in events] == ["app.start", "cli.failed", "app.stop"]
    assert "synthetic command failure" in events[1]["traceback"]
