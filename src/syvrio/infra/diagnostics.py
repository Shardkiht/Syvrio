from __future__ import annotations

import atexit
import json
import logging
import os
import platform
import re
import sys
import traceback
from datetime import datetime, timezone
from logging.handlers import QueueListener, RotatingFileHandler
from pathlib import Path
from queue import Full, Queue
from threading import RLock, current_thread

from .. import __version__
from .config import default_config_path


_EVENTS = frozenset({
    "app.start", "app.stop", "cli.failed", "tui.failed", "chat.failed",
    "search.failed", "catchup.failed", "session.failed", "session.reload_failed",
    "queue.failed", "usage.failed", "reflection.failed", "reading.changed",
    "generation.started", "generation.finished", "turn.unbound", "tui.finalize_failed",
    "session.scan_failed", "session.delete_failed",
    "command.failed", "cursor.changed", "undo.failed",
    "git_sync.failed", "git_sync.scheduler_failed", "git_sync.status_failed",
    "reflection.schedule_failed", "reflection.state_failed", "reflection.summary_failed",
})
_FIELDS = frozenset({
    "follow", "selecting", "selected", "grabbed", "scroll_y", "scroll_max",
    "streaming", "queued", "busy",
    "native", "suspended", "cursor_x", "cursor_y", "elapsed_ms",
})
_lock = RLock()
_listener: QueueListener | None = None
_handler: RotatingFileHandler | None = None
_queue: Queue[logging.LogRecord] | None = None
_path: Path | None = None


class _QuietFileHandler(RotatingFileHandler):
    def handleError(self, record: logging.LogRecord) -> None:
        # Logging must neither interrupt chat nor dump payloads onto MCP stdout.
        pass


def start_diagnostics() -> Path | None:
    """Start bounded, background-only diagnostics beside the default config."""
    global _listener, _handler, _queue, _path
    with _lock:
        if _listener is not None:
            return _path
        path = default_config_path().parent / "logs" / "syvrio.log"
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            handler = _QuietFileHandler(path, maxBytes=2 * 1024 * 1024,
                                        backupCount=3, encoding="utf-8")
        except OSError:
            print("Local diagnostics unavailable: cannot open log file.", file=sys.stderr)
            return None
        handler.setFormatter(logging.Formatter("%(message)s"))
        _queue = Queue(maxsize=1024)
        _handler = handler
        _listener = QueueListener(_queue, handler)
        _listener.start()
        _path = path
        record_event("app.start")
        return path


def stop_diagnostics() -> None:
    """Drain queued events before closing the file; safe to call repeatedly."""
    global _listener, _handler, _queue, _path
    with _lock:
        if _listener is None:
            return
        record_event("app.stop")
        # QueueListener.stop uses put_nowait for its sentinel: drain first so a
        # full queue cannot prevent shutdown. No producers enqueue under this lock.
        _queue.join()
        _listener.stop()
        _handler.close()
        _listener = _handler = _queue = _path = None


def _safe_traceback(error: BaseException) -> str:
    """Retain chained tracebacks and reasons, without locals or credentials."""
    detail = "".join(traceback.TracebackException.from_exception(error, capture_locals=False).format())
    for name, value in list(os.environ.items()):
        if re.search(r"(?:KEY|TOKEN|SECRET|PASSWORD)$", name, re.I) and len(value) >= 4:
            detail = detail.replace(value, "[REDACTED]")
    detail = re.sub(r"(?i)(bearer\s+)[^\s\"',}]+", r"\1[REDACTED]", detail)
    detail = re.sub(
        r"(?i)((?:api[_ -]?key|access[_ -]?token|secret|password|passwd|密码|口令|验证码|私钥)"
        r"[\"']?\s*(?:是|为|[:：=])\s*[\"']?)[^\s\"',;}]+",
        r"\1[REDACTED]", detail)
    detail = re.sub(r"\bsk-[A-Za-z0-9_-]{8,}", "[REDACTED]", detail)
    return detail[:32768]


def record_event(event: str, error: BaseException | None = None, **state: bool | int | float) -> None:
    """Only fixed event names and numeric UI state may cross the privacy boundary."""
    if event not in _EVENTS:
        return
    with _lock:
        if _queue is None:
            return
        payload = {
            "time": datetime.now(timezone.utc).isoformat(), "event": event,
            "pid": os.getpid(), "version": __version__, "platform": platform.system(),
            "python": platform.python_version(),
            "thread": current_thread().name, "level": "ERROR" if error is not None else "INFO",
            "state": {key: value for key, value in state.items()
                      if key in _FIELDS and type(value) in (bool, int, float)},
        }
        if error is not None:
            payload["traceback"] = _safe_traceback(error)
        record = logging.LogRecord("syvrio.diagnostics", logging.INFO, "", 0,
                                   json.dumps(payload, ensure_ascii=False), (), None)
        try:
            _queue.put_nowait(record)
        except Full:
            pass  # Slow disks must not block the UI; diagnostics are best effort.


atexit.register(stop_diagnostics)
