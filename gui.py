#!/usr/bin/env python3
"""
Entry point for the ER Diagram Generator Desktop GUI application.

Usage:
    python gui.py
"""

import sys
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow


def main():
    # Enable high-DPI scaling attributes if available
    if hasattr(Qt, "AA_EnableHighDpiScaling"):
        QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    if hasattr(Qt, "AA_UseHighDpiPixmaps"):
        QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("ER Diagram Generator")
    app.setOrganizationName("DatabaseLabs")

    window = MainWindow()
    window.showMaximized()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
