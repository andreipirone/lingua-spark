"""genanki deck/package assembly for LinguaSpark cards."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Callable, Iterable, List, Optional, Protocol

import genanki

from linguaspark.config import DECK_ID, MODEL_ID
from linguaspark.models.card import VocabCard

from .templates import (
    CardTheme,
    get_answer_format,
    get_css,
    get_question_format,
)


class _TTSEngineProtocol(Protocol):
    """Minimal interface required by `build_apkg` for TTS."""

    def synth_wav_bytes(self, text: str) -> bytes: ...


ProgressCallback = Callable[[int, int], None]
"""Optional callback invoked as `(done, total)` after each card is processed
during a TTS-enabled export. Used by the GUI to update a progress bar."""


def build_model(theme: CardTheme = "light") -> genanki.Model:
    """Construct the genanki Model used by every LinguaSpark card.

    `theme` selects the embedded card CSS ("light" or "dark"). Anki caches
    models by ID, so re-exporting with a different theme creates a new
    model entry in the user's collection (previous notes are unaffected).
    """
    return genanki.Model(
        MODEL_ID,
        "LinguaSpark Model",
        fields=[{"name": name} for name in VocabCard.anki_field_names()],
        templates=[
            {
                "name": "LinguaSpark Card",
                "qfmt": get_question_format(),
                "afmt": get_answer_format(),
            }
        ],
        css=get_css(theme),
    )


def build_deck(deck_name: str) -> genanki.Deck:
    """Construct an empty LinguaSpark deck with the canonical model."""
    return genanki.Deck(DECK_ID, deck_name)


def _audio_basename(seed: str, role: str) -> str:
    """Stable, flat basename (no subdir) for an audio file inside the .apkg.

    Anki stores media files in a flat ``collection.media/`` directory, so
    subdirectories in filenames don't survive a normal Anki import and the
    file lookup silently fails. Using a flat basename of the form
    ``<hash>_term.wav`` keeps references valid on both the .apkg side and
    Anki's media collection.
    """
    h = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:12]
    return f"ls_{h}_{role}.wav"


def _audio_html(basename: str, role: str) -> str:
    """Anki-renderable audio fragment.

    Anki's web view is strict about CSP / inline JS, so we use Anki's
    built-in ``[sound:filename]`` syntax. Anki rewrites these references
    to its renamed ``collection.media`` filenames at import time, so the
    lookup is reliable.

    The fragment is the documented ``[sound:]`` placeholder plus a small
    emoji marker — clicking the placeholder inside Anki plays the audio.
    """
    if not basename:
        return ""
    # Anki's [sound:] tag is invisible-ish: it renders the speaker glyph +
    # attaches the audio so a user click plays it. We surround it with
    # the visible "🔊" marker our CSS styles via ``.audio-btn`` class so
    # learners see a clear play affordance on both the front (term) and
    # back (example sentence).
    return f'<span class="audio-btn">🔊&nbsp;[sound:{basename}]</span>'


def build_apkg(
    deck_name: str,
    cards: Iterable[VocabCard],
    out_path: str | Path,
    theme: CardTheme = "light",
    tts_engine: Optional[_TTSEngineProtocol] = None,
    progress: Optional[ProgressCallback] = None,
) -> Path:
    """Assemble cards into an `.apkg` file at `out_path`.

    Parameters
    ----------
    deck_name, theme:
        Standard deck identity + CSS theme.
    tts_engine:
        Optional Piper TTS wrapper. When provided, every card gets two
        audio clips synthesised (term + example sentence) and embedded
        via genanki's ``media_files``. Cards where synthesis fails get
        their audio field left empty; the export still succeeds.
    progress:
        Optional ``(done, total) -> None`` callback invoked after each
        card's audio is rendered. Total counts every card in ``cards``;
        done counts cards whose audio step has finished.

    Returns the resolved output path.
    """
    model = build_model(theme)
    deck = build_deck(deck_name)
    card_list: List[VocabCard] = list(cards)

    media_files: List[Path] = []
    total = len(card_list)

    for index, card in enumerate(card_list, 1):
        if tts_engine is not None:
            for role, source in (("term", card.term), ("example", card.example)):
                if not source or not source.strip():
                    continue
                basename = _audio_basename(f"{card.term}|{role}", role)
                try:
                    wav_bytes = tts_engine.synth_wav_bytes(source)
                except Exception as exc:  # noqa: BLE001
                    print(
                        f"[linguaspark TTS] synthesis failed for "
                        f"{card.term!r} ({role}): {exc}"
                    )
                    continue
                audio_path = Path(out_path).parent / basename
                audio_path.parent.mkdir(parents=True, exist_ok=True)
                audio_path.write_bytes(wav_bytes)
                media_files.append(audio_path)
                # Keep the basename on the dataclass for round-tripping, but
                # swap to the rendered HTML fragment that the Anki template
                # actually substitutes via `{{AudioTerm}}` / `{{AudioExample}}`.
                if role == "term":
                    card.audio_term = _audio_html(basename, "term")
                else:
                    card.audio_example = _audio_html(basename, "example")
        if progress is not None:
            progress(index, total)

    for card in card_list:
        deck.add_note(genanki.Note(model=model, fields=card.to_anki_fields()))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    package = genanki.Package(deck)
    if media_files:
        package.media_files = [str(p) for p in media_files]
    package.write_to_file(str(out_path))
    return out_path


__all__ = ["build_apkg", "build_deck", "build_model"]


def audio_html_for(basename: str, role: str) -> str:
    """Public helper so UI code can preview the rendered audio fragment."""
    return _audio_html(basename, role)
