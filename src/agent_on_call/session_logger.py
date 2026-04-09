"""Session debug logger — structured log files for each call session.

Creates one .log file per session in .aoc/sessions/ with the format:
    [TIMESTAMP] [LEVEL] [COMPONENT] message

Supports log rotation: on session start, if >20 files exist in the
sessions directory, the oldest files are deleted.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

# Regex that matches the structured log format
LOG_FORMAT_RE = re.compile(
    r"^\[\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z\] \[\w+\] \[\w+\] .+"
)

DEFAULT_SESSION_DIR = os.path.join(".aoc", "sessions")
DEFAULT_MAX_FILES = 20


def rotate_session_logs(session_dir: str, max_files: int = DEFAULT_MAX_FILES) -> None:
    """Delete oldest log files if count exceeds max_files.

    Args:
        session_dir: Directory containing session log files.
        max_files: Maximum number of files to keep.
    """
    if not os.path.isdir(session_dir):
        return

    log_files = sorted(
        (f for f in os.listdir(session_dir) if f.endswith(".log")),
        key=lambda name: os.path.getmtime(os.path.join(session_dir, name)),
    )

    if len(log_files) <= max_files:
        return

    to_delete = log_files[: len(log_files) - max_files]
    for name in to_delete:
        path = os.path.join(session_dir, name)
        try:
            os.remove(path)
            logger.info("Rotated old session log: %s", path)
        except OSError as e:
            logger.warning("Failed to delete old session log %s: %s", path, e)


class SessionLogger:
    """Writes structured debug logs for a single session.

    Usage:
        slog = SessionLogger()
        slog.start("room-abc")
        slog.info("agent", "Agent connected")
        slog.info("data_channel", "Received message from user")
        slog.error("tts", "TTS synthesis failed")
        slog.close()
    """

    def __init__(self, session_dir: str = DEFAULT_SESSION_DIR):
        self._session_dir = session_dir
        self._file = None
        self._filepath: str | None = None
        self._closed = False

    @property
    def filepath(self) -> str | None:
        """Path to the current log file, or None if not started."""
        return self._filepath

    def start(self, session_id: str) -> str:
        """Start logging for a session.

        Creates the log file and writes a header entry.
        Also triggers log rotation.

        Args:
            session_id: Room/session identifier.

        Returns:
            Path to the created log file.
        """
        os.makedirs(self._session_dir, exist_ok=True)

        # Rotate before creating new file
        rotate_session_logs(self._session_dir)

        now = datetime.now(timezone.utc)
        filename = now.strftime("%Y-%m-%d-%H%M%S") + ".log"
        self._filepath = os.path.join(self._session_dir, filename)
        self._file = open(self._filepath, "w", encoding="utf-8")
        self._closed = False

        self._write_line("INFO", "session", f"Session started — room={session_id}")
        return self._filepath

    def _write_line(self, level: str, component: str, message: str) -> None:
        """Write a single structured log line."""
        if self._closed or self._file is None:
            return
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        line = f"[{ts}] [{level}] [{component}] {message}\n"
        self._file.write(line)
        self._file.flush()

    def log(self, level: str, component: str, message: str) -> None:
        """Write a log entry at the given level."""
        self._write_line(level, component, message)

    def debug(self, component: str, message: str) -> None:
        """Write a DEBUG-level log entry."""
        self._write_line("DEBUG", component, message)

    def info(self, component: str, message: str) -> None:
        """Write an INFO-level log entry."""
        self._write_line("INFO", component, message)

    def warn(self, component: str, message: str) -> None:
        """Write a WARN-level log entry."""
        self._write_line("WARN", component, message)

    def error(self, component: str, message: str) -> None:
        """Write an ERROR-level log entry."""
        self._write_line("ERROR", component, message)

    def close(self) -> None:
        """End the session and close the log file."""
        if self._closed:
            return
        self._write_line("INFO", "session", "Session ended")
        self._closed = True
        if self._file:
            self._file.close()
            self._file = None
