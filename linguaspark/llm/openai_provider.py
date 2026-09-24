"""OpenAI provider using structured outputs (JSON schema)."""

from __future__ import annotations

from typing import Any, List, Optional

from linguaspark.llm.base import LLMProvider
from linguaspark.llm.prompts import build_system_prompt, build_user_prompt


class OpenAIProvider(LLMProvider):
    name = "openai"
    requires_api_key = True

    def _enrich_batch(
        self,
        words: List[str],
        corrective_message: Optional[str] = None,
    ) -> Any:
        # Imported lazily so the rest of the package loads even if openai
        # isn't installed in the current environment.
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)

        system = build_system_prompt(self.input_language, self.output_language)
        user = build_user_prompt(words, self.input_language)
        if corrective_message:
            user = f"{user}\n\n{corrective_message}"

        completion = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            response_format={
                "type": "json_schema",
                "json_schema": {
                    "name": "linguaspark_batch",
                    "strict": True,
                    "schema": _batch_schema(),
                },
            },
        )

        message = completion.choices[0].message
        return _extract_content(message.content)

    def test_connection(self) -> bool:
        from openai import OpenAI

        client = OpenAI(api_key=self.api_key)
        client.models.list()
        return True


def _batch_schema() -> dict:
    """JSON schema for the batch response (provider-agnostic)."""
    from linguaspark.models.card import BatchResponse

    return BatchResponse.model_json_schema()


def _extract_content(content: Any) -> Any:
    """OpenAI may return content as str or list of typed parts; normalise."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        # Concatenate any text parts.
        return "".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in content
        )
    return str(content)
