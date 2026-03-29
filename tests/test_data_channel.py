"""Tests for mid-session settings updates via data channel."""

import json

from agent_on_call.main import (
    _parse_settings_update,
    _build_verbosity_instructions,
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
