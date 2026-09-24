"""Qt Style Sheets (QSS) themes for LinguaSpark.

Two themes are provided:

* ``DARK``  — default, deep navy canvas with lifted indigo accents.
* ``LIGHT`` — fallback, the original light palette.

The active theme is applied with :func:`apply_theme` and remembered in
``QSettings`` (``QSETTINGS_ORG`` / ``QSETTINGS_APP``) under
``linguaspark.config.SETTING_DARK_MODE``.
"""

from __future__ import annotations

from dataclasses import dataclass

from PySide6.QtCore import QSettings
from PySide6.QtWidgets import QApplication

from linguaspark.config import QSETTINGS_APP, QSETTINGS_ORG, SETTING_DARK_MODE


# ----------------------------------------------------------------- palettes


@dataclass(frozen=True)
class Theme:
    """A named bundle of color tokens consumed by the QSS template."""

    name: str
    is_dark: bool

    # Surfaces
    bg: str
    surface: str
    surface_alt: str

    # Borders
    border: str
    border_strong: str

    # Text
    text: str
    text_muted: str
    text_faint: str

    # Brand / action
    primary: str
    primary_hover: str
    primary_pressed: str
    primary_muted: str

    # Semantic
    danger: str
    danger_hover: str
    danger_pressed: str
    success: str

    # Selection / focus
    selection_bg: str
    selection_text: str

    # Tooltips / scrollbars
    tooltip_bg: str
    tooltip_text: str
    scrollbar_bg: str
    scrollbar_handle: str
    scrollbar_handle_hover: str

    # Mnemonic accent (unused in GUI but exposed for future use)
    accent: str

    def to_qss(self) -> str:
        """Render this theme's QSS string."""
        return _QSS_TEMPLATE.format(**self.__dict__)


LIGHT = Theme(
    name="light",
    is_dark=False,
    bg="#f8fafc",
    surface="#ffffff",
    surface_alt="#f1f5f9",
    border="#cbd5e1",
    border_strong="#94a3b8",
    text="#0f172a",
    text_muted="#475569",
    text_faint="#64748b",
    primary="#6366f1",
    primary_hover="#4f46e5",
    primary_pressed="#4338ca",
    primary_muted="#c7d2fe",
    danger="#ef4444",
    danger_hover="#dc2626",
    danger_pressed="#b91c1c",
    success="#10b981",
    selection_bg="#e0e7ff",
    selection_text="#1e1b4b",
    tooltip_bg="#1e293b",
    tooltip_text="#f8fafc",
    scrollbar_bg="#f1f5f9",
    scrollbar_handle="#cbd5e1",
    scrollbar_handle_hover="#94a3b8",
    accent="#f59e0b",
)


DARK = Theme(
    name="dark",
    is_dark=True,
    bg="#0b1020",
    surface="#131a2c",
    surface_alt="#1a2238",
    border="#283149",
    border_strong="#3a4566",
    text="#e6ecff",
    text_muted="#94a3c4",
    text_faint="#6e7a99",
    primary="#7c8cff",
    primary_hover="#9aa9ff",
    primary_pressed="#b3c0ff",
    primary_muted="#2a3358",
    danger="#f87171",
    danger_hover="#fca5a5",
    danger_pressed="#fecaca",
    success="#34d399",
    selection_bg="#2c3760",
    selection_text="#e6ecff",
    tooltip_bg="#060914",
    tooltip_text="#e6ecff",
    scrollbar_bg="#0b1020",
    scrollbar_handle="#283149",
    scrollbar_handle_hover="#3a4566",
    accent="#fbbf24",
)


# ---------------------------------------------------------------- QSS template


_QSS_TEMPLATE = """
QMainWindow, QWidget {{
  background: {bg};
  color: {text};
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto,
               'Helvetica Neue', Arial, sans-serif;
  font-size: 13px;
}}

QLabel {{
  color: {text};
  background: transparent;
}}

QLabel#sectionTitle {{
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: {text_muted};
  padding-top: 4px;
}}

QLabel#emptyState {{
  color: {text_faint};
  font-size: 14px;
  padding: 48px;
}}

QLabel#wordCount {{
  color: {text_faint};
}}

QPlainTextEdit, QLineEdit, QComboBox, QSpinBox {{
  background: {surface};
  color: {text};
  border: 1px solid {border};
  border-radius: 6px;
  padding: 6px 8px;
  selection-background-color: {primary};
  selection-color: {surface};
}}

QPlainTextEdit:focus, QLineEdit:focus, QComboBox:focus, QSpinBox:focus {{
  border: 1px solid {primary};
}}

QPlainTextEdit {{
  selection-background-color: {primary};
}}

QPlainTextEdit:read-only {{
  background: {surface_alt};
  color: {text_muted};
}}

QComboBox::drop-down {{
  border: none;
  width: 22px;
}}

QComboBox QAbstractItemView {{
  background: {surface};
  color: {text};
  border: 1px solid {border};
  selection-background-color: {selection_bg};
  selection-color: {selection_text};
  outline: 0;
}}

QPushButton {{
  background: {primary};
  color: #ffffff;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  font-weight: 600;
}}

QPushButton:hover {{
  background: {primary_hover};
}}

QPushButton:pressed {{
  background: {primary_pressed};
}}

QPushButton:disabled {{
  background: {primary_muted};
  color: {text_faint};
}}

QPushButton#secondary {{
  background: {surface};
  color: {text};
  border: 1px solid {border};
}}

QPushButton#secondary:hover {{
  background: {surface_alt};
  border: 1px solid {border_strong};
}}

QPushButton#secondary:disabled {{
  background: {surface_alt};
  color: {text_faint};
  border: 1px solid {border};
}}

QPushButton#danger {{
  background: {danger};
  color: #ffffff;
}}

QPushButton#danger:hover {{
  background: {danger_hover};
}}

QPushButton#danger:pressed {{
  background: {danger_pressed};
}}

QPushButton#danger:disabled {{
  background: {primary_muted};
  color: {text_faint};
}}

QPushButton#small {{
  padding: 4px 10px;
  font-size: 12px;
}}

QTableWidget {{
  background: {surface};
  alternate-background-color: {surface_alt};
  color: {text};
  border: 1px solid {border};
  border-radius: 6px;
  gridline-color: {border};
  selection-background-color: {selection_bg};
  selection-color: {selection_text};
  outline: 0;
}}

QTableWidget::item {{
  padding: 4px 6px;
}}

QTableWidget::item:selected {{
  background: {selection_bg};
  color: {selection_text};
}}

QHeaderView::section {{
  background: {surface_alt};
  color: {text_muted};
  padding: 6px 8px;
  border: none;
  border-right: 1px solid {border};
  border-bottom: 1px solid {border};
  font-weight: 600;
}}

QHeaderView::section:hover {{
  background: {border};
  color: {text};
}}

QStatusBar {{
  background: {surface};
  border-top: 1px solid {border};
  color: {text_muted};
}}

QStatusBar QLabel {{
  color: {text_muted};
}}

QProgressBar {{
  background: {surface_alt};
  border: 1px solid {border};
  border-radius: 4px;
  text-align: center;
  color: {text};
  height: 14px;
}}

QProgressBar::chunk {{
  background: {primary};
  border-radius: 3px;
  margin: 1px;
}}

QMenu {{
  background: {surface};
  color: {text};
  border: 1px solid {border};
  padding: 4px;
}}

QMenu::item {{
  padding: 6px 18px;
  border-radius: 4px;
}}

QMenu::item:selected {{
  background: {selection_bg};
  color: {selection_text};
}}

QMenu::item:disabled {{
  color: {text_faint};
}}

QMenuBar {{
  background: {surface};
  color: {text};
  border-bottom: 1px solid {border};
  padding: 2px;
}}

QMenuBar::item {{
  background: transparent;
  padding: 4px 10px;
  border-radius: 4px;
}}

QMenuBar::item:selected {{
  background: {selection_bg};
  color: {selection_text};
}}

QSplitter::handle {{
  background: {border};
}}

QSplitter::handle:horizontal {{
  width: 1px;
}}

QSplitter::handle:vertical {{
  height: 1px;
}}

QScrollBar:vertical {{
  background: {scrollbar_bg};
  width: 12px;
  margin: 0;
}}

QScrollBar::handle:vertical {{
  background: {scrollbar_handle};
  border-radius: 6px;
  min-height: 24px;
  margin: 2px;
}}

QScrollBar::handle:vertical:hover {{
  background: {scrollbar_handle_hover};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
  height: 0;
  background: none;
}}

QScrollBar:horizontal {{
  background: {scrollbar_bg};
  height: 12px;
  margin: 0;
}}

QScrollBar::handle:horizontal {{
  background: {scrollbar_handle};
  border-radius: 6px;
  min-width: 24px;
  margin: 2px;
}}

QScrollBar::handle:horizontal:hover {{
  background: {scrollbar_handle_hover};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
  width: 0;
  background: none;
}}

QToolTip {{
  background: {tooltip_bg};
  color: {tooltip_text};
  border: 1px solid {border_strong};
  padding: 4px 6px;
  border-radius: 4px;
}}
"""


# ------------------------------------------------------------ public helpers


_current_theme: Theme = DARK


def current_theme() -> Theme:
    """Return the theme most recently applied to the application."""
    return _current_theme


def apply_theme(app: QApplication, theme: Theme | None = None) -> Theme:
    """Apply `theme` (or the persisted preference if `None`) to `app`.

    Returns the theme that was applied so callers can persist it.
    """
    global _current_theme
    if theme is None:
        theme = load_theme_preference()
    app.setStyleSheet(theme.to_qss())
    _current_theme = theme
    return theme


def load_theme_preference() -> Theme:
    """Read the persisted theme preference. Defaults to DARK."""
    settings = QSettings(QSETTINGS_ORG, QSETTINGS_APP)
    dark = settings.value(SETTING_DARK_MODE, True, type=bool)
    return DARK if dark else LIGHT


def save_theme_preference(theme: Theme) -> None:
    """Persist the user's theme choice to QSettings."""
    settings = QSettings(QSETTINGS_ORG, QSETTINGS_APP)
    settings.setValue(SETTING_DARK_MODE, theme.is_dark)
    settings.sync()


def toggle_theme(app: QApplication) -> Theme:
    """Flip between DARK and LIGHT, persist, and re-apply."""
    new_theme = LIGHT if current_theme().is_dark else DARK
    apply_theme(app, new_theme)
    save_theme_preference(new_theme)
    return new_theme
