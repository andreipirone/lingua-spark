"""Anthropic provider using tool-use for structured output."""

from __future__ import annotations

from typing import Any, List, Optional

from linguaspark.llm.base import LLMProvider
from linguaspark.llm.prompts import build_system_prompt, build_user_prompt


_TOOL_NAME = "submit_flashcards"


class AnthropicProvider(LLMProvider):
    name = "anthropic"
    requires_api_key = True

    def _enrich_batch(
        self,
        words: List[str],
        corrective_message: Optional[str] = None,
    ) -> Any:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)

        system = build_system_prompt(self.input_language, self.output_language)
        user = build_user_prompt(words, self.input_language)
        if corrective_message:
            user = f"{user}\n\n{corrective_message}"

        message = client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            tools=[_tool_definition()],
            tool_choice={"type": "tool", "name": _TOOL_NAME},
            messages=[{"role": "user", "content": user}],
        )

        return _extract_tool_input(message)

    def test_connection(self) -> bool:
        import anthropic

        client = anthropic.Anthropic(api_key=self.api_key)
        # Lightweight call; counts against rate limits but validates the key.
        client.messages.create(
            model=self.model,
            max_tokens=8,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True


def _tool_definition() -> dict:
    """Build the Anthropic tool schema for the batch response."""
    schema = _batch_schema()
    return {
        "name": _TOOL_NAME,
        "description": "Submit the enriched flashcard batch.",
        "input_schema": schema,
    }


def _batch_schema() -> dict:
    from linguaspark.models.card import BatchResponse

    return BatchResponse.model_json_schema()


def _extract_tool_input(message: Any) -> Any:
    """Pull the structured input from the first tool-use block."""
    for block in getattr(message, "content", []) or []:
        block_type = getattr(block, "type", None)
        if block_type == "tool_use" and getattr(block, "name", None) == _TOOL_NAME:
            return getattr(block, "input", {})
    raise ValueError("Anthropic response did not contain a tool_use block")
