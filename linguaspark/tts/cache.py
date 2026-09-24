"""Memoised Piper voice loader.

Loading an ONNX voice from disk takes ~1 second. ``get_engine`` returns
the same ``PiperVoice`` instance for repeated calls with the same model
path, sparing the user additional synth stalls mid-export.
"""

from __future__ import annotations

from threading import Lock
from typing import Any, Dict, Optional


_cache: Dict[str, Any] = {}
_lock = Lock()


def _cache_key(model_path: str, config_path: str, use_cuda: bool) -> str:
    return f"{model_path}|{config_path}|cuda={int(use_cuda)}"


def get_engine(
    model_path: str,
    config_path: str,
    use_cuda: bool = False,
) -> Any:
    """Return the cached ``PiperVoice`` for ``model_path``.

    ``piper.PiperVoice.load`` is wrapped in a cache so repeated calls
    during a deck export (one per card) reuse the same ONNX session.
    """
    key = _cache_key(model_path, config_path, use_cuda)
    with _lock:
        if key in _cache:
            return _cache[key]
        # Imported lazily so non-TTS code paths never load piper/onnx.
        from piper import PiperVoice

        voice = PiperVoice.load(model_path, config_path=config_path, use_cuda=use_cuda)
        _cache[key] = voice
        return voice


def clear_cache() -> None:
    """Drop all cached voices (useful in tests / after toggling TTS settings)."""
    with _lock:
        _cache.clear()
