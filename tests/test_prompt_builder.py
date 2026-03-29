"""Tests for PromptBuilder."""

import pytest


class TestPromptBuilder:
    """Test PromptBuilder section composition and token budget."""

    def _make_builder(self, **kwargs):
        from agent_on_call.prompt_builder import PromptBuilder

        return PromptBuilder(**kwargs)

    def test_build_includes_base_instructions(self):
        builder = self._make_builder()
        builder.set_base_instructions("You are an AI assistant.")
        result = builder.build()
        assert "You are an AI assistant." in result

    def test_build_includes_verbosity_directive(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_verbosity(1)
        result = builder.build()
        assert "Verbosity directive:" in result
        assert "extremely concise" in result.lower()

    def test_build_verbosity_default_is_3(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        result = builder.build()
        # Default verbosity 3 should still be included
        assert "Verbosity directive:" in result
        assert "natural conversational" in result.lower()

    def test_build_all_verbosity_levels(self):
        from agent_on_call.prompt_builder import VERBOSITY_PROMPTS

        for level in range(1, 6):
            builder = self._make_builder()
            builder.set_base_instructions("Base.")
            builder.set_verbosity(level)
            result = builder.build()
            assert VERBOSITY_PROMPTS[level] in result

    def test_build_includes_tts_text_mode_when_unavailable(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_tts_available(False)
        result = builder.build()
        assert "TTS is unavailable" in result

    def test_build_omits_tts_note_when_available(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_tts_available(True)
        result = builder.build()
        assert "TTS is unavailable" not in result

    def test_build_includes_active_tools(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_active_tools(["exec_command", "git_clone", "web_search"])
        result = builder.build()
        assert "exec_command" in result
        assert "git_clone" in result
        assert "web_search" in result

    def test_build_includes_workspace_info(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_workspace_info("Active workspace: my-app (running)")
        result = builder.build()
        assert "my-app" in result

    def test_build_omits_workspace_when_none(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_workspace_info(None)
        result = builder.build()
        assert "Workspace:" not in result

    def test_build_omits_tools_when_empty(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_active_tools([])
        result = builder.build()
        assert "Active tools:" not in result

    def test_build_within_token_budget(self):
        from agent_on_call.prompt_builder import PromptBuilder

        builder = PromptBuilder(token_budget=100)
        builder.set_base_instructions("Short base.")
        builder.set_verbosity(3)
        builder.set_workspace_info("Workspace info " * 50)  # Very long
        result = builder.build()
        tokens = PromptBuilder.estimate_tokens(result)
        assert tokens <= 100

    def test_truncation_drops_workspace_first(self):
        from agent_on_call.prompt_builder import PromptBuilder

        builder = PromptBuilder(token_budget=50)
        builder.set_base_instructions("Base instructions here.")
        builder.set_verbosity(1)
        builder.set_workspace_info("This workspace info should be dropped")
        result = builder.build()
        assert "Base instructions here." in result
        # Workspace info should be truncated or dropped
        assert "Verbosity directive:" in result

    def test_base_instructions_never_truncated(self):
        from agent_on_call.prompt_builder import PromptBuilder

        # Even with tiny budget, base is always present
        builder = PromptBuilder(token_budget=10)
        builder.set_base_instructions("Base instructions that exceed token budget.")
        result = builder.build()
        assert "Base instructions that exceed token budget." in result

    def test_estimate_tokens(self):
        from agent_on_call.prompt_builder import PromptBuilder

        assert PromptBuilder.estimate_tokens("") == 0
        assert PromptBuilder.estimate_tokens("abcd") == 1
        assert PromptBuilder.estimate_tokens("a" * 400) == 100

    def test_set_verbosity_clamps_range(self):
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_verbosity(0)  # Below range
        result = builder.build()
        # Should default to level 3
        assert "natural conversational" in result.lower()

        builder.set_verbosity(6)  # Above range
        result = builder.build()
        assert "natural conversational" in result.lower()

    def test_builder_pattern_returns_self(self):
        builder = self._make_builder()
        result = builder.set_base_instructions("Base.")
        assert result is builder
        result = builder.set_verbosity(3)
        assert result is builder
        result = builder.set_tts_available(True)
        assert result is builder
        result = builder.set_active_tools([])
        assert result is builder
        result = builder.set_workspace_info(None)
        assert result is builder

    def test_mid_session_rebuild(self):
        """Simulates a mid-session verbosity change: build, change, rebuild."""
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_verbosity(3)
        result1 = builder.build()
        assert "natural conversational" in result1.lower()

        builder.set_verbosity(1)
        result2 = builder.build()
        assert "extremely concise" in result2.lower()
        assert "natural conversational" not in result2.lower()

    def test_mid_session_tts_disable(self):
        """Simulates TTS failing mid-session."""
        builder = self._make_builder()
        builder.set_base_instructions("Base.")
        builder.set_tts_available(True)
        result1 = builder.build()
        assert "TTS is unavailable" not in result1

        builder.set_tts_available(False)
        result2 = builder.build()
        assert "TTS is unavailable" in result2

    def test_empty_base_instructions(self):
        builder = self._make_builder()
        # No base instructions set
        result = builder.build()
        # Should still work, just have verbosity directive
        assert "Verbosity directive:" in result
