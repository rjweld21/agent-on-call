"""Tests for main.py — TTS health check and session builder."""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestCheckTtsAvailable:
    def test_returns_false_no_key_when_env_not_set(self):
        from agent_on_call.main import _check_tts_available

        # Ensure CARTESIA_API_KEY is not present
        env_copy = os.environ.copy()
        env_copy.pop("CARTESIA_API_KEY", None)
        with patch.dict(os.environ, env_copy, clear=True):
            available, reason = _check_tts_available()
            assert available is False
            assert reason == "no_key"

    def test_returns_false_no_key_when_empty_string(self):
        with patch.dict(os.environ, {"CARTESIA_API_KEY": ""}, clear=False):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "no_key"

    def test_returns_false_no_key_for_placeholder(self):
        with patch.dict(os.environ, {"CARTESIA_API_KEY": "placeholder"}, clear=False):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "no_key"

    def test_returns_true_when_key_set(self):
        with patch.dict(
            os.environ, {"CARTESIA_API_KEY": "sk_cart_real_key_123"}, clear=False
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is True
            assert reason == ""

    def test_returns_false_for_whitespace_only_key(self):
        with patch.dict(os.environ, {"CARTESIA_API_KEY": "   "}, clear=False):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "no_key"


class TestBuildSession:
    def test_build_session_with_tts_enabled(self):
        with patch("agent_on_call.main.deepgram") as mock_dg, \
             patch("agent_on_call.main.cartesia") as mock_cart, \
             patch("agent_on_call.main.silero") as mock_silero, \
             patch("agent_on_call.main._build_llm") as mock_llm:
            mock_silero.VAD.load.return_value = MagicMock()
            mock_dg.STT.return_value = MagicMock()
            mock_cart.TTS.return_value = MagicMock()
            mock_llm.return_value = MagicMock()

            from agent_on_call.main import _build_session

            session = _build_session(model=None, tts_enabled=True)
            # TTS should have been created
            mock_cart.TTS.assert_called_once()
            assert session is not None

    def test_build_session_with_tts_disabled(self):
        with patch("agent_on_call.main.deepgram") as mock_dg, \
             patch("agent_on_call.main.cartesia") as mock_cart, \
             patch("agent_on_call.main.silero") as mock_silero, \
             patch("agent_on_call.main._build_llm") as mock_llm:
            mock_silero.VAD.load.return_value = MagicMock()
            mock_dg.STT.return_value = MagicMock()
            mock_llm.return_value = MagicMock()

            from agent_on_call.main import _build_session

            session = _build_session(model=None, tts_enabled=False)
            # TTS should NOT have been created
            mock_cart.TTS.assert_not_called()
            assert session is not None


class TestTextModeInstruction:
    def test_text_mode_instruction_appended_when_tts_unavailable(self):
        from agent_on_call.main import TEXT_MODE_INSTRUCTION
        from agent_on_call.orchestrator import ORCHESTRATOR_INSTRUCTIONS

        combined = ORCHESTRATOR_INSTRUCTIONS + TEXT_MODE_INSTRUCTION
        assert "text in the transcript" in combined
        assert "reading, not listening" in combined

    def test_text_mode_instruction_not_in_base(self):
        from agent_on_call.orchestrator import ORCHESTRATOR_INSTRUCTIONS

        assert "TTS is unavailable" not in ORCHESTRATOR_INSTRUCTIONS


class TestTtsStatusMessages:
    def test_all_reasons_have_messages(self):
        from agent_on_call.main import TTS_STATUS_MESSAGES

        assert "no_key" in TTS_STATUS_MESSAGES
        assert "auth_failed" in TTS_STATUS_MESSAGES
        assert "no_credits" in TTS_STATUS_MESSAGES
        assert "network_error" in TTS_STATUS_MESSAGES

    def test_messages_are_user_friendly(self):
        from agent_on_call.main import TTS_STATUS_MESSAGES

        for reason, msg in TTS_STATUS_MESSAGES.items():
            assert "unavailable" in msg.lower()
            assert len(msg) > 20  # Not too short
