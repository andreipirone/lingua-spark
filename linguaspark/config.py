"""Application-wide constants and default settings."""

from __future__ import annotations

# QSettings identifiers (used for persisting API keys + last-used config).
QSETTINGS_ORG = "Anki-Deck-Generator"
QSETTINGS_APP = "LinguaSpark"

# Stable Anki deck/model IDs (deterministic so re-imports don't duplicate).
# Generated once with uuid4 — keeping them constant avoids deck duplication in Anki.
DECK_ID = 2059400110
MODEL_ID = 1607392319

# Default enrichment targets.
DEFAULT_LANGUAGE = "English"
DEFAULT_INPUT_LANGUAGE = "English"
DEFAULT_OUTPUT_LANGUAGE = "English"
DEFAULT_DECK_NAME = "LinguaSpark Deck"

SUPPORTED_LANGUAGES = [
    "English",
    "Spanish",
    "French",
    "German",
    "Italian",
    "Portuguese",
    "Japanese",
    "Chinese (Mandarin)",
    "Korean",
    "Russian",
    "Arabic",
    "Hindi",
    "Romanian",
]

SUPPORTED_PROVIDERS = [
    "openai",
    "anthropic",
    "gemini",
    "ollama",
    "ollama_cloud",
]

# Ollama endpoint (local).
OLLAMA_DEFAULT_BASE_URL = "http://localhost:11434"
# Ollama Cloud endpoint.
OLLAMA_CLOUD_BASE_URL = "https://ollama.com"

# Enrichment batching.
BATCH_SIZE = 10

# QSettings keys.
SETTING_API_KEY_PREFIX = "api_keys/"
SETTING_LAST_PROVIDER = "last_provider"
SETTING_LAST_MODEL = "last_model"
# Legacy key — kept for backward reads; new code uses the input/output pair.
SETTING_LAST_LANGUAGE = "last_language"
SETTING_LAST_INPUT_LANGUAGE = "last_input_language"
SETTING_LAST_OUTPUT_LANGUAGE = "last_output_language"
SETTING_LAST_DECK_NAME = "last_deck_name"
SETTING_DARK_MODE = "dark_mode"
# Default theme for newly generated .apkg decks ("light" or "dark").
SETTING_DECK_THEME = "deck_theme"


def api_key_setting_key(provider: str) -> str:
    """Return the QSettings key used to store an API key for a provider."""
    return f"{SETTING_API_KEY_PREFIX}{provider}"
