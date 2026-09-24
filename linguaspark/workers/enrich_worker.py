"""Background worker that streams VocabCards from an LLM provider into the UI.

The worker runs in its own `QThread`, emitting Qt signals for each card as it
becomes available so the table can populate incrementally without freezing the
main window. It also exposes a `stop()` flag for cooperative cancellation.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from PySide6.QtCore import QThread, Signal

from linguaspark.config import BATCH_SIZE
from linguaspark.llm.base import LLMProvider
from linguaspark.models.card import VocabCard
from linguaspark.utils.parsers import chunked


class EnrichWorker(QThread):
    """Run enrichment in the background and stream cards to the UI thread."""

    card_ready = Signal(object)        # emits VocabCard
    progress = Signal(int, int)        # done, total
    word_failed = Signal(str, str)     # word, error_message
    finished_success = Signal(int)     # total cards successfully produced
    failed = Signal(str)               # fatal error message

    def __init__(
        self,
        provider: LLMProvider,
        words: Iterable[str],
        batch_size: int = BATCH_SIZE,
    ) -> None:
        super().__init__()
        self.provider = provider
        self._words: List[str] = [w for w in (s.strip() for s in words) if w]
        self._batch_size = batch_size
        self._stop_requested = False

    # ----------------------------------------------------------- public api

    def stop(self) -> None:
        """Request cooperative cancellation. Safe to call from any thread."""
        self._stop_requested = True

    def total(self) -> int:
        return len(self._words)

    # ----------------------------------------------------------- main loop

    def run(self) -> None:  # noqa: D401 — QThread API
        if not self._words:
            self.finished_success.emit(0)
            return

        try:
            produced = 0
            for batch in chunked(self._words, self._batch_size):
                if self._stop_requested:
                    break

                # Walk inside the batch so the table updates even before a
                # full batch resolves — when the provider returns the whole
                # batch in one shot we still fan out per-card below.
                batch_cards: List[VocabCard] = []
                try:
                    batch_cards = self.provider.enrich_words(batch)
                except Exception as exc:  # noqa: BLE001 — surfaced to UI
                    for word in batch:
                        self.word_failed.emit(word, str(exc))
                    self.progress.emit(
                        min(produced + len(batch), len(self._words)),
                        len(self._words),
                    )
                    continue

                seen_in_batch = set()
                for card in batch_cards:
                    key = card.term.casefold()
                    if key in seen_in_batch:
                        continue
                    seen_in_batch.add(key)
                    self.card_ready.emit(card)
                    produced += 1
                # Surface words the provider dropped (no card returned).
                returned = {c.term.casefold() for c in batch_cards}
                for word in batch:
                    if word.casefold() not in returned:
                        self.word_failed.emit(word, "no card returned")
                self.progress.emit(
                    min(produced + len(returned), len(self._words)),
                    len(self._words),
                )

            self.finished_success.emit(produced)
        except Exception as exc:  # noqa: BLE001 — top-level safety net
            self.failed.emit(str(exc))
