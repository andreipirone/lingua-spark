"""genanki deck/package assembly for LinguaSpark cards."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List

import genanki

from linguaspark.config import DECK_ID, MODEL_ID
from linguaspark.models.card import VocabCard

from .templates import (
    CardTheme,
    get_answer_format,
    get_css,
    get_question_format,
)


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


def build_apkg(
    deck_name: str,
    cards: Iterable[VocabCard],
    out_path: str | Path,
    theme: CardTheme = "light",
) -> Path:
    """Assemble cards into an `.apkg` file at `out_path`.

    `theme` selects the embedded card CSS ("light" or "dark").

    Returns the resolved output path.
    """
    model = build_model(theme)
    deck = build_deck(deck_name)

    card_list: List[VocabCard] = list(cards)
    for card in card_list:
        deck.add_note(genanki.Note(model=model, fields=card.to_anki_fields()))

    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    package = genanki.Package(deck)
    package.write_to_file(str(out_path))
    return out_path
