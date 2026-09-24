"""Main window — wires InputPanel, ReviewTable, EnrichWorker, and Anki export."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QSettings, Qt
from PySide6.QtGui import QAction, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from linguaspark import __app_name__
from linguaspark.anki.builder import build_apkg
from linguaspark.anki.templates import CardTheme
from linguaspark.config import (
    QSETTINGS_APP,
    QSETTINGS_ORG,
)
from linguaspark.llm.base import LLMProvider
from linguaspark.llm.factory import build_provider
from linguaspark.models.card import VocabCard
from linguaspark.workers.enrich_worker import EnrichWorker

from .input_panel import InputPanel
from .review_table import ReviewTable
from .styles import (
    DARK,
    LIGHT,
    apply_theme,
    current_theme,
    load_theme_preference,
    save_theme_preference,
)


class MainWindow(QMainWindow):
    """Top-level window. Owns the worker thread and orchestrates the flow."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(__app_name__)
        self.resize(1200, 800)

        self._worker: Optional[EnrichWorker] = None
        self._current_provider: Optional[LLMProvider] = None
        self._settings = QSettings(QSETTINGS_ORG, QSETTINGS_APP)
        self._dark_mode_action: Optional[QAction] = None

        self._build_ui()
        self._build_menu()
        self._apply_theme(load_theme_preference())

    # ------------------------------------------------------------------ build

    def _build_ui(self) -> None:
        splitter = QSplitter(Qt.Orientation.Vertical)

        self.input_panel = InputPanel()
        self.review_table = ReviewTable()

        # Wrap input panel in a container so it doesn't grab all vertical space.
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(self.input_panel)

        splitter.addWidget(top_container)
        splitter.addWidget(self.review_table)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 600])

        self.setCentralWidget(splitter)

        self._status_label = QLabel("Ready.")
        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 1)
        self._progress_bar.setValue(0)
        self._progress_bar.setFixedWidth(220)
        status = QStatusBar()
        status.addWidget(self._status_label, 1)
        status.addPermanentWidget(self._progress_bar)
        self.setStatusBar(status)

        # --- Wire signals ---
        self.input_panel.process_requested.connect(self._on_process_requested)
        self.input_panel.export_requested.connect(self._on_export_requested)
        self.input_panel.stop_requested.connect(self._on_stop_requested)
        self.input_panel.regenerate_requested.connect(self._on_regenerate_requested)
        self.input_panel.clear_button.clicked.connect(self._on_clear_table)
        self.review_table.regenerate_requested.connect(self._on_regenerate_requested)
        self.review_table.card_changed.connect(self._sync_export_enabled)
        self.review_table.card_removed.connect(lambda *_: self._sync_export_enabled())
        self._sync_export_enabled()

    def _build_menu(self) -> None:
        menu = self.menuBar()
        file_menu = menu.addMenu("&File")

        export_action = QAction("Export to Anki…", self)
        export_action.setShortcut(QKeySequence("Ctrl+E"))
        export_action.triggered.connect(self._on_export_requested)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        quit_action = QAction("Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = menu.addMenu("&View")
        dark_action = QAction("Dark Mode", self)
        dark_action.setCheckable(True)
        dark_action.setShortcut(QKeySequence("Ctrl+D"))
        dark_action.setStatusTip("Toggle between dark and light theme")
        dark_action.setChecked(load_theme_preference().is_dark)
        dark_action.toggled.connect(self._on_dark_mode_toggled)
        view_menu.addAction(dark_action)
        self._dark_mode_action = dark_action

        help_menu = menu.addMenu("&Help")
        about_action = QAction("About LinguaSpark", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    # -------------------------------------------------------------- handlers

    def _on_process_requested(self, words: List[str]) -> None:
        if self._worker is not None and self._worker.isRunning():
            return

        try:
            provider = build_provider(
                self.input_panel.current_provider(),
                api_key=self.input_panel.api_key(),
                model=self.input_panel.model(),
                base_url=self.input_panel.ollama_base_url(),
                input_language=self.input_panel.input_language(),
                output_language=self.input_panel.output_language(),
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Provider error", str(exc))
            return

        self._current_provider = provider

        # Reset progress bar + status.
        self._progress_bar.setRange(0, max(len(words), 1))
        self._progress_bar.setValue(0)
        self._status_label.setText(
            f"Enriching {len(words)} word{'s' if len(words) != 1 else ''} via "
            f"{provider.name}…"
        )

        self._worker = EnrichWorker(provider, words)
        self._worker.card_ready.connect(self._on_card_ready)
        self._worker.progress.connect(self._on_progress)
        self._worker.word_failed.connect(self._on_word_failed)
        self._worker.finished_success.connect(self._on_worker_finished)
        self._worker.failed.connect(self._on_worker_failed)

        self.input_panel.set_busy(True)
        self._worker.start()

    def _on_stop_requested(self) -> None:
        if self._worker is None:
            return
        self._worker.stop()
        self._status_label.setText("Stopping…")

    def _on_card_ready(self, card: VocabCard) -> None:
        self.review_table.add_or_replace_card(card)

    def _on_progress(self, done: int, total: int) -> None:
        self._progress_bar.setRange(0, max(total, 1))
        self._progress_bar.setValue(done)

    def _on_word_failed(self, word: str, message: str) -> None:
        self.review_table.mark_failed(word, message)

    def _on_worker_finished(self, produced: int) -> None:
        self.input_panel.set_busy(False)
        self._progress_bar.setValue(self._progress_bar.maximum())
        self._status_label.setText(
            f"Done. {produced} card{'s' if produced != 1 else ''} ready to export."
        )
        self._worker = None

    def _on_worker_failed(self, message: str) -> None:
        self.input_panel.set_busy(False)
        self._status_label.setText("Error.")
        QMessageBox.critical(self, "Enrichment failed", message)
        self._worker = None

    def _on_dark_mode_toggled(self, checked: bool) -> None:
        theme = DARK if checked else LIGHT
        self._apply_theme(theme)
        save_theme_preference(theme)
        label = "Dark" if theme.is_dark else "Light"
        self._status_label.setText(f"Switched to {label} theme.")

    def _apply_theme(self, theme) -> None:
        app = QApplication.instance()
        if app is not None:
            apply_theme(app, theme)
            # Re-apply the failed-word marker brush using the theme's danger color.
            self.review_table.refresh_theme_colors()

    def _on_clear_table(self) -> None:
        if self._worker is not None and self._worker.isRunning():
            return
        self.review_table.clear_cards()
        self._status_label.setText("Table cleared.")
        self._sync_export_enabled()

    def _sync_export_enabled(self, *_args) -> None:
        has_cards = bool(self.review_table.cards())
        self.input_panel.set_export_enabled(has_cards)

    def _on_regenerate_requested(self, term: str) -> None:
        if self._current_provider is None:
            QMessageBox.information(
                self, "Regenerate",
                "No active provider — process some words first.",
            )
            return
        if self._worker is not None and self._worker.isRunning():
            QMessageBox.information(
                self, "Busy", "Wait for the current run to finish before regenerating."
            )
            return

        # One-off worker for a single term.
        try:
            provider = build_provider(
                self.input_panel.current_provider(),
                api_key=self.input_panel.api_key(),
                model=self.input_panel.model(),
                base_url=self.input_panel.ollama_base_url(),
                input_language=self.input_panel.input_language(),
                output_language=self.input_panel.output_language(),
            )
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Provider error", str(exc))
            return

        self._status_label.setText(f"Regenerating '{term}'…")
        self._worker = EnrichWorker(provider, [term])
        self._worker.card_ready.connect(self._on_card_ready)
        self._worker.finished_success.connect(self._on_regen_finished)
        self._worker.failed.connect(self._on_worker_failed)
        self._worker.start()

    def _on_regen_finished(self, _produced: int) -> None:
        self.input_panel.set_busy(False)
        self._status_label.setText("Regeneration complete.")
        self._worker = None

    def _on_export_requested(self) -> None:
        cards = self.review_table.cards()
        if not cards:
            QMessageBox.information(self, "Nothing to export",
                                    "Add some enriched cards first.")
            return

        # Use whatever the visible "Dark deck theme" checkbox shows right now.
        theme: CardTheme = self.input_panel.deck_theme()  # "light" or "dark"

        # Choose where to write the .apkg.
        default_name = f"{self.input_panel.deck_name().replace(' ', '_')}.apkg"
        path, _ = QFileDialog.getSaveFileName(
            self, "Export Anki deck", default_name, "Anki Package (*.apkg)"
        )
        if not path:
            return

        if not path.lower().endswith(".apkg"):
            path += ".apkg"

        try:
            out = build_apkg(self.input_panel.deck_name(), cards, path, theme=theme)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export failed", str(exc))
            return

        self._status_label.setText(
            f"Exported {len(cards)} cards ({theme} theme) to {out}"
        )
        QMessageBox.information(
            self, "Export complete",
            f"Wrote {len(cards)} cards ({theme} theme) to:\n{out}",
        )

    def _show_about(self) -> None:
        QMessageBox.about(
            self, "About LinguaSpark",
            "<b>LinguaSpark</b><br>"
            "AI-powered Anki deck builder.<br><br>"
            "Paste words, choose a provider, enrich, review, export.",
        )

    # ----------------------------------------------------------- lifecycle

    def closeEvent(self, event) -> None:  # noqa: N802 — Qt API
        if self._worker is not None and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        self.input_panel.save_settings()
        super().closeEvent(event)
