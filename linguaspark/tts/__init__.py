"""Local TTS synthesis via Piper (piper-tts).

Experimental feature: the user supplies a Piper voice model (``.onnx`` +
``.onnx.json``) and LinguaSpark embeds the rendered audio into the .apkg.
"""

from __future__ import annotations

from linguaspark.tts.cache import get_engine
from linguaspark.tts.piper_engine import PiperEngine, TTSError


__all__ = ["PiperEngine", "TTSError", "get_engine"]
