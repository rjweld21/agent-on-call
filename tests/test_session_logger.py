"""Tests for session_logger — structured debug log files per session."""

from __future__ import annotations

import os
import re

from agent_on_call.session_logger import SessionLogger, LOG_FORMAT_RE, rotate_session_logs


class TestSessionLogger:
    """Unit tests for SessionLogger."""

    def test_creates_log_file_on_start(self, tmp_path):
        """SessionLogger creates a .log file in the sessions directory."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room-123")

        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].suffix == ".log"
        logger.close()

    def test_log_file_name_format(self, tmp_path):
        """Log file name follows YYYY-MM-DD-HHMMSS.log pattern."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room")

        filename = os.path.basename(logger.filepath)
        # Pattern: 2026-04-08-153042.log
        assert re.match(r"\d{4}-\d{2}-\d{2}-\d{6}\.log", filename)
        logger.close()

    def test_log_entry_format(self, tmp_path):
        """Each log line matches [TIMESTAMP] [LEVEL] [COMPONENT] message."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room")
        logger.log("INFO", "agent", "Session started")
        logger.close()

        content = open(logger.filepath).read()
        lines = [line for line in content.strip().split("\n") if line.strip()]
        # Should have at least the "Session started" entry
        assert any("Session started" in line for line in lines)
        for line in lines:
            assert LOG_FORMAT_RE.match(line), f"Line doesn't match format: {line}"

    def test_log_levels(self, tmp_path):
        """Logger supports DEBUG, INFO, WARN, ERROR levels."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room")
        logger.debug("agent", "Debug message")
        logger.info("agent", "Info message")
        logger.warn("agent", "Warn message")
        logger.error("agent", "Error message")
        logger.close()

        content = open(logger.filepath).read()
        assert "[DEBUG]" in content
        assert "[INFO]" in content
        assert "[WARN]" in content
        assert "[ERROR]" in content

    def test_component_names(self, tmp_path):
        """Log entries include the component name."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room")
        logger.info("data_channel", "Message received")
        logger.info("tts", "Synthesis complete")
        logger.close()

        content = open(logger.filepath).read()
        assert "[data_channel]" in content
        assert "[tts]" in content

    def test_close_writes_footer(self, tmp_path):
        """Closing the logger writes a session-end entry."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room")
        logger.info("agent", "Something happened")
        logger.close()

        content = open(logger.filepath).read()
        assert "Session ended" in content

    def test_double_close_is_safe(self, tmp_path):
        """Calling close() twice doesn't raise."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room")
        logger.close()
        logger.close()  # Should not raise

    def test_log_after_close_is_ignored(self, tmp_path):
        """Writing after close doesn't raise or append."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("test-room")
        logger.close()
        content_after_close = open(logger.filepath).read()
        logger.info("agent", "Should be ignored")
        content_later = open(logger.filepath).read()
        assert content_after_close == content_later

    def test_session_id_logged(self, tmp_path):
        """The session/room ID appears in the log."""
        logger = SessionLogger(session_dir=str(tmp_path))
        logger.start("my-unique-room-42")
        logger.close()

        content = open(logger.filepath).read()
        assert "my-unique-room-42" in content

    def test_creates_directory_if_missing(self, tmp_path):
        """SessionLogger creates the session_dir if it doesn't exist."""
        nested = str(tmp_path / "deep" / "sessions")
        logger = SessionLogger(session_dir=nested)
        logger.start("test-room")
        logger.info("agent", "hello")
        logger.close()

        assert os.path.isfile(logger.filepath)


class TestLogRotation:
    """Tests for rotate_session_logs — delete oldest when >20 files."""

    def test_no_rotation_under_limit(self, tmp_path):
        """If <=20 files exist, nothing is deleted."""
        for i in range(15):
            (tmp_path / f"2026-01-01-{i:06d}.log").write_text("log")

        rotate_session_logs(str(tmp_path), max_files=20)
        assert len(list(tmp_path.glob("*.log"))) == 15

    def test_rotation_deletes_oldest(self, tmp_path):
        """If >20 files, oldest are deleted to bring count to 20."""
        for i in range(25):
            f = tmp_path / f"2026-01-{i + 1:02d}-120000.log"
            f.write_text(f"log {i}")
            # Set mtime so ordering is deterministic
            os.utime(f, (1000000 + i, 1000000 + i))

        rotate_session_logs(str(tmp_path), max_files=20)
        remaining = sorted(tmp_path.glob("*.log"))
        assert len(remaining) == 20
        # The 5 oldest should have been deleted (days 01-05)
        names = [f.name for f in remaining]
        assert "2026-01-01-120000.log" not in names
        assert "2026-01-05-120000.log" not in names
        assert "2026-01-06-120000.log" in names

    def test_rotation_with_empty_dir(self, tmp_path):
        """Rotation on empty dir doesn't raise."""
        rotate_session_logs(str(tmp_path), max_files=20)

    def test_rotation_with_nonexistent_dir(self, tmp_path):
        """Rotation with nonexistent dir doesn't raise."""
        rotate_session_logs(str(tmp_path / "nope"), max_files=20)
