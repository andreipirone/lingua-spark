"""Factory for constructing the appropriate LLM provider from settings."""

from __future__ import annotations

from typing import Optional

from linguaspark.config import OLLAMA_CLOUD_BASE_URL, SUPPORTED_PROVIDERS
from linguaspark.llm.base import LLMProvider


_PROVIDERS = {
    "openai": "linguaspark.llm.openai_provider.OpenAIProvider",
    "anthropic": "linguaspark.llm.anthropic_provider.AnthropicProvider",
    "gemini": "linguaspark.llm.gemini_provider.GeminiProvider",
    "ollama": "linguaspark.llm.ollama_provider.OllamaProvider",
    "ollama_cloud": "linguaspark.llm.ollama_provider.OllamaProvider",
}


def build_provider(
    kind: str,
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
    base_url: Optional[str] = None,
    input_language: str = "English",
    output_language: str = "English",
) -> LLMProvider:
    """Instantiate the provider identified by `kind`.

    `input_language` is the language of the supplied words and the example
    sentences to generate. `output_language` is the language used for all
    explanatory content on the back of the card.

    Raises:
      ValueError: if `kind` is unknown or `model` is empty.
    """
    if kind not in SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown provider: {kind!r}. Supported: {SUPPORTED_PROVIDERS}"
        )
    if not model or not model.strip():
        raise ValueError(
            f"A model name is required for provider {kind!r} "
            "(no default is provided)."
        )

    cls = _load_class(_PROVIDERS[kind])
    in_lang = (input_language or "English").strip() or "English"
    out_lang = (output_language or "English").strip() or "English"

    if cls is _load_class(_PROVIDERS["ollama"]):
        # OllamaProvider can serve both local and cloud requests.
        cloud = (kind == "ollama_cloud")
        return cls(
            model=model.strip(),
            input_language=in_lang,
            output_language=out_lang,
            api_key=api_key,
            base_url=OLLAMA_CLOUD_BASE_URL if cloud else base_url,
            cloud=cloud,
        )

    return cls(
        model=model.strip(),
        input_language=in_lang,
        output_language=out_lang,
        api_key=api_key,
        base_url=base_url,
    )


def provider_metadata() -> list[dict]:
    """Return display info for every supported provider (used by the UI)."""
    return [
        {"key": "openai", "label": "OpenAI", "requires_key": True},
        {"key": "anthropic", "label": "Anthropic", "requires_key": True},
        {"key": "gemini", "label": "Google Gemini", "requires_key": True},
        {"key": "ollama", "label": "Ollama (Local)", "requires_key": False},
        {"key": "ollama_cloud", "label": "Ollama Cloud", "requires_key": True},
    ]


def _load_class(dotted: str):
    """Import a class from `package.module.ClassName`."""
    module_path, _, class_name = dotted.rpartition(".")
    import importlib

    module = importlib.import_module(module_path)
    return getattr(module, class_name)

