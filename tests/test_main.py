"""Tests for main.py — TTS health check, session builder, and utility functions."""

import json
import os
from unittest.mock import patch, MagicMock, AsyncMock

import httpx
import pytest


def _mock_httpx_response(status_code: int):
    """Create a mock httpx.Response with a given status code."""
    resp = MagicMock(spec=httpx.Response)
    resp.status_code = status_code
    return resp


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

    def test_returns_false_for_whitespace_only_key(self):
        with patch.dict(os.environ, {"CARTESIA_API_KEY": "   "}, clear=False):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "no_key"

    def test_returns_true_when_key_valid(self):
        """Key present and both API endpoints return success — TTS is available."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_real_key_123"}, clear=False),
            patch("agent_on_call.main.httpx.get", return_value=_mock_httpx_response(200)),
            patch("agent_on_call.main.httpx.post", return_value=_mock_httpx_response(200)),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is True
            assert reason == ""

    def test_returns_auth_failed_on_401(self):
        """Key present but invalid — API returns 401."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_invalid"}, clear=False),
            patch("agent_on_call.main.httpx.get", return_value=_mock_httpx_response(401)),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "auth_failed"

    def test_returns_auth_failed_on_403(self):
        """Key present but forbidden — API returns 403."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_forbidden"}, clear=False),
            patch("agent_on_call.main.httpx.get", return_value=_mock_httpx_response(403)),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "auth_failed"

    def test_returns_no_credits_on_402(self):
        """Key present but account has no credits — API returns 402."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_expired"}, clear=False),
            patch("agent_on_call.main.httpx.get", return_value=_mock_httpx_response(402)),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "no_credits"

    def test_returns_network_error_on_timeout(self):
        """API is unreachable — httpx.TimeoutException."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_real_key"}, clear=False),
            patch("agent_on_call.main.httpx.get", side_effect=httpx.TimeoutException("timeout")),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "network_error"

    def test_returns_network_error_on_connect_error(self):
        """API is unreachable — httpx.ConnectError."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_real_key"}, clear=False),
            patch("agent_on_call.main.httpx.get", side_effect=httpx.ConnectError("refused")),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "network_error"

    def test_returns_network_error_on_5xx(self):
        """API returns a server error — should report network_error."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_real_key"}, clear=False),
            patch("agent_on_call.main.httpx.get", return_value=_mock_httpx_response(500)),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "network_error"

    def test_sends_correct_headers(self):
        """Verify the health check sends the correct API key and version headers."""
        mock_get = MagicMock(return_value=_mock_httpx_response(200))
        mock_post = MagicMock(return_value=_mock_httpx_response(200))
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_test_key"}, clear=False),
            patch("agent_on_call.main.httpx.get", mock_get),
            patch("agent_on_call.main.httpx.post", mock_post),
        ):
            from agent_on_call.main import _check_tts_available

            _check_tts_available()
            mock_get.assert_called_once()
            call_kwargs = mock_get.call_args
            assert call_kwargs[1]["headers"]["X-API-Key"] == "sk_cart_test_key"
            assert "Cartesia-Version" in call_kwargs[1]["headers"]

    def test_returns_no_credits_when_tts_endpoint_returns_402(self):
        """Voices endpoint returns 200 but TTS endpoint returns 402 — no credits."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_real_key"}, clear=False),
            patch("agent_on_call.main.httpx.get", return_value=_mock_httpx_response(200)),
            patch("agent_on_call.main.httpx.post", return_value=_mock_httpx_response(402)),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is False
            assert reason == "no_credits"

    def test_returns_true_when_tts_endpoint_returns_400(self):
        """Voices 200 + TTS 400 (bad request body) means auth works and credits exist."""
        with (
            patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_real_key"}, clear=False),
            patch("agent_on_call.main.httpx.get", return_value=_mock_httpx_response(200)),
            patch("agent_on_call.main.httpx.post", return_value=_mock_httpx_response(400)),
        ):
            from agent_on_call.main import _check_tts_available

            available, reason = _check_tts_available()
            assert available is True
            assert reason == ""


class TestBuildSession:
    def test_build_session_with_tts_enabled(self):
        with (
            patch("agent_on_call.main.deepgram") as mock_dg,
            patch("agent_on_call.main.cartesia") as mock_cart,
            patch("agent_on_call.main.silero") as mock_silero,
            patch("agent_on_call.main._build_llm") as mock_llm,
        ):
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
        with (
            patch("agent_on_call.main.deepgram") as mock_dg,
            patch("agent_on_call.main.cartesia") as mock_cart,
            patch("agent_on_call.main.silero") as mock_silero,
            patch("agent_on_call.main._build_llm") as mock_llm,
        ):
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


class TestBuildLlm:
    def test_openai_provider(self):
        """When LLM_PROVIDER=openai, returns an OpenAI LLM."""
        mock_openai_module = MagicMock()
        mock_openai_module.LLM.return_value = MagicMock()
        with (
            patch.dict(os.environ, {"LLM_PROVIDER": "openai", "OPENAI_API_KEY": "sk-test"}, clear=False),
            patch.dict("sys.modules", {"livekit.plugins.openai": mock_openai_module}),
        ):
            from agent_on_call.main import _build_llm

            result = _build_llm()
            mock_openai_module.LLM.assert_called_once()
            assert result is not None

    def test_anthropic_provider_with_api_key(self):
        """When LLM_PROVIDER=anthropic with a valid key, returns an Anthropic LLM."""
        with (
            patch.dict(
                os.environ,
                {"LLM_PROVIDER": "anthropic", "ANTHROPIC_API_KEY": "sk-ant-test123"},
                clear=False,
            ),
        ):
            from agent_on_call.main import _build_llm

            # Mock the anthropic plugins
            mock_plugin = MagicMock()
            mock_sdk = MagicMock()
            with (patch.dict("sys.modules", {"livekit.plugins.anthropic": mock_plugin, "anthropic": mock_sdk}),):
                _build_llm()
                mock_plugin.LLM.assert_called_once()

    def test_anthropic_provider_with_oauth_token(self):
        """When using an OAuth token (sk-ant-oat prefix), creates client with auth_token."""
        env = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_AUTH_TOKEN": "sk-ant-oat-test-token",
        }
        with patch.dict(os.environ, env, clear=False):
            from agent_on_call.main import _build_llm

            mock_plugin = MagicMock()
            mock_sdk = MagicMock()
            with patch.dict("sys.modules", {"livekit.plugins.anthropic": mock_plugin, "anthropic": mock_sdk}):
                _build_llm()
                mock_sdk.AsyncAnthropic.assert_called_once_with(auth_token="sk-ant-oat-test-token")

    def test_anthropic_provider_no_key_raises(self):
        """When no API key or auth token, raises RuntimeError."""
        env = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "",
            "ANTHROPIC_AUTH_TOKEN": "",
        }
        with patch.dict(os.environ, env, clear=False):
            from agent_on_call.main import _build_llm

            mock_plugin = MagicMock()
            mock_sdk = MagicMock()
            with (
                patch.dict("sys.modules", {"livekit.plugins.anthropic": mock_plugin, "anthropic": mock_sdk}),
                pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"),
            ):
                _build_llm()

    def test_model_override_with_valid_model(self):
        """Valid model override is used."""
        env = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-test",
        }
        with patch.dict(os.environ, env, clear=False):
            from agent_on_call.main import _build_llm

            mock_plugin = MagicMock()
            mock_sdk = MagicMock()
            with patch.dict("sys.modules", {"livekit.plugins.anthropic": mock_plugin, "anthropic": mock_sdk}):
                _build_llm(model="claude-haiku-4-5-20250514")
                call_kwargs = mock_plugin.LLM.call_args
                assert call_kwargs[1]["model"] == "claude-haiku-4-5-20250514"

    def test_invalid_model_override_falls_back(self):
        """Invalid model override falls back to env var default."""
        env = {
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-test",
            "ANTHROPIC_MODEL": "claude-sonnet-4-5-20250514",
        }
        with patch.dict(os.environ, env, clear=False):
            from agent_on_call.main import _build_llm

            mock_plugin = MagicMock()
            mock_sdk = MagicMock()
            with patch.dict("sys.modules", {"livekit.plugins.anthropic": mock_plugin, "anthropic": mock_sdk}):
                _build_llm(model="invalid-model")
                call_kwargs = mock_plugin.LLM.call_args
                assert call_kwargs[1]["model"] == "claude-sonnet-4-5-20250514"


class TestParseSettingsUpdate:
    def test_valid_settings_update(self):
        from agent_on_call.main import _parse_settings_update

        data = json.dumps({"type": "settings_update", "model": "claude-haiku-4-5-20250514", "verbosity": 2}).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["model"] == "claude-haiku-4-5-20250514"
        assert result["verbosity"] == 2

    def test_invalid_type_returns_none(self):
        from agent_on_call.main import _parse_settings_update

        data = json.dumps({"type": "other_message"}).encode()
        result = _parse_settings_update(data)
        assert result is None

    def test_empty_data_returns_none(self):
        from agent_on_call.main import _parse_settings_update

        assert _parse_settings_update(b"") is None

    def test_invalid_json_returns_none(self):
        from agent_on_call.main import _parse_settings_update

        assert _parse_settings_update(b"not json") is None

    def test_invalid_model_returns_none_model(self):
        from agent_on_call.main import _parse_settings_update

        data = json.dumps({"type": "settings_update", "model": "invalid-model"}).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["model"] is None

    def test_invalid_verbosity_returns_none_verbosity(self):
        from agent_on_call.main import _parse_settings_update

        data = json.dumps({"type": "settings_update", "verbosity": 10}).encode()
        result = _parse_settings_update(data)
        assert result is not None
        assert result["verbosity"] is None

    def test_verbosity_boundary_values(self):
        from agent_on_call.main import _parse_settings_update

        # Valid boundaries
        data1 = json.dumps({"type": "settings_update", "verbosity": 1}).encode()
        assert _parse_settings_update(data1)["verbosity"] == 1

        data5 = json.dumps({"type": "settings_update", "verbosity": 5}).encode()
        assert _parse_settings_update(data5)["verbosity"] == 5

        # Out of range
        data0 = json.dumps({"type": "settings_update", "verbosity": 0}).encode()
        assert _parse_settings_update(data0)["verbosity"] is None

        data6 = json.dumps({"type": "settings_update", "verbosity": 6}).encode()
        assert _parse_settings_update(data6)["verbosity"] is None

    def test_non_dict_json_returns_none(self):
        from agent_on_call.main import _parse_settings_update

        data = json.dumps([1, 2, 3]).encode()
        assert _parse_settings_update(data) is None


class TestReasonFromStatus:
    def test_401_returns_auth_failed(self):
        from agent_on_call.main import _reason_from_status

        assert _reason_from_status(401) == "auth_failed"

    def test_403_returns_auth_failed(self):
        from agent_on_call.main import _reason_from_status

        assert _reason_from_status(403) == "auth_failed"

    def test_402_returns_no_credits(self):
        from agent_on_call.main import _reason_from_status

        assert _reason_from_status(402) == "no_credits"

    def test_500_returns_network_error(self):
        from agent_on_call.main import _reason_from_status

        assert _reason_from_status(500) == "network_error"

    def test_200_returns_network_error(self):
        from agent_on_call.main import _reason_from_status

        assert _reason_from_status(200) == "network_error"


class TestReasonFromStatusStr:
    def test_402_in_string(self):
        from agent_on_call.main import _reason_from_status_str

        assert _reason_from_status_str("cartesia error 402 no credits") == "no_credits"

    def test_401_in_string(self):
        from agent_on_call.main import _reason_from_status_str

        assert _reason_from_status_str("auth error 401") == "auth_failed"

    def test_403_in_string(self):
        from agent_on_call.main import _reason_from_status_str

        assert _reason_from_status_str("forbidden 403") == "auth_failed"

    def test_generic_error(self):
        from agent_on_call.main import _reason_from_status_str

        assert _reason_from_status_str("connection refused") == "network_error"


class TestIsTtsGreetingError:
    def test_cartesia_keyword(self):
        from agent_on_call.main import _is_tts_greeting_error

        assert _is_tts_greeting_error("cartesia connection failed") is True

    def test_tts_keyword(self):
        from agent_on_call.main import _is_tts_greeting_error

        assert _is_tts_greeting_error("tts synthesis error") is True

    def test_402_keyword(self):
        from agent_on_call.main import _is_tts_greeting_error

        assert _is_tts_greeting_error("http 402 payment required") is True

    def test_handshake_keyword(self):
        from agent_on_call.main import _is_tts_greeting_error

        assert _is_tts_greeting_error("websocket handshake failed") is True

    def test_non_tts_error(self):
        from agent_on_call.main import _is_tts_greeting_error

        assert _is_tts_greeting_error("connection timeout to livekit") is False


class TestDetectTtsError:
    def test_non_tts_error_returns_false(self):
        from agent_on_call.main import _detect_tts_error

        error = Exception("some random error")
        is_tts, reason = _detect_tts_error(error)
        assert is_tts is False
        assert reason == "network_error"

    def test_cartesia_in_error_string(self):
        from agent_on_call.main import _detect_tts_error

        error = Exception("Cartesia TTS synthesis failed with 402")
        is_tts, reason = _detect_tts_error(error)
        assert is_tts is True
        assert reason == "no_credits"

    def test_tts_in_error_string(self):
        from agent_on_call.main import _detect_tts_error

        error = Exception("TTS connection error")
        is_tts, reason = _detect_tts_error(error)
        assert is_tts is True
        assert reason == "network_error"

    def test_error_with_status_attribute_401(self):
        from agent_on_call.main import _detect_tts_error

        error = Exception("ws error")
        error.status = 401  # type: ignore
        is_tts, reason = _detect_tts_error(error)
        assert is_tts is True
        assert reason == "auth_failed"

    def test_error_with_status_attribute_402(self):
        from agent_on_call.main import _detect_tts_error

        error = Exception("ws error")
        error.status = 402  # type: ignore
        is_tts, reason = _detect_tts_error(error)
        assert is_tts is True
        assert reason == "no_credits"


class TestGetParticipantMetadata:
    def test_returns_metadata_from_first_participant(self):
        from agent_on_call.main import _get_participant_metadata

        mock_participant = MagicMock()
        mock_participant.metadata = json.dumps({"model": "claude-haiku-4-5-20250514"})
        mock_ctx = MagicMock()
        mock_ctx.room.remote_participants.values.return_value = [mock_participant]

        result = _get_participant_metadata(mock_ctx)
        assert result == {"model": "claude-haiku-4-5-20250514"}

    def test_returns_empty_dict_when_no_metadata(self):
        from agent_on_call.main import _get_participant_metadata

        mock_participant = MagicMock()
        mock_participant.metadata = None
        mock_ctx = MagicMock()
        mock_ctx.room.remote_participants.values.return_value = [mock_participant]

        result = _get_participant_metadata(mock_ctx)
        assert result == {}

    def test_returns_empty_dict_when_no_participants(self):
        from agent_on_call.main import _get_participant_metadata

        mock_ctx = MagicMock()
        mock_ctx.room.remote_participants.values.return_value = []

        result = _get_participant_metadata(mock_ctx)
        assert result == {}

    def test_returns_empty_dict_on_invalid_json(self):
        from agent_on_call.main import _get_participant_metadata

        mock_participant = MagicMock()
        mock_participant.metadata = "not json"
        mock_ctx = MagicMock()
        mock_ctx.room.remote_participants.values.return_value = [mock_participant]

        result = _get_participant_metadata(mock_ctx)
        assert result == {}

    def test_returns_empty_dict_when_metadata_is_not_dict(self):
        from agent_on_call.main import _get_participant_metadata

        mock_participant = MagicMock()
        mock_participant.metadata = json.dumps([1, 2, 3])
        mock_ctx = MagicMock()
        mock_ctx.room.remote_participants.values.return_value = [mock_participant]

        result = _get_participant_metadata(mock_ctx)
        assert result == {}


class TestGetCartesiaApiKey:
    def test_returns_key_when_valid(self):
        from agent_on_call.main import _get_cartesia_api_key

        with patch.dict(os.environ, {"CARTESIA_API_KEY": "sk_cart_valid_key"}):
            assert _get_cartesia_api_key() == "sk_cart_valid_key"

    def test_returns_none_for_placeholder(self):
        from agent_on_call.main import _get_cartesia_api_key

        with patch.dict(os.environ, {"CARTESIA_API_KEY": "placeholder"}):
            assert _get_cartesia_api_key() is None

    def test_returns_none_for_empty(self):
        from agent_on_call.main import _get_cartesia_api_key

        with patch.dict(os.environ, {"CARTESIA_API_KEY": ""}):
            assert _get_cartesia_api_key() is None

    def test_returns_none_when_not_set(self):
        from agent_on_call.main import _get_cartesia_api_key

        env = os.environ.copy()
        env.pop("CARTESIA_API_KEY", None)
        with patch.dict(os.environ, env, clear=True):
            assert _get_cartesia_api_key() is None

    def test_strips_whitespace(self):
        from agent_on_call.main import _get_cartesia_api_key

        with patch.dict(os.environ, {"CARTESIA_API_KEY": "  sk_cart_key  "}):
            assert _get_cartesia_api_key() == "sk_cart_key"


class TestCheckCartesiaStatus:
    def test_returns_auth_failed_for_401(self):
        from agent_on_call.main import _check_cartesia_status

        result = _check_cartesia_status(401, "API")
        assert result == (False, "auth_failed")

    def test_returns_auth_failed_for_403(self):
        from agent_on_call.main import _check_cartesia_status

        result = _check_cartesia_status(403, "API")
        assert result == (False, "auth_failed")

    def test_returns_no_credits_for_402(self):
        from agent_on_call.main import _check_cartesia_status

        result = _check_cartesia_status(402, "API")
        assert result == (False, "no_credits")

    def test_strict_mode_returns_network_error_for_4xx(self):
        from agent_on_call.main import _check_cartesia_status

        result = _check_cartesia_status(400, "API", strict=True)
        assert result == (False, "network_error")

    def test_non_strict_mode_returns_none_for_400(self):
        from agent_on_call.main import _check_cartesia_status

        result = _check_cartesia_status(400, "TTS", strict=False)
        assert result is None

    def test_returns_none_for_200(self):
        from agent_on_call.main import _check_cartesia_status

        result = _check_cartesia_status(200, "API")
        assert result is None


class TestBuildVerbosityInstructions:
    def test_appends_verbosity_to_instructions(self):
        from agent_on_call.main import _build_verbosity_instructions

        result = _build_verbosity_instructions("Base instructions here.", 1)
        assert "Base instructions here." in result

    def test_different_verbosity_levels_produce_different_output(self):
        from agent_on_call.main import _build_verbosity_instructions

        result1 = _build_verbosity_instructions("Base.", 1)
        result5 = _build_verbosity_instructions("Base.", 5)
        assert result1 != result5


class TestApplySettingsUpdate:
    @pytest.mark.asyncio
    async def test_verbosity_change_updates_agent(self):
        from agent_on_call.main import _apply_settings_update

        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        update = {"model": None, "verbosity": 2}
        new_model, new_verbosity, changed = await _apply_settings_update(update, agent, session, room, None, 3)
        assert new_verbosity == 2
        assert changed is True
        agent.update_instructions.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_change_updates_session(self):
        from agent_on_call.main import _apply_settings_update

        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        with patch("agent_on_call.main._build_llm") as mock_build_llm:
            mock_build_llm.return_value = MagicMock()
            update = {"model": "claude-haiku-4-5-20250514", "verbosity": None}
            new_model, new_verbosity, changed = await _apply_settings_update(update, agent, session, room, None, 3)
            assert new_model == "claude-haiku-4-5-20250514"
            assert changed is True

    @pytest.mark.asyncio
    async def test_no_change_returns_unchanged(self):
        from agent_on_call.main import _apply_settings_update

        agent = MagicMock()
        session = MagicMock()
        room = MagicMock()

        update = {"model": None, "verbosity": None}
        new_model, new_verbosity, changed = await _apply_settings_update(update, agent, session, room, None, 3)
        assert changed is False

    @pytest.mark.asyncio
    async def test_same_values_returns_unchanged(self):
        from agent_on_call.main import _apply_settings_update

        agent = MagicMock()
        session = MagicMock()
        room = MagicMock()

        update = {"model": "claude-haiku-4-5-20250514", "verbosity": 3}
        new_model, new_verbosity, changed = await _apply_settings_update(
            update, agent, session, room, "claude-haiku-4-5-20250514", 3
        )
        assert changed is False

    @pytest.mark.asyncio
    async def test_sends_ack_on_change(self):
        from agent_on_call.main import _apply_settings_update

        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        update = {"model": None, "verbosity": 1}
        await _apply_settings_update(update, agent, session, room, None, 3)
        room.local_participant.publish_data.assert_called_once()

    @pytest.mark.asyncio
    async def test_model_change_failure_does_not_crash(self):
        from agent_on_call.main import _apply_settings_update

        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()

        with patch("agent_on_call.main._build_llm", side_effect=Exception("LLM init failed")):
            update = {"model": "claude-haiku-4-5-20250514", "verbosity": None}
            new_model, new_verbosity, changed = await _apply_settings_update(update, agent, session, room, None, 3)
            # Model change failed, so changed should be False
            assert changed is False

    @pytest.mark.asyncio
    async def test_with_prompt_builder(self):
        from agent_on_call.main import _apply_settings_update

        agent = MagicMock()
        agent.update_instructions = AsyncMock()
        session = MagicMock()
        room = MagicMock()
        room.local_participant.publish_data = AsyncMock()
        prompt_builder = MagicMock()
        prompt_builder.build.return_value = "new instructions"

        update = {"model": None, "verbosity": 2}
        await _apply_settings_update(update, agent, session, room, None, 3, prompt_builder=prompt_builder)
        prompt_builder.set_verbosity.assert_called_once_with(2)
        prompt_builder.build.assert_called_once()
