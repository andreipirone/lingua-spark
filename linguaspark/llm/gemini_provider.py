"""Google Gemini provider using `response_schema` for structured output."""

from __future__ import annotations

import json
from typing import Any, List, Optional

from linguaspark.llm.base import LLMProvider
from linguaspark.llm.prompts import build_system_prompt, build_user_prompt


class GeminiProvider(LLMProvider):
    name = "gemini"
    requires_api_key = True

    def _enrich_batch(
        self,
        words: List[str],
        corrective_message: Optional[str] = None,
    ) -> Any:
        from google import genai
        from google.genai import types

        client = genai.Client(api_key=self.api_key)

        system = build_system_prompt(self.input_language, self.output_language)
        user = build_user_prompt(words, self.input_language)
        if corrective_message:
            user = f"{user}\n\n{corrective_message}"

        response = client.models.generate_content(
            model=self.model,
            contents=user,
            config=types.GenerateContentConfig(
                system_instruction=system,
                response_mime_type="application/json",
                response_schema=_batch_schema(),
                temperature=0.4,
            ),
        )

        text = getattr(response, "text", None)
        if not text:
            raise ValueError("Gemini returned empty content")
        # Gemini with response_mime_type='application/json' returns a JSON string.
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text

    def test_connection(self) -> bool:
        from google import genai

        client = genai.Client(api_key=self.api_key)
        client.models.generate_content(
            model=self.model,
            contents="ping",
        )
        return True


def _batch_schema() -> dict:
    from linguaspark.models.card import BatchResponse

    return BatchResponse.model_json_schema()
