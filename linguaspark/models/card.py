"""Pydantic data contracts for vocabulary cards and LLM responses."""

from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class VocabCard(BaseModel):
    """A single enriched flashcard.

    The field set is what the LLM must produce and what `anki.builder` will
    render into the Anki template.
    """

    term: str = Field(..., description="The vocabulary term being defined.")
    translation_primary: str = Field(
        ...,
        description=(
            "Direct, concise translation of the term itself into the "
            "output language (the language used for all explanatory "
            "content on the back of the card). This is the primary answer "
            "the learner sees first. If input language == output language, "
            "this is still the headline restatement of the term."
        ),
    )
    pos: str = Field(
        ...,
        description=(
            "Grammatical part of speech, e.g. 'noun', 'transitive verb', "
            "'adjective', 'adverb'."
        ),
    )
    definition: str = Field(
        ...,
        description=(
            "Accurate, concise definition written in the output language, "
            "tailored for flashcard recall. Secondary — appears below the "
            "direct translation on the back."
        ),
    )
    phonetics: str = Field(
        ...,
        description=(
            "IPA transcription, pitch/stress markers, or native syllabary "
            "(furigana/pinyin/romaji) where applicable."
        ),
    )
    example: str = Field(
        ...,
        description="A natural, native-level sentence demonstrating the term in context.",
    )
    translation: str = Field(
        ...,
        description=(
            "Translation of the example sentence into the output language. "
            "Distinct from `translation_primary`, which translates the term."
        ),
    )
    mnemonic: str = Field(
        ...,
        description=(
            "A high-retention visual or phonetic association bridging the term "
            "into long-term memory."
        ),
    )
    language: str = Field(
        default="",
        description=(
            "Input language the term belongs to (the language of the "
            "supplied word + example sentence)."
        ),
    )
    # The next two are populated client-side (by the TTS engine at export time).
    # The LLM never fills them; genanki only needs the basename of the audio file.
    audio_term: str = Field(
        default="",
        description=(
            "Client-side field. Holds the rendered audio HTML fragment "
            "(<audio> + clickable 🔊 button) for the term — produced at "
            "export time by the TTS engine. Empty when TTS is disabled or "
            "synthesis failed."
        ),
    )
    audio_example: str = Field(
        default="",
        description=(
            "Client-side field. Holds the rendered audio HTML fragment for "
            "the example sentence — produced at export time. Empty when TTS "
            "is disabled or synthesis failed."
        ),
    )

    def to_anki_fields(self) -> List[str]:
        """Return fields in the order expected by the Anki model template."""
        return [
            self.term,
            self.translation_primary,
            self.pos,
            self.phonetics,
            self.definition,
            self.example,
            self.translation,
            self.mnemonic,
            self.language,
            self.audio_term,
            self.audio_example,
        ]

    @classmethod
    def anki_field_names(cls) -> List[str]:
        return [
            "Term",
            "Translation",
            "POS",
            "Phonetics",
            "Definition",
            "Example",
            "Example Translation",
            "Mnemonic",
            "Language",
            "AudioTerm",
            "AudioExample",
        ]


class BatchResponse(BaseModel):
    """Wrapper for a batch of cards returned by an LLM in a single call."""

    cards: List[VocabCard]
