"""Shared test fixtures."""

import os
import pytest
from unittest.mock import patch


@pytest.fixture
def mock_env():
    """Provide a complete set of environment variables for testing."""
    env = {
        "LIVEKIT_URL": "ws://localhost:7880",
        "LIVEKIT_API_KEY": "devkey",
        "LIVEKIT_API_SECRET": "secret",
        "DEEPGRAM_API_KEY": "test_dg_key",
        "CARTESIA_API_KEY": "test_cart_key",
        "LLM_PROVIDER": "anthropic",
        "ANTHROPIC_API_KEY": "test_ant_key",
    }
    with patch.dict(os.environ, env, clear=False):
        yield env
