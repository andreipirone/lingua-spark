"""Review table widget — editable staging area for VocabCards."""

from __future__ import annotations

from typing import Dict, List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QBrush, QColor
from PySide6.QtWidgets import (
    QAbstractItemView,
    QHeaderView,
    QLabel,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from linguaspark.models.card import VocabCard

from .styles import current_theme


_COLUMN_NAMES = VocabCard.anki_field_names()  # 8 columns


class ReviewTable(QWidget):
    """Editable `QTableWidget` wrapped with an empty-state placeholder."""

    card_changed = Signal(int, object)    # row, VocabCard
    card_removed = Signal(str)            # term
    regenerate_requested = Signal(str)    # term

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._cards_by_row: Dict[int, VocabCard] = {}
        self._failed_rows: set[int] = set()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._empty_state = QLabel(
            "No cards yet.\n\n"
            "Paste a list of words above and click "
            "<b>Process Vocabulary</b> to enrich them with AI."
        )
        self._empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_state.setObjectName("emptyState")

        self.table = QTableWidget()
        self.table.setColumnCount(len(_COLUMN_NAMES))
        self.table.setHorizontalHeaderLabels(_COLUMN_NAMES)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked
            | QAbstractItemView.EditTrigger.SelectedClicked
            | QAbstractItemView.EditTrigger.AnyKeyPressed
        )
        self.table.verticalHeader().setVisible(False)
        self.table.itemChanged.connect(self._on_item_changed)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        self._configure_columns()

        layout.addWidget(self._empty_state)
        layout.addWidget(self.table)
        self._update_empty_state()

    # ------------------------------------------------------------- columns

    def _configure_columns(self) -> None:
        header = self.table.horizontalHeader()
        widths = {
            "Term": 140,
            "Translation": 200,           # primary translation (big, prominent)
            "POS": 110,
            "Phonetics": 130,
            "Definition": 240,
            "Example": 260,
            "Example Translation": 220,   # example sentence translation
            "Mnemonic": 220,
            "Language": 90,
        }
        for col, name in enumerate(_COLUMN_NAMES):
            header.resizeSection(col, widths.get(name, 150))
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setStretchLastSection(False)

    def _update_empty_state(self) -> None:
        empty = self.table.rowCount() == 0
        self._empty_state.setVisible(empty)
        self.table.setVisible(not empty)

    # --------------------------------------------------------------- public

    def add_or_replace_card(self, card: VocabCard) -> int:
        row = self._find_row(card.term)
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)
        self._cards_by_row[row] = card
        self._populate_row(row, card)
        self._update_empty_state()
        return row

    def cards(self) -> List[VocabCard]:
        out: List[VocabCard] = []
        for row in range(self.table.rowCount()):
            card = self._row_to_card(row)
            if card is not None:
                out.append(card)
        return out

    def clear_cards(self) -> None:
        self.table.setRowCount(0)
        self._cards_by_row.clear()
        self._failed_rows.clear()
        self._update_empty_state()

    def mark_failed(self, word: str, message: str) -> None:
        row = self._find_row(word)
        if row is None:
            row = self.table.rowCount()
            self.table.insertRow(row)
        self._failed_rows.add(row)
        term_item = QTableWidgetItem(word)
        self.table.setItem(row, 0, term_item)
        danger = QColor(current_theme().danger)
        for col in range(1, self.table.columnCount()):
            err_item = QTableWidgetItem(f"⚠ {message}" if col == 1 else "")
            err_item.setForeground(QBrush(danger))
            self.table.setItem(row, col, err_item)
        self._update_empty_state()

    def refresh_theme_colors(self) -> None:
        """Re-paint failed-row markers after a theme change."""
        danger = QColor(current_theme().danger)
        for row in self._failed_rows:
            for col in range(1, self.table.columnCount()):
                item = self.table.item(row, col)
                if item is not None:
                    item.setForeground(QBrush(danger))

    # --------------------------------------------------------------- helpers

    def _find_row(self, term: str) -> Optional[int]:
        key = term.casefold()
        for row, card in self._cards_by_row.items():
            if card.term.casefold() == key:
                return row
        return None

    def _populate_row(self, row: int, card: VocabCard) -> None:
        fields = card.to_anki_fields()
        for col, value in enumerate(fields):
            item = QTableWidgetItem(value)
            item.setToolTip(value)
            self.table.setItem(row, col, item)

    def _on_item_changed(self, item: QTableWidgetItem) -> None:
        row = item.row()
        card = self._row_to_card(row)
        if card is not None:
            self._cards_by_row[row] = card
            self.card_changed.emit(row, card)

    def _row_to_card(self, row: int) -> Optional[VocabCard]:
        try:
            values = [self.table.item(row, col).text() for col in range(self.table.columnCount())]
        except AttributeError:
            return None
        # Column order matches `VocabCard.to_anki_fields()`:
        # 0 Term | 1 Translation (primary) | 2 POS | 3 Phonetics | 4 Definition
        # 5 Example | 6 Example Translation | 7 Mnemonic | 8 Language
        try:
            return VocabCard(
                term=values[0],
                translation_primary=values[1],
                pos=values[2],
                phonetics=values[3],
                definition=values[4],
                example=values[5],
                translation=values[6],
                mnemonic=values[7],
                language=values[8],
            )
        except Exception:
            return None

    # -------------------------------------------------------------- context

    def _show_context_menu(self, pos) -> None:
        item = self.table.itemAt(pos)
        if item is None:
            return
        row = item.row()
        card = self._cards_by_row.get(row)
        if card is None:
            return

        menu = QMenu(self)
        regen = QAction("Regenerate this card", menu)
        regen.triggered.connect(lambda: self.regenerate_requested.emit(card.term))
        menu.addAction(regen)

        copy = QAction("Copy term", menu)
        copy.triggered.connect(lambda: self._copy_term(card.term))
        menu.addAction(copy)

        menu.addSeparator()
        delete = QAction("Delete from deck", menu)
        delete.triggered.connect(lambda: self._delete_row(row, card.term))
        menu.addAction(delete)

        menu.exec(self.table.viewport().mapToGlobal(pos))

    def _copy_term(self, term: str) -> None:
        from PySide6.QtWidgets import QApplication

        QApplication.clipboard().setText(term)

    def _delete_row(self, row: int, term: str) -> None:
        self.table.removeRow(row)
        # Rebuild the row index -> card mapping after removal.
        remapped: Dict[int, VocabCard] = {}
        remapped_failed: set[int] = set()
        for r in range(self.table.rowCount()):
            card = self._row_to_card(r)
            if card is not None:
                remapped[r] = card
            if r in self._failed_rows and r < row:
                remapped_failed.add(r)
            elif r in self._failed_rows and r >= row:
                remapped_failed.add(r - 1)
        self._cards_by_row = remapped
        self._failed_rows = remapped_failed
        self._update_empty_state()
        self.card_removed.emit(term)
