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
# Piper TTS (experimental).
SETTING_TTS_ENABLED = "tts_enabled"
SETTING_TTS_MODEL_PATH = "tts_model_path"
SETTING_TTS_CONFIG_PATH = "tts_config_path"
SETTING_TTS_SPEAKER_ID = "tts_speaker_id"
SETTING_TTS_LENGTH_SCALE = "tts_length_scale"
SETTING_TTS_NOISE_SCALE = "tts_noise_scale"
SETTING_TTS_NOISE_W = "tts_noise_w"
SETTING_TTS_USE_DEFAULTS = "tts_use_defaults"

# TTS defaults (Piper's recommended values).
DEFAULT_TTS_SPEAKER_ID = 0
DEFAULT_TTS_LENGTH_SCALE = 1.0
DEFAULT_TTS_NOISE_SCALE = 0.667
DEFAULT_TTS_NOISE_W = 0.8


def api_key_setting_key(provider: str) -> str:
    """Return the QSettings key used to store an API key for a provider."""
    return f"{SETTING_API_KEY_PREFIX}{provider}"
