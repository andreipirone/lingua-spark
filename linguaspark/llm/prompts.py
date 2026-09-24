"""Prompt templates shared across providers."""

from __future__ import annotations

import json
from typing import List

from linguaspark.models.card import VocabCard


def build_system_prompt(
    input_language: str,
    output_language: str,
) -> str:
    """System prompt that establishes the model's role + two-language contract.

    - ``input_language`` is the language of the supplied words (and of the
      generated example sentences).
    - ``output_language`` is the language of all explanatory content on the
      back of the card: the ``translation_primary`` (direct translation of
      the term), the ``definition``, the ``translation`` (example sentence
      translation), and the ``mnemonic``.
    """
    same_language = input_language.strip().casefold() == output_language.strip().casefold()
    if same_language:
        instruction = (
            f"All fields are written in {input_language}. Definitions must "
            f"be concise and learner-friendly in {input_language}. Mnemonics "
            f"should reference vivid, concrete imagery that resonates with "
            f"a {input_language} speaker."
        )
    else:
        instruction = (
            f"The vocabulary terms AND the example sentences are in "
            f"{input_language}; write them using natural, idiomatic "
            f"{input_language}. All explanatory fields on the back of the "
            f"card (translation of the term, definition, translation of the "
            f"example sentence, mnemonic) must be written in "
            f"{output_language}. The learner's native language is "
            f"{output_language} — make every explanation feel native, not "
            f"machine-translated."
        )
    return (
        "You are LinguaSpark, an expert linguist and vocabulary tutor. "
        "For each term you receive, you produce a single flashcard object "
        "with the exact fields defined in the JSON schema. "
        "`translation_primary` is the direct, concise translation of the "
        f"term itself into {output_language} — this is the headline answer "
        "the learner sees first. The `translation` field is separate and "
        f"translates the example SENTENCE into {output_language}. "
        f"{instruction} "
        "Example sentences must be natural, native-level, and demonstrate "
        "the term in realistic context. Mnemonics must be vivid, concrete, "
        "and easy to recall. Respond with ONLY a JSON object — no prose, no "
        "markdown, no fences."
    )


def build_user_prompt(words: List[str], input_language: str) -> str:
    """User prompt listing the words and instructing the JSON output shape."""
    schema_hint = json.dumps(VocabCard.model_json_schema(), indent=2)
    return (
        f"Enrich each of the following {input_language} words into a "
        f"flashcard.\n\n"
        f"Words (one per line, in order):\n" + "\n".join(words) + "\n\n"
        "Return a JSON object with this exact shape:\n"
        '{\n  "cards": [ <card>, <card>, ... ]\n}\n'
        "Each <card> must conform to this schema:\n"
        f"{schema_hint}\n\n"
        "Produce exactly one card per word, preserving the input order. "
        "Do NOT include any field other than those listed above."
    )


def build_corrective_message(extra: str) -> str:
    """Optional trailing note appended to a retry user message."""
    return extra
