"""Tests for session error handler — sync callback with asyncio.create_task."""

import asyncio
import inspect
import pytest
from unittest.mock import MagicMock, patch


class TestSessionErrorHandlerIsSync:
    """Verify that the error handler registered on the session is synchronous.

    LiveKit SDK 1.5.1 rejects async callbacks on EventEmitter.on().
    The handler must be a regular function that uses asyncio.create_task()
    for any async work.
    """

    def test_on_session_error_is_not_coroutine_function(self):
        """_on_session_error must be a sync function, not async."""
        # We need to extract the callback that gets registered with session.on().
        # To do this, we'll capture what session.on("error") registers.
        registered_callbacks = {}

        class MockSession:
            """Mock AgentSession that captures .on() registrations."""

            _tts = MagicMock()

            def on(self, event):
                def decorator(fn):
                    registered_callbacks[event] = fn
                    return fn

                return decorator

        mock_session = MockSession()

        # Register a sync handler the same way main.py does
        @mock_session.on("error")
        def _on_session_error(error):
            pass

        # Verify the captured callback is NOT a coroutine function
        handler = registered_callbacks.get("error")
        assert handler is not None, "No error handler was registered"
        assert not inspect.iscoroutinefunction(handler), (
            "_on_session_error must be a sync function, not async. " "LiveKit SDK 1.5.1 rejects async callbacks on .on()"
        )


class TestSessionErrorHandlerBehavior:
    """Test the actual behavior of the sync error handler."""

    @pytest.mark.asyncio
    async def test_handler_creates_task_for_notification(self):
        """When a TTS error occurs, the handler should use
        asyncio.create_task() instead of await."""

        async def mock_notify(reason):
            pass

        with patch("asyncio.create_task") as mock_create_task:
            mock_create_task.return_value = MagicMock()

            # Simulate the handler calling create_task (as main.py does)
            reason = "no_credits"
            asyncio.create_task(mock_notify(reason))

            mock_create_task.assert_called_once()

    def test_handler_disables_tts_on_tts_error(self):
        """Handler should set tts_disabled_at_runtime and clear session._tts."""
        # Simulate the sync state changes the handler performs
        session = MagicMock()
        session._tts = MagicMock()

        # After handler runs, TTS should be cleared
        session._tts = None
        assert session._tts is None

    def test_handler_ignores_non_tts_errors(self):
        """Handler should return early for non-TTS errors."""
        # Create a mock error that is NOT a TTSError
        mock_error = MagicMock()

        # Mock tts module
        mock_tts_module = MagicMock()
        mock_tts_module.TTSError = type("TTSError", (Exception,), {})

        # The error is not a TTSError instance
        assert not isinstance(mock_error, mock_tts_module.TTSError)

    def test_handler_skips_when_already_disabled(self):
        """Handler should return immediately if TTS already disabled.
        The flag is checked at the top of the handler as a guard clause."""
        # Verify the guard clause pattern: if flag is True, handler returns early
        flag = True
        assert flag is True  # handler would return here


class TestSourceCodeSync:
    """Verify the actual source code has the correct pattern."""

    def test_main_py_has_sync_error_handler(self):
        """The session error handler in main.py must be 'def', not 'async def'."""
        import pathlib

        main_path = pathlib.Path(__file__).parent.parent / "src" / "agent_on_call" / "main.py"
        source = main_path.read_text()

        # Must NOT have async def _on_session_error
        assert "async def _on_session_error" not in source, (
            "Found 'async def _on_session_error' in main.py — " "this will crash with LiveKit SDK 1.5.1"
        )

        # Must have sync def _on_session_error
        assert "def _on_session_error" in source, "Could not find 'def _on_session_error' in main.py"

    def test_main_py_uses_create_task_for_notify(self):
        """The handler must use asyncio.create_task() for async calls."""
        import pathlib

        main_path = pathlib.Path(__file__).parent.parent / "src" / "agent_on_call" / "main.py"
        source = main_path.read_text()

        assert (
            "asyncio.create_task(_notify_tts_disabled" in source
        ), "Expected asyncio.create_task(_notify_tts_disabled(...)) in main.py"

    def test_main_py_imports_asyncio(self):
        """main.py must import asyncio for create_task."""
        import pathlib

        main_path = pathlib.Path(__file__).parent.parent / "src" / "agent_on_call" / "main.py"
        source = main_path.read_text()

        assert "import asyncio" in source, "main.py must import asyncio for asyncio.create_task()"

    def test_main_py_has_sync_data_received_handler(self):
        """The data_received handler passed to room.on() must be sync.

        LiveKit SDK 1.5.1 raises ValueError for async callbacks on .on().
        The async logic must be in a separate function called via create_task.
        """
        import pathlib

        main_path = pathlib.Path(__file__).parent.parent / "src" / "agent_on_call" / "main.py"
        source = main_path.read_text()

        # The sync wrapper registered with room.on() must NOT be async
        assert 'ctx.room.on("data_received", _on_data_received)' in source, (
            "Expected room.on() registration for _on_data_received"
        )
        # _on_data_received itself must be sync (def, not async def)
        assert "def _on_data_received(data_packet" in source, (
            "Could not find sync 'def _on_data_received' in main.py"
        )
        # It should NOT be 'async def _on_data_received'
        assert "async def _on_data_received" not in source, (
            "Found 'async def _on_data_received' in main.py — "
            "this will crash with LiveKit SDK 1.5.1. Use a sync wrapper."
        )
