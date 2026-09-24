"""Thin wrapper around ``piper-tts`` for batch synthesis.

Usage::

    engine = PiperEngine("/path/to/en_US-lessac-medium.onnx")
    wav_bytes = engine.synth_wav_bytes("Welcome to the world.")

The engine caches its loaded `PiperVoice` so repeated calls share the same
ONNX runtime session.
"""

from __future__ import annotations

import io
import wave
from pathlib import Path
from typing import Optional


class TTSError(RuntimeError):
    """Raised when Piper fails to load or synthesize audio."""


class PiperEngine:
    """High-level Piper TTS wrapper.

    Parameters mirror Piper's :class:`piper.PiperVoice.load` and
    :class:`piper.SynthesisConfig` knobs.
    """

    def __init__(
        self,
        onnx_path: str | Path,
        config_path: Optional[str | Path] = None,
        speaker_id: Optional[int] = None,
        length_scale: Optional[float] = None,
        noise_scale: Optional[float] = None,
        noise_w_scale: Optional[float] = None,
        use_voice_defaults: bool = True,
    ) -> None:
        self.onnx_path = Path(onnx_path)
        self.config_path = (
            Path(config_path)
            if config_path
            else self.onnx_path.with_suffix(self.onnx_path.suffix + ".json")
        )
        if not self.onnx_path.is_file():
            raise TTSError(
                f"Piper voice model not found: {self.onnx_path}"
            )
        if not self.config_path.is_file():
            raise TTSError(
                f"Piper config (.onnx.json) not found next to the model: "
                f"{self.config_path}"
            )

        self._speaker_id = speaker_id
        self._length_scale = length_scale
        self._noise_scale = noise_scale
        self._noise_w_scale = noise_w_scale
        # When True (default), the engine ignores the four parameters above
        # and lets Piper use the values it baked into the voice model at
        # training time. This is what the `piper` CLI does and — critically
        # — what makes voices sound natural. Per-language prosody
        # calibrations (e.g. German) differ noticeably between voice
        # defaults and our manual defaults.
        self._use_voice_defaults = use_voice_defaults

        # Defer importing piper + loading ONNX until the engine is actually used.
        # ``cache.get_engine`` handles memoisation across calls.
        from linguaspark.tts.cache import get_engine

        self._voice = get_engine(
            str(self.onnx_path),
            str(self.config_path),
            use_cuda=False,
        )

    # ---------------------------------------------------------------- public

    def synth_wav_bytes(self, text: str) -> bytes:
        """Synthesize ``text`` and return WAV bytes (in-memory)."""
        if not text or not text.strip():
            raise TTSError("Cannot synthesize empty text.")

        from piper import SynthesisConfig

        syn_config: Optional[SynthesisConfig] = None
        if not self._use_voice_defaults:
            # Caller has overridden the voice's recommended parameters.
            kwargs = {}
            if self._speaker_id is not None:
                kwargs["speaker_id"] = self._speaker_id
            if self._length_scale is not None:
                kwargs["length_scale"] = self._length_scale
            if self._noise_scale is not None:
                kwargs["noise_scale"] = self._noise_scale
            if self._noise_w_scale is not None:
                kwargs["noise_w_scale"] = self._noise_w_scale
            if kwargs:
                syn_config = SynthesisConfig(**kwargs)
            # When overrides are blank we keep ``syn_config = None`` so Piper
            # falls back to the voice's calibration.

        buffer = io.BytesIO()
        try:
            with wave.open(buffer, "wb") as wf:
                self._voice.synthesize_wav(text, wf, syn_config=syn_config)
        except Exception as exc:  # piper may raise from C++ ONNX runtime
            raise TTSError(f"Piper synthesis failed: {exc}") from exc

        return buffer.getvalue()
