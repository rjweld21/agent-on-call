"""Turn-taking and VAD configuration for smarter pause detection.

These settings tune the voice activity detection and endpointing behavior
to reduce premature interruptions when users pause mid-sentence. The defaults
here are more conservative than the framework defaults, prioritizing natural
conversation flow over response latency.

Tuning rationale:
- min_silence_duration 0.8s (default 0.55s): Allows natural thinking pauses
  without the agent jumping in. Users often pause 0.5-1.0s mid-thought.
- activation_threshold 0.55 (default 0.5): Slightly less sensitive to avoid
  triggering on background noise or quiet sounds.
- min_endpointing_delay 0.6s: Ensures at least 0.6s of silence before the
  agent considers the user done speaking.
- max_endpointing_delay 3.0s: Agent will respond after 3s of silence even if
  the turn detector is uncertain.
- min_interruption_duration 0.5s: User must speak for at least 0.5s to
  interrupt the agent (prevents accidental interrupts from coughs, etc.).
- min_interruption_words 2: User must say at least 2 words to interrupt.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class VADConfig:
    """Silero VAD configuration."""

    min_speech_duration: float = 0.05
    min_silence_duration: float = 0.8  # Increased from 0.55s for more patient pauses
    prefix_padding_duration: float = 0.5
    activation_threshold: float = 0.55  # Increased from 0.5 for less noise sensitivity
    max_buffered_speech: float = 60.0


@dataclass(frozen=True)
class TurnTakingConfig:
    """AgentSession turn-taking configuration."""

    min_endpointing_delay: float = 0.6  # Minimum silence before considering turn over
    max_endpointing_delay: float = 3.0  # Maximum wait before responding
    min_interruption_duration: float = 0.5  # Minimum speech to interrupt agent
    min_interruption_words: int = 2  # Minimum words to count as interruption


# Default configurations — these can be overridden via environment variables
# or future settings panel controls.
DEFAULT_VAD_CONFIG = VADConfig()
DEFAULT_TURN_TAKING_CONFIG = TurnTakingConfig()
