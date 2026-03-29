"""Tests for mid-session settings updates via data channel."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent_on_call.main import (
    _parse_settings_update,
    _build_verbosity_instructions,
    _apply_settings_update,
    VERBOSITY_PROMPTS,
)


class TestParseSettingsUpdate:
    """Test the settings update message parser."""

    def test_valid_settings_update(self):
        data = json.dumps(
            {
                "type": "settings_update",
                "model": "claude-haiku-4-5-20250514",
                "verbosity": 2,
            }
        ).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["model"] == "claude-haiku-4-5-20250514"
        assert result["verbosity"] == 2

    def test_wrong_message_type(self):
        data = json.dumps({"type": "chat_message", "text": "hello"}).encode()
        result = _parse_settings_update(data)
        assert result is None

    def test_invalid_json(self):
        data = b"not json at all"
        result = _parse_settings_update(data)
        assert result is None

    def test_empty_data(self):
        result = _parse_settings_update(b"")
        assert result is None

    def test_invalid_model_rejected(self):
        data = json.dumps(
            {
                "type": "settings_update",
                "model": "gpt-4o-mini",
                "verbosity": 3,
            }
        ).encode()
        result = _parse_settings_update(data)
        assert result is not None
        # Invalid model should be set to None (meaning "keep current")
        assert result["model"] is None

    def test_invalid_verbosity_rejected(self):
        data = json.dumps(
            {
                "type": "settings_update",
                "model": "claude-sonnet-4-5-20250514",
                "verbosity": 0,
            }
        ).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["verbosity"] is None

    def test_verbosity_too_high_rejected(self):
        data = json.dumps(
            {
                "type": "settings_update",
                "verbosity": 6,
            }
        ).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["verbosity"] is None

    def test_verbosity_non_integer_rejected(self):
        data = json.dumps(
            {
                "type": "settings_update",
                "verbosity": "high",
            }
        ).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["verbosity"] is None

    def test_only_model_update(self):
        data = json.dumps(
            {
                "type": "settings_update",
                "model": "claude-opus-4-20250514",
            }
        ).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["model"] == "claude-opus-4-20250514"
        assert result["verbosity"] is None

    def test_only_verbosity_update(self):
        data = json.dumps(
            {
                "type": "settings_update",
                "verbosity": 5,
            }
        ).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["model"] is None
        assert result["verbosity"] == 5


class TestBuildVerbosityInstructions:
    """Test verbosity instruction builder."""

    def test_builds_instructions_with_verbosity(self):
        base = "You are a helpful assistant."
        result = _build_verbosity_instructions(base, 1)
        assert "You are a helpful assistant." in result
        assert "Verbosity directive:" in result
        assert VERBOSITY_PROMPTS[1] in result

    def test_builds_instructions_with_default_verbosity(self):
        base = "You are a helpful assistant."
        result = _build_verbosity_instructions(base, 3)
        assert VERBOSITY_PROMPTS[3] in result

    def test_builds_instructions_with_max_verbosity(self):
        base = "Base instructions."
        result = _build_verbosity_instructions(base, 5)
        assert VERBOSITY_PROMPTS[5] in result


class TestApplySettingsUpdate:
    """Test that _apply_settings_update uses the correct public APIs."""

    @pytest.mark.asyncio
    async def test_verbosity_update_calls_update_instructions(self):
        """Verbosity changes must use agent.update_instructions() (async public API),
        not agent._raw_instructions (private attr that doesn't reach the LLM)."""
        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        update = {"model": None, "verbosity": 1}
        new_model, new_verbosity, changed = await _apply_settings_update(
            update,
            agent,
            session,
            room,
            current_model=None,
            current_verbosity=3,
        )

        assert new_verbosity == 1
        assert changed is True
        # The key assertion: update_instructions must have been called
        agent.update_instructions.assert_awaited_once()
        call_args = agent.update_instructions.call_args[0][0]
        assert "Verbosity directive:" in call_args
        assert VERBOSITY_PROMPTS[1] in call_args

    @pytest.mark.asyncio
    async def test_verbosity_update_uses_async_api(self):
        """Verify update_instructions is awaited (async), confirming it's the
        public API and not a direct attribute assignment."""
        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        update = {"model": None, "verbosity": 4}
        await _apply_settings_update(
            update,
            agent,
            session,
            room,
            current_model=None,
            current_verbosity=3,
        )

        # update_instructions must be awaited (it's async in the LiveKit SDK)
        agent.update_instructions.assert_awaited_once()
        instructions = agent.update_instructions.call_args[0][0]
        assert VERBOSITY_PROMPTS[4] in instructions

    @pytest.mark.asyncio
    async def test_model_update_sets_session_llm(self):
        """Model changes set session._llm (no public setter exists in LiveKit SDK)."""
        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        with patch("agent_on_call.main._build_llm") as mock_build:
            mock_llm = MagicMock()
            mock_build.return_value = mock_llm

            update = {"model": "claude-haiku-4-5-20250514", "verbosity": None}
            new_model, new_verbosity, changed = await _apply_settings_update(
                update,
                agent,
                session,
                room,
                current_model=None,
                current_verbosity=3,
            )

            assert new_model == "claude-haiku-4-5-20250514"
            assert changed is True
            mock_build.assert_called_once_with(model="claude-haiku-4-5-20250514")
            assert session._llm == mock_llm

    @pytest.mark.asyncio
    async def test_no_change_when_same_values(self):
        """No update when values haven't changed."""
        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        update = {"model": None, "verbosity": None}
        _, _, changed = await _apply_settings_update(
            update,
            agent,
            session,
            room,
            current_model="claude-sonnet-4-5-20250514",
            current_verbosity=3,
        )

        assert changed is False
        agent.update_instructions.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_both_model_and_verbosity_update(self):
        """Both model and verbosity update in one call."""
        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        with patch("agent_on_call.main._build_llm") as mock_build:
            mock_llm = MagicMock()
            mock_build.return_value = mock_llm

            update = {"model": "claude-opus-4-20250514", "verbosity": 5}
            new_model, new_verbosity, changed = await _apply_settings_update(
                update,
                agent,
                session,
                room,
                current_model=None,
                current_verbosity=3,
            )

            assert new_model == "claude-opus-4-20250514"
            assert new_verbosity == 5
            assert changed is True
            agent.update_instructions.assert_awaited_once()
            assert session._llm == mock_llm
