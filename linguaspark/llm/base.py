"""Abstract base class + shared helpers for LLM providers."""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any, Callable, Iterable, List, Optional

from pydantic import ValidationError

from linguaspark.config import BATCH_SIZE
from linguaspark.models.card import BatchResponse, VocabCard
from linguaspark.utils.parsers import chunked


class LLMProvider(ABC):
    """Common interface every concrete provider must implement."""

    name: str = "base"
    requires_api_key: bool = True

    def __init__(
        self,
        model: str,
        input_language: str,
        output_language: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        max_retries: int = 1,
    ) -> None:
        # Read requires_api_key via self so subclasses can flip it per
        # instance (e.g. Ollama local vs Ollama cloud).
        if getattr(self, "requires_api_key", False) and not api_key:
            raise ValueError(
                f"{self.name} provider requires an API key"
            )
        if not input_language or not input_language.strip():
            raise ValueError("input_language is required")
        if not output_language or not output_language.strip():
            raise ValueError("output_language is required")
        self.model = model
        self.input_language = input_language.strip()
        self.output_language = output_language.strip()
        self.api_key = api_key
        self.base_url = base_url
        self.max_retries = max_retries

    # ------------------------------------------------------------------ public

    def enrich_words(self, words: Iterable[str]) -> List[VocabCard]:
        """Enrich every term in `words` using fixed-size LLM batches.

        Returns a list of `VocabCard` in the same order as `words` whenever
        possible. Words that fail to enrich after retries are silently
        dropped; callers should rely on the length of the returned list
        and cross-reference by `term`.
        """
        words = [w for w in (s.strip() for s in words) if w]
        out: List[VocabCard] = []
        for batch in chunked(words, BATCH_SIZE):
            out.extend(self._enrich_batch_with_retry(batch))
        return out

    def enrich_word(self, word: str) -> VocabCard:
        """Enrich a single term. Convenience wrapper around batch enrichment."""
        results = self.enrich_words([word])
        if not results:
            raise RuntimeError(f"Failed to enrich word: {word!r}")
        return results[0]

    # ----------------------------------------------------------------- internal

    def _enrich_batch_with_retry(self, words: List[str]) -> List[VocabCard]:
        """Try `_enrich_batch` up to `max_retries + 1` times.

        Between attempts the corrective message is escalated so the model
        is told what went wrong (parse error vs. schema validation).
        """
        last_error: Optional[Exception] = None
        for attempt in range(self.max_retries + 1):
            corrective = (
                _format_corrective_message(attempt, last_error, words)
                if attempt > 0
                else None
            )
            try:
                raw = self._enrich_batch(words, corrective_message=corrective)
                cards = self._parse_batch_response(raw, expected_terms=set(words))
                if cards:
                    return cards
                last_error = ValueError("empty card list")
            except (ValidationError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
            except Exception as exc:  # network / API failures are not retried
                raise
        return []

    def _parse_batch_response(
        self,
        raw: Any,
        expected_terms: set[str],
    ) -> List[VocabCard]:
        """Coerce raw LLM output into a validated list of `VocabCard`."""
        payload = _coerce_to_payload(raw)
        # Inject the input language so individual cards don't need to repeat it.
        for entry in payload.get("cards", []):
            if isinstance(entry, dict) and not entry.get("language"):
                entry["language"] = self.input_language
        batch = BatchResponse.model_validate(payload)
        # Filter to terms the caller actually asked for (drop hallucinated rows).
        valid = [c for c in batch.cards if c.term.casefold() in {t.casefold() for t in expected_terms}]
        return valid

    # -------------------------------------------------------------- abstract

    @abstractmethod
    def _enrich_batch(
        self,
        words: List[str],
        corrective_message: Optional[str] = None,
    ) -> Any:
        """Send a batch of words to the LLM and return its raw response.

        Implementations should return something `_coerce_to_payload` can
        interpret (a dict with a 'cards' key, a JSON string, or a list of
        dicts).
        """


# ===================================================================== helpers


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def _coerce_to_payload(raw: Any) -> dict:
    """Best-effort conversion of provider-specific output to a dict."""
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, list):
        return {"cards": raw}
    if isinstance(raw, str):
        text = raw.strip()
        # Strip ```json ... ``` fences if present.
        m = _JSON_FENCE_RE.search(text)
        if m:
            text = m.group(1).strip()
        return json.loads(text)
    raise ValueError(f"Unsupported raw response type: {type(raw).__name__}")


def _format_corrective_message(
    attempt: int,
    error: Optional[Exception],
    words: List[str],
) -> str:
    """Build the corrective text appended to the user message on a retry."""
    base = (
        "Your previous response could not be parsed. "
        "Respond again with ONLY a valid JSON object matching the schema. "
        "Do not include any commentary, code fences, or markdown."
    )
    if error is None:
        return base
    hint = f" Last error: {type(error).__name__}: {str(error)[:200]}"
    if isinstance(error, ValidationError):
        hint += " Make sure every required field is present and non-empty."
    return base + hint


class _CallableProvider(LLMProvider):
    """Lightweight provider for tests: lets the caller supply a function."""

    name = "callable"
    requires_api_key = False

    def __init__(self, fn: Callable[[List[str], Optional[str]], Any], **kwargs) -> None:
        super().__init__(
            model=kwargs.pop("model", "test"),
            input_language=kwargs.pop("input_language", "English"),
            output_language=kwargs.pop("output_language", "English"),
            **kwargs,
        )
        self._fn = fn

    def _enrich_batch(self, words: List[str], corrective_message: Optional[str] = None) -> Any:
        return self._fn(words, corrective_message)
