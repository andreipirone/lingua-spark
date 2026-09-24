"""Top input panel: word list, deck name, languages, provider, API key, actions."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from linguaspark.config import (
    DEFAULT_DECK_NAME,
    DEFAULT_INPUT_LANGUAGE,
    DEFAULT_OUTPUT_LANGUAGE,
    QSETTINGS_APP,
    QSETTINGS_ORG,
    SETTING_API_KEY_PREFIX,
    SETTING_DECK_THEME,
    SETTING_LAST_DECK_NAME,
    SETTING_LAST_INPUT_LANGUAGE,
    SETTING_LAST_LANGUAGE,
    SETTING_LAST_MODEL,
    SETTING_LAST_OUTPUT_LANGUAGE,
    SETTING_LAST_PROVIDER,
    SUPPORTED_LANGUAGES,
    SUPPORTED_PROVIDERS,
    api_key_setting_key,
)
from linguaspark.llm.factory import provider_metadata
from linguaspark.utils.parsers import parse_word_list


class InputPanel(QWidget):
    """User-facing input form. Emits `process_requested` and `export_requested`."""

    process_requested = Signal(list)            # list[str]
    export_requested = Signal()
    stop_requested = Signal()
    regenerate_requested = Signal(str)          # term

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._settings = _make_settings()
        self._provider_requires_key: dict[str, bool] = {
            meta["key"]: meta["requires_key"] for meta in provider_metadata()
        }
        self._build_ui()
        self._restore_settings()
        self._install_shortcuts()

    # ------------------------------------------------------------------ build

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 8)
        root.setSpacing(10)

        # --- Words input ---
        words_label = QLabel("Vocabulary")
        words_label.setObjectName("sectionTitle")
        root.addWidget(words_label)

        self.words_edit = QPlainTextEdit()
        self.words_edit.setPlaceholderText(
            "Paste or type one word per line, or load a .txt file…"
        )
        self.words_edit.setMinimumHeight(160)
        root.addWidget(self.words_edit, 1)

        load_row = QHBoxLayout()
        self.load_button = QPushButton("Load .txt…")
        self.load_button.setObjectName("secondary")
        self.load_button.clicked.connect(self._on_load_file)
        load_row.addWidget(self.load_button)
        load_row.addStretch(1)

        self.word_count_label = QLabel("0 words")
        self.word_count_label.setObjectName("wordCount")
        load_row.addWidget(self.word_count_label)
        root.addLayout(load_row)

        self.words_edit.textChanged.connect(self._update_word_count)

        # --- Configuration grid ---
        config_label = QLabel("Configuration")
        config_label.setObjectName("sectionTitle")
        root.addWidget(config_label)

        form = QGridLayout()
        form.setHorizontalSpacing(12)
        form.setVerticalSpacing(8)

        form.addWidget(QLabel("Deck Name"), 0, 0)
        self.deck_name_edit = QLineEdit(DEFAULT_DECK_NAME)
        form.addWidget(self.deck_name_edit, 0, 1, 1, 3)

        # Row 1 — input language (the user's word list) + output language
        # (the language used for definitions / translations on the back).
        form.addWidget(QLabel("Input Language"), 1, 0)
        self.input_language_combo = QComboBox()
        self.input_language_combo.addItems(SUPPORTED_LANGUAGES)
        self.input_language_combo.setCurrentText(DEFAULT_INPUT_LANGUAGE)
        self.input_language_combo.setToolTip(
            "Language of the words you paste, and of the generated "
            "example sentences. Shown on the front of every card."
        )
        form.addWidget(self.input_language_combo, 1, 1)

        form.addWidget(QLabel("Output Language"), 1, 2)
        self.output_language_combo = QComboBox()
        self.output_language_combo.addItems(SUPPORTED_LANGUAGES)
        self.output_language_combo.setCurrentText(DEFAULT_OUTPUT_LANGUAGE)
        self.output_language_combo.setToolTip(
            "Language used for all explanatory content on the back of "
            "each card: direct translation of the term, definition, "
            "translation of the example sentence, and the memory mnemonic."
        )
        form.addWidget(self.output_language_combo, 1, 3)

        # Row 2 — provider + model.
        form.addWidget(QLabel("Provider"), 2, 0)
        self.provider_combo = QComboBox()
        for meta in provider_metadata():
            self.provider_combo.addItem(meta["label"], meta["key"])
        form.addWidget(self.provider_combo, 2, 1)

        form.addWidget(QLabel("Model"), 2, 2)
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("Enter model name (required)")
        form.addWidget(self.model_edit, 2, 3)

        # Row 3 — local-Ollama URL (visible only when local Ollama is selected).
        self.ollama_label = QLabel("Ollama URL (local)")
        self.ollama_edit = QLineEdit("http://localhost:11434")
        form.addWidget(self.ollama_label, 3, 0)
        form.addWidget(self.ollama_edit, 3, 1, 1, 3)

        root.addLayout(form)

        # --- API key row (visible only for key-required providers) ---
        key_row = QHBoxLayout()
        key_row.setSpacing(8)
        self.api_key_label = QLabel("API Key")
        self.api_key_edit = QLineEdit()
        self.api_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_edit.setPlaceholderText("Paste key, then Save (stored locally)")
        self.save_key_button = QPushButton("Save")
        self.save_key_button.setObjectName("small secondary")
        self.save_key_button.clicked.connect(self._on_save_key)
        self.forget_key_button = QPushButton("Forget")
        self.forget_key_button.setObjectName("small secondary")
        self.forget_key_button.clicked.connect(self._on_forget_key)
        key_row.addWidget(self.api_key_label)
        key_row.addWidget(self.api_key_edit, 1)
        key_row.addWidget(self.save_key_button)
        key_row.addWidget(self.forget_key_button)
        root.addLayout(key_row)

        self.provider_combo.currentIndexChanged.connect(self._refresh_provider_ui)
        self._refresh_provider_ui()

        # --- Action row ---
        actions = QHBoxLayout()
        actions.setSpacing(8)
        self.process_button = QPushButton("Process Vocabulary")
        self.process_button.setShortcut(QKeySequence("Ctrl+Return"))
        self.process_button.setToolTip("Enrich every word in the input list (Ctrl+Return)")
        self.process_button.clicked.connect(self._on_process_clicked)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("danger")
        self.stop_button.clicked.connect(self.stop_requested.emit)
        self.stop_button.setEnabled(False)
        self.export_button = QPushButton("Export to Anki…")
        self.export_button.setShortcut(QKeySequence("Ctrl+E"))
        self.export_button.setToolTip("Generate the .apkg file (Ctrl+E)")
        self.export_button.clicked.connect(self.export_requested.emit)
        self.clear_button = QPushButton("Clear Table")
        self.clear_button.setObjectName("secondary")
        actions.addWidget(self.process_button)
        actions.addWidget(self.stop_button)
        actions.addStretch(1)
        # Always-visible deck-theme dropdown (persistent across sessions).
        actions.addWidget(QLabel("Deck Theme:"))
        self.deck_theme_combo = QComboBox()
        self.deck_theme_combo.addItem("Light", "light")
        self.deck_theme_combo.addItem("Dark", "dark")
        self.deck_theme_combo.setToolTip(
            "Light — white background, dark text (default).\n"
            "Dark — navy background, light text."
        )
        self.deck_theme_combo.setCurrentIndex(0)
        self.deck_theme_combo.currentIndexChanged.connect(self._on_deck_theme_changed)
        actions.addWidget(self.deck_theme_combo)
        actions.addWidget(self.clear_button)
        actions.addWidget(self.export_button)
        root.addLayout(actions)

    def _install_shortcuts(self) -> None:
        """Wire Ctrl+Return (process) and Ctrl+L (load .txt)."""
        QShortcut(QKeySequence("Ctrl+Return"), self,
                  activated=self._on_process_clicked)
        QShortcut(QKeySequence("Ctrl+L"), self,
                  activated=self._on_load_file)

    def _on_deck_theme_changed(self, _index: int) -> None:
        """Persist the deck-theme preference whenever the user changes it."""
        self._settings.setValue(SETTING_DECK_THEME, self.deck_theme())
        self._settings.sync()

    # --------------------------------------------------------------- helpers

    def _refresh_provider_ui(self) -> None:
        provider_key = self.current_provider()
        requires_key = self._provider_requires_key.get(provider_key, True)
        self.api_key_label.setVisible(requires_key)
        self.api_key_edit.setVisible(requires_key)
        self.save_key_button.setVisible(requires_key)
        self.forget_key_button.setVisible(requires_key)

        # Local-URL field only makes sense for the local Ollama row.
        is_local_ollama = provider_key == "ollama"
        self.ollama_label.setVisible(is_local_ollama)
        self.ollama_edit.setVisible(is_local_ollama)

        # No defaults: the model field is always left to the user.

    def _update_word_count(self) -> None:
        n = len(self.words())
        self.word_count_label.setText(f"{n} word{'s' if n != 1 else ''}")

    def _on_load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Load word list", "", "Text Files (*.txt);;All Files (*)"
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            QMessageBox.critical(self, "Load failed", f"Could not read file:\n{exc}")
            return
        self.words_edit.setPlainText(content)

    def _on_save_key(self) -> None:
        provider_key = self.current_provider()
        key = self.api_key_edit.text().strip()
        if not key:
            QMessageBox.warning(self, "API Key", "Please enter a key before saving.")
            return
        self._settings.setValue(api_key_setting_key(provider_key), key)
        self._settings.sync()
        self.api_key_edit.clear()
        QMessageBox.information(
            self, "API Key saved",
            f"API key for {provider_key} stored locally. "
            "It will be auto-loaded next session.",
        )

    def _on_forget_key(self) -> None:
        provider_key = self.current_provider()
        self._settings.remove(api_key_setting_key(provider_key))
        self._settings.sync()
        self.api_key_edit.clear()
        QMessageBox.information(
            self, "API Key forgotten",
            f"Stored key for {provider_key} has been removed.",
        )

    # ------------------------------------------------------------- public api

    def words(self) -> List[str]:
        return parse_word_list(self.words_edit.toPlainText())

    def set_words(self, words: List[str]) -> None:
        self.words_edit.setPlainText("\n".join(words))

    def current_provider(self) -> str:
        return self.provider_combo.currentData() or SUPPORTED_PROVIDERS[0]

    def api_key(self) -> Optional[str]:
        provider_key = self.current_provider()
        if not self._provider_requires_key.get(provider_key, True):
            return None
        # Prefer the in-memory field if the user is currently editing it.
        typed = self.api_key_edit.text().strip()
        if typed:
            return typed
        stored = self._settings.value(api_key_setting_key(provider_key), "", type=str)
        return stored.strip() or None

    def ollama_base_url(self) -> Optional[str]:
        if self.current_provider() != "ollama":
            return None
        url = self.ollama_edit.text().strip()
        return url or None

    def deck_name(self) -> str:
        return self.deck_name_edit.text().strip() or DEFAULT_DECK_NAME

    def language(self) -> str:
        """Legacy single-language accessor — returns the input language.

        New code should call :meth:`input_language` and
        :meth:`output_language` separately.
        """
        return self.input_language()

    def input_language(self) -> str:
        """Language of the supplied words + generated example sentences."""
        return self.input_language_combo.currentText().strip() or DEFAULT_INPUT_LANGUAGE

    def output_language(self) -> str:
        """Language used for definitions / translations / mnemonics."""
        return self.output_language_combo.currentText().strip() or DEFAULT_OUTPUT_LANGUAGE

    def model(self) -> str:
        """Return the typed model name, or an empty string if blank."""
        return self.model_edit.text().strip()

    def deck_theme(self) -> str:
        """Return the deck theme to bake into the next exported .apkg.

        Returns "dark" if the dropdown shows "Dark", otherwise "light".
        """
        data = self.deck_theme_combo.currentData()
        return data if data in ("light", "dark") else "light"

    def set_busy(self, busy: bool) -> None:
        self.process_button.setEnabled(not busy)
        self.stop_button.setEnabled(busy)
        self.export_button.setEnabled(not busy)
        self.clear_button.setEnabled(not busy)
        self.load_button.setEnabled(not busy)
        self.words_edit.setReadOnly(busy)

    def set_export_enabled(self, enabled: bool) -> None:
        self.export_button.setEnabled(enabled)

    def save_settings(self) -> None:
        self._settings.setValue(SETTING_LAST_DECK_NAME, self.deck_name_edit.text())
        self._settings.setValue(SETTING_LAST_INPUT_LANGUAGE, self.input_language())
        self._settings.setValue(SETTING_LAST_OUTPUT_LANGUAGE, self.output_language())
        # Legacy key — keep writing so older app versions still find a value.
        self._settings.setValue(SETTING_LAST_LANGUAGE, self.input_language())
        self._settings.setValue(SETTING_LAST_PROVIDER, self.current_provider())
        self._settings.setValue(SETTING_LAST_MODEL, self.model_edit.text())
        if self.current_provider() == "ollama":
            self._settings.setValue("last_ollama_url", self.ollama_edit.text())
        self._settings.setValue(SETTING_DECK_THEME, self.deck_theme())
        self._settings.sync()

    # --------------------------------------------------------------- internal

    def _restore_settings(self) -> None:
        deck = self._settings.value(SETTING_LAST_DECK_NAME, DEFAULT_DECK_NAME, type=str)
        self.deck_name_edit.setText(deck)

        # Restore input language. Prefer the new key, fall back to legacy.
        in_lang = self._settings.value(SETTING_LAST_INPUT_LANGUAGE, "", type=str)
        if not in_lang:
            in_lang = self._settings.value(SETTING_LAST_LANGUAGE, DEFAULT_INPUT_LANGUAGE, type=str)
        idx = self.input_language_combo.findText(in_lang)
        if idx >= 0:
            self.input_language_combo.setCurrentIndex(idx)

        # Restore output language. Default to input language if never set.
        out_lang = self._settings.value(SETTING_LAST_OUTPUT_LANGUAGE, "", type=str)
        if not out_lang:
            out_lang = in_lang or DEFAULT_OUTPUT_LANGUAGE
        idx = self.output_language_combo.findText(out_lang)
        if idx >= 0:
            self.output_language_combo.setCurrentIndex(idx)

        provider = self._settings.value(SETTING_LAST_PROVIDER, SUPPORTED_PROVIDERS[0], type=str)
        idx = self.provider_combo.findData(provider)
        if idx >= 0:
            self.provider_combo.setCurrentIndex(idx)

        # No defaults: leave the model field empty when nothing was previously saved.
        self.model_edit.setText(self._settings.value(SETTING_LAST_MODEL, "", type=str))

        ollama_url = self._settings.value("last_ollama_url", "http://localhost:11434", type=str)
        self.ollama_edit.setText(ollama_url)

        # Pre-load saved API key into the field (read-only-ish — user can overwrite).
        saved_key = self._settings.value(api_key_setting_key(provider), "", type=str)
        if saved_key:
            self.api_key_edit.setText(saved_key)

        # Restore deck-theme preference; block signals so we don't re-write
        # back what we just read.
        theme = self._settings.value(SETTING_DECK_THEME, "light", type=str)
        if theme not in ("light", "dark"):
            theme = "light"
        idx = self.deck_theme_combo.findData(theme)
        self.deck_theme_combo.blockSignals(True)
        self.deck_theme_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.deck_theme_combo.blockSignals(False)

    def _on_process_clicked(self) -> None:
        words = self.words()
        if not words:
            QMessageBox.warning(
                self, "No words",
                "Please add at least one word before processing.",
            )
            return
        if not self.model().strip():
            QMessageBox.warning(
                self, "Model required",
                "Please enter a model name (e.g. 'gpt-4o-mini', "
                "'llama3.1', 'gemma3:cloud') before processing.",
            )
            return
        provider_key = self.current_provider()
        if self._provider_requires_key.get(provider_key, True) and not self.api_key():
            QMessageBox.warning(
                self, "API key required",
                f"Please enter and save an API key for {provider_key}.",
            )
            return
        self.save_settings()
        self.process_requested.emit(words)


def _make_settings():
    """Construct a QSettings instance scoped to LinguaSpark."""
    from PySide6.QtCore import QSettings

    return QSettings(QSETTINGS_ORG, QSETTINGS_APP)
