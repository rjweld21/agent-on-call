import os
import pytest
from unittest.mock import patch


class TestConfig:
    def test_load_config_with_all_vars(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "ant_key",
        }
        with patch.dict(os.environ, env, clear=False):
            config = load_config()
            assert config.livekit_url == "ws://localhost:7880"
            assert config.llm_provider == "anthropic"
            assert config.anthropic_api_key == "ant_key"

    def test_load_config_missing_required_var(self):
        from agent_on_call.config import load_config, ConfigError

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ConfigError):
                load_config()

    def test_load_config_openai_provider(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "openai",
            "OPENAI_API_KEY": "oai_key",
        }
        with patch.dict(os.environ, env, clear=False):
            config = load_config()
            assert config.llm_provider == "openai"
            assert config.openai_api_key == "oai_key"

    def test_load_config_anthropic_auth_token_fallback(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_AUTH_TOKEN": "sk-ant-oat01-test-token",
            # No ANTHROPIC_API_KEY — should fall back to AUTH_TOKEN
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.anthropic_api_key == "sk-ant-oat01-test-token"

    def test_load_config_api_key_takes_precedence_over_auth_token(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "sk-ant-api03-real-key",
            "ANTHROPIC_AUTH_TOKEN": "sk-ant-oat01-fallback",
        }
        with patch.dict(os.environ, env, clear=False):
            config = load_config()
            assert config.anthropic_api_key == "sk-ant-api03-real-key"

    def test_load_config_with_git_token(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "ant_key",
            "GIT_TOKEN": "ghp_test_token_123",
        }
        with patch.dict(os.environ, env, clear=False):
            config = load_config()
            assert config.git_token == "ghp_test_token_123"

    def test_load_config_without_git_token(self):
        from agent_on_call.config import load_config

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            "ANTHROPIC_API_KEY": "ant_key",
        }
        with patch.dict(os.environ, env, clear=True):
            config = load_config()
            assert config.git_token is None

    def test_load_config_missing_llm_key_for_provider(self):
        from agent_on_call.config import load_config, ConfigError

        env = {
            "LIVEKIT_URL": "ws://localhost:7880",
            "LIVEKIT_API_KEY": "devkey",
            "LIVEKIT_API_SECRET": "secret",
            "DEEPGRAM_API_KEY": "dg_key",
            "CARTESIA_API_KEY": "cart_key",
            "LLM_PROVIDER": "anthropic",
            # Missing ANTHROPIC_API_KEY
        }
        with patch.dict(os.environ, env, clear=True):
            with pytest.raises(ConfigError, match="ANTHROPIC_API_KEY"):
                load_config()
