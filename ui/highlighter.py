"""JSON Syntax Highlighter for QPlainTextEdit using QSyntaxHighlighter."""

from __future__ import annotations

from PySide6.QtCore import QRegularExpression
from PySide6.QtGui import QColor, QFont, QSyntaxHighlighter, QTextCharFormat


class JSONHighlighter(QSyntaxHighlighter):
    """Provides real-time syntax highlighting for JSON documents."""

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self._highlighting_rules = []
        self._setup_formats()

    def set_theme(self, theme: str):
        """Update colors when switching between dark and light themes."""
        self.theme = theme
        self._setup_formats()
        self.rehighlight()

    def _setup_formats(self):
        self._highlighting_rules.clear()

        is_dark = self.theme == "dark"

        # Colors tuned for clean contrast in both modes
        color_key = QColor("#818CF8") if is_dark else QColor("#4F46E5")       # Indigo
        color_string = QColor("#34D399") if is_dark else QColor("#059669")    # Emerald
        color_number = QColor("#F472B6") if is_dark else QColor("#DB2777")    # Pink
        color_keyword = QColor("#FB923C") if is_dark else QColor("#EA580C")   # Orange
        color_punctuation = QColor("#94A3B8") if is_dark else QColor("#64748B") # Slate

        # Formats
        fmt_key = QTextCharFormat()
        fmt_key.setForeground(color_key)
        fmt_key.setFontWeight(QFont.DemiBold)

        fmt_string = QTextCharFormat()
        fmt_string.setForeground(color_string)

        fmt_number = QTextCharFormat()
        fmt_number.setForeground(color_number)

        fmt_keyword = QTextCharFormat()
        fmt_keyword.setForeground(color_keyword)
        fmt_keyword.setFontWeight(QFont.Bold)

        fmt_punctuation = QTextCharFormat()
        fmt_punctuation.setForeground(color_punctuation)

        # Rule 1: JSON Keys ("key":)
        self._highlighting_rules.append((
            QRegularExpression(r'"([^"\\]|\\.)*"\s*(?=:)'),
            fmt_key,
        ))

        # Rule 2: JSON String values (": "string" or ["string"])
        self._highlighting_rules.append((
            QRegularExpression(r':\s*("[^"\\]*(\\.[^"\\]*)*")'),
            fmt_string,
        ))
        self._highlighting_rules.append((
            QRegularExpression(r'\[\s*("[^"\\]*(\\.[^"\\]*)*")'),
            fmt_string,
        ))
        self._highlighting_rules.append((
            QRegularExpression(r',\s*("[^"\\]*(\\.[^"\\]*)*")'),
            fmt_string,
        ))

        # Rule 3: Numbers
        self._highlighting_rules.append((
            QRegularExpression(r'\b-?(?:0|[1-9]\d*)(?:\.\d+)?(?:[eE][+-]?\d+)?\b'),
            fmt_number,
        ))

        # Rule 4: Keywords (true, false, null)
        self._highlighting_rules.append((
            QRegularExpression(r'\b(true|false|null)\b'),
            fmt_keyword,
        ))

        # Rule 5: Braces and brackets
        self._highlighting_rules.append((
            QRegularExpression(r'[\{\}\[\]]'),
            fmt_punctuation,
        ))

    def highlightBlock(self, text: str):
        for pattern, char_format in self._highlighting_rules:
            iterator = pattern.globalMatch(text)
            while iterator.hasNext():
                match = iterator.next()
                self.setFormat(match.capturedStart(), match.capturedLength(), char_format)
