"""PromptBuilder — composable system prompt with token budget management."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

VERBOSITY_PROMPTS: dict[int, str] = {
    1: (
        "Be extremely concise. Give bare minimum answers. Short, declarative sentences. "
        "Skip pleasantries, context, and elaboration."
    ),
    2: (
        "Be brief but complete. Answer with just enough context. No filler or examples "
        "unless asked. One or two sentences when possible."
    ),
    3: "Use a natural conversational tone. Provide context when helpful. Explain reasoning briefly.",
    4: "Give thorough explanations. Walk through reasoning step by step. Offer examples and alternatives.",
    5: "Explain everything in full detail. Cover background, context, trade-offs, edge cases, and implications.",
}

TEXT_MODE_INSTRUCTION = (
    "\n\nNote: TTS is unavailable for this session. Your responses will appear as "
    "text in the transcript only. Keep responses well-formatted for reading. "
    "You do not need to change your behavior significantly — just be aware the "
    "user is reading, not listening."
)


class PromptBuilder:
    """Composes the orchestrator system prompt from structured sections.

    Sections are assembled in priority order. When the total exceeds the
    token budget, lower-priority sections are dropped first:

    1. Base instructions (never truncated)
    2. TTS text-mode note (high priority when present)
    3. Verbosity directive (always included if budget allows)
    4. Active tools list (dropped if budget tight)
    5. Workspace info (lowest priority, dropped first)
    """

    def __init__(self, token_budget: int = 1500) -> None:
        self._token_budget = token_budget
        self._base_instructions: str = ""
        self._verbosity: int = 3
        self._tts_available: bool = True
        self._active_tools: list[str] = []
        self._workspace_info: str | None = None

    def set_base_instructions(self, instructions: str) -> PromptBuilder:
        """Set the fixed base instructions (always included)."""
        self._base_instructions = instructions
        return self

    def set_verbosity(self, level: int) -> PromptBuilder:
        """Set verbosity level (1-5). Out-of-range values default to 3."""
        if not isinstance(level, int) or level < 1 or level > 5:
            level = 3
        self._verbosity = level
        return self

    def set_tts_available(self, available: bool) -> PromptBuilder:
        """Set TTS availability status."""
        self._tts_available = available
        return self

    def set_active_tools(self, tools: list[str]) -> PromptBuilder:
        """Set list of active tool names for context."""
        self._active_tools = list(tools)
        return self

    def set_workspace_info(self, info: str | None) -> PromptBuilder:
        """Set current workspace status summary."""
        self._workspace_info = info
        return self

    def build(self) -> str:
        """Compose all sections into a final prompt string within token budget.

        Base instructions are always included (never truncated). Other sections
        are added in priority order; if the budget is exceeded, lower-priority
        sections are omitted.
        """
        # Start with base instructions (always present)
        parts: list[str] = []
        if self._base_instructions:
            parts.append(self._base_instructions)

        # TTS text-mode note (high priority)
        tts_section = ""
        if not self._tts_available:
            tts_section = TEXT_MODE_INSTRUCTION

        # Verbosity directive
        directive = VERBOSITY_PROMPTS.get(self._verbosity, VERBOSITY_PROMPTS[3])
        verbosity_section = f"\n\nVerbosity directive: {directive}"

        # Active tools
        tools_section = ""
        if self._active_tools:
            tools_list = ", ".join(self._active_tools)
            tools_section = f"\n\nActive tools: {tools_list}"

        # Workspace info
        workspace_section = ""
        if self._workspace_info:
            workspace_section = f"\n\nWorkspace: {self._workspace_info}"

        # Assemble in priority order, checking budget
        # Priority (highest to lowest): base > tts > verbosity > tools > workspace
        base_text = "".join(parts)
        base_tokens = self.estimate_tokens(base_text)

        remaining = self._token_budget - base_tokens

        # Add sections in priority order, dropping if over budget
        optional_sections: list[tuple[str, str]] = [
            ("tts", tts_section),
            ("verbosity", verbosity_section),
            ("tools", tools_section),
            ("workspace", workspace_section),
        ]

        included: list[str] = [base_text]

        for name, section in optional_sections:
            if not section:
                continue
            section_tokens = self.estimate_tokens(section)
            if section_tokens <= remaining:
                included.append(section)
                remaining -= section_tokens
            else:
                logger.debug(
                    "PromptBuilder: dropping '%s' section (%d tokens, %d remaining)",
                    name,
                    section_tokens,
                    remaining,
                )

        result = "".join(included)
        logger.debug(
            "PromptBuilder: built prompt (%d tokens, budget %d)",
            self.estimate_tokens(result),
            self._token_budget,
        )
        return result

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Rough token estimate: len(text) / 4."""
        return len(text) // 4
