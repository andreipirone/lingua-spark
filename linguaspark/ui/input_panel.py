"""Top input panel: word list, deck name, languages, provider, API key, actions."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QIcon, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QStyle,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from linguaspark.config import (
    DEFAULT_DECK_NAME,
    DEFAULT_INPUT_LANGUAGE,
    DEFAULT_OUTPUT_LANGUAGE,
    DEFAULT_TTS_LENGTH_SCALE,
    DEFAULT_TTS_NOISE_SCALE,
    DEFAULT_TTS_NOISE_W,
    DEFAULT_TTS_SPEAKER_ID,
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
    SETTING_TTS_CONFIG_PATH,
    SETTING_TTS_ENABLED,
    SETTING_TTS_LENGTH_SCALE,
    SETTING_TTS_MODEL_PATH,
    SETTING_TTS_NOISE_SCALE,
    SETTING_TTS_NOISE_W,
    SETTING_TTS_SPEAKER_ID,
    SETTING_TTS_USE_DEFAULTS,
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

        # --- Advanced / Piper TTS (experimental) ---
        root.addWidget(self._build_advanced_group())

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

    # ------------------------------------------------------- advanced / TTS

    def _build_advanced_group(self) -> QWidget:
        """Build the Advanced dropdown that hosts experimental Piper TTS.

        A ``QToolButton`` in checkable mode renders as a clickable header
        with an arrow indicator; toggling it reveals or hides the
        body widget holding all Piper TTS controls.
        """
        container = QWidget()
        container.setObjectName("advancedDropdown")
        v = QVBoxLayout(container)
        v.setContentsMargins(0, 4, 0, 0)
        v.setSpacing(0)

        # --- Dropdown header (QToolButton) ---
        self.advanced_toggle = QToolButton()
        self.advanced_toggle.setObjectName("advancedToggle")
        self.advanced_toggle.setText("Advanced  (Piper TTS — experimental)")
        self.advanced_toggle.setCheckable(True)
        self.advanced_toggle.setChecked(False)
        # Note: styling lives in styles.py under the `.advancedToggle` /
        # `.advancedBody` QSS selectors so the active theme (light / dark)
        # colors it appropriately. Do NOT set a hardcoded stylesheet here
        # or it will override the global theme.
        # Standard Qt arrow icon.
        self.advanced_toggle.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowDown))
        v.addWidget(self.advanced_toggle)

        # --- Body (the actual TTS controls) ---
        body = QWidget()
        body.setObjectName("advancedBody")
        body_layout = QVBoxLayout(body)
        body_layout.setContentsMargins(12, 10, 12, 4)
        body_layout.setSpacing(8)
        v.addWidget(body)

        # Start collapsed. The persistence step in ``_restore_settings``
        # applies the user's last-known open/closed state. We connect the
        # toggled handler *after* this initial setChecked(False) so the
        # constructor doesn't write back a stale value to QSettings.
        body.setVisible(False)
        self.advanced_toggle.setArrowType(Qt.ArrowType.RightArrow)

        # Wire the handler now that the initial state is set.
        # Save the body reference FIRST so the handler can use it.
        self.advanced_body = body
        self.advanced_toggle.toggled.connect(self._on_advanced_toggled)

        warning = QLabel(
            "⚠ Experimental: voice synthesis via Piper TTS. Requires a "
            "downloaded Piper voice (.onnx + .onnx.json). Not all voices "
            "render every text correctly. Audio files are embedded in the "
            ".apkg and inflate its size."
        )
        warning.setWordWrap(True)
        warning.setObjectName("ttsWarning")
        warning.setStyleSheet(
            "color: #92400e; background: #fffbeb; padding: 8px 10px; "
            "border-left: 3px solid #f59e0b; border-radius: 4px;"
        )
        body_layout.addWidget(warning)

        self.tts_enabled_checkbox = QCheckBox("Enable voice pronunciation")
        self.tts_enabled_checkbox.setToolTip(
            "Synthesise the term and example sentence with Piper and ship "
            "them as audio inside the .apkg."
        )
        self.tts_enabled_checkbox.toggled.connect(self._refresh_tts_ui)
        body_layout.addWidget(self.tts_enabled_checkbox)

        # --- Model path picker ---
        model_row = QHBoxLayout()
        model_label = QLabel("Voice model (.onnx):")
        self.tts_model_edit = QLineEdit()
        self.tts_model_edit.setPlaceholderText(
            "Select a Piper voice model — e.g. en_US-lessac-medium.onnx"
        )
        self.tts_model_edit.setReadOnly(True)
        self.tts_model_browse = QPushButton("Browse…")
        self.tts_model_browse.setObjectName("secondary")
        self.tts_model_browse.clicked.connect(self._on_browse_tts_model)
        model_row.addWidget(model_label)
        model_row.addWidget(self.tts_model_edit, 1)
        model_row.addWidget(self.tts_model_browse)
        body_layout.addLayout(model_row)

        # --- Params grid ---
        params = QGridLayout()
        params.setHorizontalSpacing(12)
        params.setVerticalSpacing(6)

        params.addWidget(QLabel("Speaker ID"), 0, 0)
        self.tts_speaker_id = QSpinBox()
        self.tts_speaker_id.setRange(0, 16)
        self.tts_speaker_id.setValue(DEFAULT_TTS_SPEAKER_ID)
        params.addWidget(self.tts_speaker_id, 0, 1)

        params.addWidget(QLabel("Length scale"), 0, 2)
        self.tts_length_scale = QDoubleSpinBox()
        self.tts_length_scale.setRange(0.1, 4.0)
        self.tts_length_scale.setSingleStep(0.05)
        self.tts_length_scale.setValue(DEFAULT_TTS_LENGTH_SCALE)
        params.addWidget(self.tts_length_scale, 0, 3)

        params.addWidget(QLabel("Noise scale"), 1, 0)
        self.tts_noise_scale = QDoubleSpinBox()
        self.tts_noise_scale.setRange(0.0, 2.0)
        self.tts_noise_scale.setSingleStep(0.05)
        self.tts_noise_scale.setValue(DEFAULT_TTS_NOISE_SCALE)
        params.addWidget(self.tts_noise_scale, 1, 1)

        params.addWidget(QLabel("Noise W"), 1, 2)
        self.tts_noise_w = QDoubleSpinBox()
        self.tts_noise_w.setRange(0.0, 2.0)
        self.tts_noise_w.setSingleStep(0.05)
        self.tts_noise_w.setValue(DEFAULT_TTS_NOISE_W)
        params.addWidget(self.tts_noise_w, 1, 3)
        body_layout.addLayout(params)

        # --- Voice defaults toggle (recommended) ---
        self.tts_use_defaults_checkbox = QCheckBox(
            "Use voice's recommended parameters"
        )
        self.tts_use_defaults_checkbox.setChecked(True)
        self.tts_use_defaults_checkbox.setToolTip(
            "When checked (recommended), Piper uses the length_scale / "
            "noise_scale values that the voice was trained with — this "
            "matches the audio from Piper's official samples and avoids "
            "high-pitched or unnaturally fast output. Uncheck to manually "
            "override the parameters above."
        )
        self.tts_use_defaults_checkbox.toggled.connect(self._refresh_tts_ui)
        body_layout.addWidget(self.tts_use_defaults_checkbox)

        # --- Test synthesize button ---
        test_row = QHBoxLayout()
        self.tts_test_button = QPushButton("▶ Test synthesize sample")
        self.tts_test_button.setObjectName("secondary")
        self.tts_test_button.clicked.connect(self._on_test_synthesize)
        test_row.addWidget(self.tts_test_button)
        test_row.addStretch(1)
        body_layout.addLayout(test_row)

        # ``body`` is set collapsed + the toggle handler is connected at the
        # top of this method (after the initial setChecked(False)). The
        # ``_restore_settings`` step will apply the user's last-known state.

        self._refresh_tts_ui()
        return container

    def _on_advanced_toggled(self, checked: bool) -> None:
        """Toggle body visibility + arrow icon, persist the choice."""
        self.advanced_body.setVisible(checked)
        # Make the dropdown behaviour obvious: down-arrow when expanded,
        # right-arrow when collapsed.
        self.advanced_toggle.setArrowType(
            Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow
        )
        self._settings.setValue("tts_advanced_open", checked)
        self._settings.sync()

    def _refresh_tts_ui(self) -> None:
        enabled = self.tts_enabled_checkbox.isChecked()
        self.tts_model_browse.setEnabled(enabled)
        # Manual parameters are only relevant when voice defaults are off.
        params_enabled = enabled and not self.tts_use_defaults_checkbox.isChecked()
        self.tts_speaker_id.setEnabled(params_enabled)
        self.tts_length_scale.setEnabled(params_enabled)
        self.tts_noise_scale.setEnabled(params_enabled)
        self.tts_noise_w.setEnabled(params_enabled)
        self.tts_test_button.setEnabled(enabled)

    def _on_browse_tts_model(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Piper voice model", "",
            "Piper voice (*.onnx *.onnx.json);;All Files (*)",
        )
        if not path:
            return
        self.tts_model_edit.setText(path)

    def _on_test_synthesize(self) -> None:
        path = self._tts_resolved_paths()
        if path is None:
            QMessageBox.warning(
                self, "Piper model",
                "Select a Piper .onnx file (and the sibling .onnx.json "
                "must exist) before testing.",
            )
            return
        try:
            from linguaspark.tts import PiperEngine
            engine = PiperEngine(
                onnx_path=path[0],
                config_path=path[1],
                speaker_id=self.tts_speaker_id.value(),
                length_scale=self.tts_length_scale.value(),
                noise_scale=self.tts_noise_scale.value(),
                noise_w_scale=self.tts_noise_w.value(),
            )
            wav = engine.synth_wav_bytes("Hello, this is a LinguaSpark sample.")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Piper error", str(exc))
            return
        # Persist a temp file and open it with the OS default player.
        import tempfile, subprocess, sys
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as fp:
            fp.write(wav)
            tmp = fp.name
        try:
            if sys.platform == "darwin":
                subprocess.Popen(["open", tmp])
            elif sys.platform.startswith("win"):
                os.startfile(tmp)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", tmp])
        except Exception:
            QMessageBox.information(
                self, "Sample synthesised",
                f"Wrote sample to {tmp}. Open it with any audio player to hear it.",
            )

    # ---------------------------------------------------- TTS public accessors

    def tts_enabled(self) -> bool:
        return self.tts_enabled_checkbox.isChecked()

    def tts_model_path(self) -> Optional[Path]:
        text = self.tts_model_edit.text().strip()
        return Path(text) if text else None

    def tts_config_path(self, model: Optional[Path] = None) -> Optional[Path]:
        """Return the resolved .onnx.json path. Auto-derives the sibling.

        Looks at:
        1. ``SETTING_TTS_CONFIG_PATH`` if explicitly saved.
        2. ``<model>.onnx.json`` next to the model file.
        """
        stored = self._settings.value(SETTING_TTS_CONFIG_PATH, "", type=str).strip()
        if stored:
            p = Path(stored)
            if p.is_file():
                return p
        candidate = (model or self.tts_model_path())
        if candidate is None:
            return None
        sibling = candidate.with_suffix(candidate.suffix + ".json")
        return sibling if sibling.is_file() else None

    def _tts_resolved_paths(self) -> Optional[tuple[Path, Path]]:
        model = self.tts_model_path()
        config = self.tts_config_path(model)
        if model is None or config is None:
            return None
        return model, config

    def tts_parameters(self) -> dict:
        return {
            "use_voice_defaults": self.tts_use_defaults_checkbox.isChecked(),
            "speaker_id": self.tts_speaker_id.value(),
            "length_scale": self.tts_length_scale.value(),
            "noise_scale": self.tts_noise_scale.value(),
            "noise_w_scale": self.tts_noise_w.value(),
        }

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
        # TTS (experimental).
        self._settings.setValue(SETTING_TTS_ENABLED, self.tts_enabled_checkbox.isChecked())
        self._settings.setValue(SETTING_TTS_MODEL_PATH, self.tts_model_edit.text())
        # Auto-derive sibling if present; only persist when both files exist.
        model = self.tts_model_path()
        config = self.tts_config_path(model) if model else None
        if config is not None:
            self._settings.setValue(SETTING_TTS_CONFIG_PATH, str(config))
        self._settings.setValue(SETTING_TTS_SPEAKER_ID, self.tts_speaker_id.value())
        self._settings.setValue(SETTING_TTS_LENGTH_SCALE, self.tts_length_scale.value())
        self._settings.setValue(SETTING_TTS_NOISE_SCALE, self.tts_noise_scale.value())
        self._settings.setValue(SETTING_TTS_NOISE_W, self.tts_noise_w.value())
        self._settings.setValue(
            SETTING_TTS_USE_DEFAULTS,
            self.tts_use_defaults_checkbox.isChecked(),
        )
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

        # Restore TTS state (experimental).
        tts_enabled = self._settings.value(SETTING_TTS_ENABLED, False, type=bool)
        tts_model = self._settings.value(SETTING_TTS_MODEL_PATH, "", type=str)
        for w in (self.tts_enabled_checkbox, self.tts_speaker_id,
                  self.tts_length_scale, self.tts_noise_scale, self.tts_noise_w,
                  self.tts_use_defaults_checkbox):
            w.blockSignals(True)
        self.tts_enabled_checkbox.setChecked(bool(tts_enabled))
        self.tts_model_edit.setText(tts_model)
        self.tts_speaker_id.setValue(
            int(self._settings.value(SETTING_TTS_SPEAKER_ID, DEFAULT_TTS_SPEAKER_ID, type=int))
        )
        self.tts_length_scale.setValue(
            float(self._settings.value(SETTING_TTS_LENGTH_SCALE, DEFAULT_TTS_LENGTH_SCALE, type=float))
        )
        self.tts_noise_scale.setValue(
            float(self._settings.value(SETTING_TTS_NOISE_SCALE, DEFAULT_TTS_NOISE_SCALE, type=float))
        )
        self.tts_noise_w.setValue(
            float(self._settings.value(SETTING_TTS_NOISE_W, DEFAULT_TTS_NOISE_W, type=float))
        )
        # Default to True on first launch; honor explicit user choice later.
        self.tts_use_defaults_checkbox.setChecked(
            self._settings.value(SETTING_TTS_USE_DEFAULTS, True, type=bool)
        )
        for w in (self.tts_enabled_checkbox, self.tts_speaker_id,
                  self.tts_length_scale, self.tts_noise_scale, self.tts_noise_w,
                  self.tts_use_defaults_checkbox):
            w.blockSignals(False)
        self._refresh_tts_ui()

        # Advanced dropdown expanded/collapsed state.
        adv_open = self._settings.value("tts_advanced_open", False, type=bool)
        # The new container is a plain QWidget with objectName="advancedDropdown"
        # we set in _build_advanced_group; the body is captured as
        # ``self.advanced_body`` and the toggle as ``self.advanced_toggle``.
        # Use ``blockSignals(True)`` so the toggle handler doesn't write
        # back what we just read.
        self.advanced_toggle.blockSignals(True)
        self.advanced_toggle.setChecked(bool(adv_open))
        self.advanced_body.setVisible(bool(adv_open))
        self.advanced_toggle.setArrowType(
            Qt.ArrowType.DownArrow if adv_open else Qt.ArrowType.RightArrow
        )
        self.advanced_toggle.blockSignals(False)

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
