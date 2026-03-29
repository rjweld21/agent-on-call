"""Tests for turn-taking configuration."""


class TestVADConfig:
    def test_default_vad_config_values(self):
        from agent_on_call.turn_taking import DEFAULT_VAD_CONFIG

        # More conservative than framework defaults
        assert DEFAULT_VAD_CONFIG.min_silence_duration == 0.8  # framework default: 0.55
        assert DEFAULT_VAD_CONFIG.activation_threshold == 0.55  # framework default: 0.5
        assert DEFAULT_VAD_CONFIG.min_speech_duration == 0.05
        assert DEFAULT_VAD_CONFIG.prefix_padding_duration == 0.5
        assert DEFAULT_VAD_CONFIG.max_buffered_speech == 60.0

    def test_vad_config_is_frozen(self):
        from agent_on_call.turn_taking import VADConfig

        cfg = VADConfig()
        try:
            cfg.min_silence_duration = 1.0  # type: ignore
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass

    def test_custom_vad_config(self):
        from agent_on_call.turn_taking import VADConfig

        cfg = VADConfig(min_silence_duration=1.2, activation_threshold=0.7)
        assert cfg.min_silence_duration == 1.2
        assert cfg.activation_threshold == 0.7


class TestTurnTakingConfig:
    def test_default_turn_taking_config_values(self):
        from agent_on_call.turn_taking import DEFAULT_TURN_TAKING_CONFIG

        assert DEFAULT_TURN_TAKING_CONFIG.min_endpointing_delay == 0.6
        assert DEFAULT_TURN_TAKING_CONFIG.max_endpointing_delay == 3.0
        assert DEFAULT_TURN_TAKING_CONFIG.min_interruption_duration == 0.5
        assert DEFAULT_TURN_TAKING_CONFIG.min_interruption_words == 2

    def test_turn_taking_config_is_frozen(self):
        from agent_on_call.turn_taking import TurnTakingConfig

        cfg = TurnTakingConfig()
        try:
            cfg.min_endpointing_delay = 2.0  # type: ignore
            assert False, "Should have raised FrozenInstanceError"
        except AttributeError:
            pass

    def test_custom_turn_taking_config(self):
        from agent_on_call.turn_taking import TurnTakingConfig

        cfg = TurnTakingConfig(
            min_endpointing_delay=1.0,
            max_endpointing_delay=5.0,
            min_interruption_words=3,
        )
        assert cfg.min_endpointing_delay == 1.0
        assert cfg.max_endpointing_delay == 5.0
        assert cfg.min_interruption_words == 3
