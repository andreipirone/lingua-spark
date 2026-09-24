"""LinguaSpark entry point.

Launches the PySide6 GUI. The UI itself is wired up in Phase 3; for now this
file imports cleanly so the package foundation can be exercised.
"""

from __future__ import annotations

import sys


def main() -> int:
    """Run the LinguaSpark application."""
    from PySide6.QtWidgets import QApplication

    from linguaspark import __app_name__

    app = QApplication(sys.argv)
    app.setApplicationName(__app_name__)
    app.setOrganizationName("Anki-Deck-Generator")

    # The full main window is implemented in Phase 3 (ui/main_window.py).
    # Until then, launch a minimal placeholder so the entry point is verifiable.
    from linguaspark.ui.main_window import MainWindow

    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
