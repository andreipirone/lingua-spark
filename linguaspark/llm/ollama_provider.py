"""Ollama provider — talks to a local Ollama server OR Ollama Cloud via HTTP.

* Local: ``http://localhost:11434`` by default, no API key.
* Cloud: ``https://ollama.com`` with an ``Authorization: Bearer ...`` header.
"""

from __future__ import annotations

import json
from typing import Any, List, Optional

import requests

from linguaspark.config import OLLAMA_CLOUD_BASE_URL, OLLAMA_DEFAULT_BASE_URL
from linguaspark.llm.base import LLMProvider
from linguaspark.llm.prompts import build_system_prompt, build_user_prompt


class OllamaProvider(LLMProvider):
    """Provider for both local and cloud Ollama deployments."""

    name = "ollama"
    requires_api_key = False  # overridden on instances targeting Ollama Cloud

    def __init__(
        self,
        model: str,
        input_language: str,
        output_language: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 1,
        timeout: int = 120,
        cloud: bool = False,
    ) -> None:
        is_cloud = bool(cloud) or base_url == OLLAMA_CLOUD_BASE_URL
        if is_cloud:
            # Per-instance override; base.py reads self.requires_api_key.
            self.requires_api_key = True
            resolved_base = OLLAMA_CLOUD_BASE_URL
        else:
            self.requires_api_key = False
            resolved_base = base_url or OLLAMA_DEFAULT_BASE_URL

        super().__init__(
            model=model,
            input_language=input_language,
            output_language=output_language,
            api_key=api_key,
            base_url=resolved_base,
            max_retries=max_retries,
        )
        self._is_cloud = is_cloud
        self.timeout = timeout

    @property
    def is_cloud(self) -> bool:
        return self._is_cloud

    def _enrich_batch(
        self,
        words: List[str],
        corrective_message: Optional[str] = None,
    ) -> Any:
        url = f"{self.base_url.rstrip('/')}/api/chat"
        system = build_system_prompt(self.input_language, self.output_language)
        user = build_user_prompt(words, self.input_language)
        if corrective_message:
            user = f"{user}\n\n{corrective_message}"

        payload = {
            "model": self.model,
            "stream": False,
            "format": _batch_schema(),  # Ollama enforces JSON shape when `format` is a schema.
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }

        headers = {}
        if self._is_cloud and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        response = requests.post(url, json=payload, headers=headers, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()

        message = data.get("message") or {}
        content = message.get("content", "")
        if not content:
            raise ValueError("Ollama returned empty content")
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            return content

    def test_connection(self) -> bool:
        url = f"{self.base_url.rstrip('/')}/api/tags"
        headers = {}
        if self._is_cloud and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        response = requests.get(url, headers=headers, timeout=5)
        response.raise_for_status()
        tags = response.json().get("models", [])
        names = {m.get("name", "").split(":")[0] for m in tags}
        if names and self.model.split(":")[0] not in names:
            raise RuntimeError(
                f"Model '{self.model}' is not available. "
                f"Available: {sorted(names)}"
            )
        return True


def _batch_schema() -> dict:
    from linguaspark.models.card import BatchResponse

    return BatchResponse.model_json_schema()
