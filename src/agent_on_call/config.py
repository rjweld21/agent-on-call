"""Configuration loading from environment variables."""

import os
from dataclasses import dataclass


class ConfigError(Exception):
    """Raised when required configuration is missing."""

    pass


@dataclass(frozen=True)
class Config:
    livekit_url: str
    livekit_api_key: str
    livekit_api_secret: str
    deepgram_api_key: str
    llm_provider: str  # "anthropic" or "openai"
    cartesia_api_key: str | None = None
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    git_token: str | None = None


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise ConfigError(f"Required environment variable {name} is not set")
    return value


def load_config() -> Config:
    livekit_url = _require("LIVEKIT_URL")
    livekit_api_key = _require("LIVEKIT_API_KEY")
    livekit_api_secret = _require("LIVEKIT_API_SECRET")
    deepgram_api_key = _require("DEEPGRAM_API_KEY")
    cartesia_api_key = os.environ.get("CARTESIA_API_KEY")

    llm_provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()

    anthropic_api_key = None
    openai_api_key = None

    if llm_provider == "anthropic":
        anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
        if not anthropic_api_key:
            raise ConfigError(
                "Required environment variable ANTHROPIC_API_KEY is not set. "
                "Get one at https://console.anthropic.com/settings/keys"
            )
    elif llm_provider == "openai":
        openai_api_key = _require("OPENAI_API_KEY")
    else:
        raise ConfigError(f"Unsupported LLM_PROVIDER: {llm_provider}. Use 'anthropic' or 'openai'.")

    git_token = os.environ.get("GIT_TOKEN")

    return Config(
        livekit_url=livekit_url,
        livekit_api_key=livekit_api_key,
        livekit_api_secret=livekit_api_secret,
        deepgram_api_key=deepgram_api_key,
        cartesia_api_key=cartesia_api_key,
        llm_provider=llm_provider,
        anthropic_api_key=anthropic_api_key,
        openai_api_key=openai_api_key,
        git_token=git_token,
    )
