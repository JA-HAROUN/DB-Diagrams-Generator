"""Code-style JSON editor with line numbers, syntax highlighting, and debounced validation."""

from __future__ import annotations

import json

from PySide6.QtCore import QRect, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (
    QColor,
    QFont,
    QPainter,
    QTextCursor,
    QTextFormat,
)
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ui.highlighter import JSONHighlighter
from ui.styles import FONT_FAMILY_CODE
from ui.validator import ValidationResult, validate_database_json


class LineNumberArea(QWidget):
    """Paints line numbers for the adjacent QPlainTextEdit."""

    def __init__(self, editor: JSONCodeEditor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self) -> QSize:
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


class JSONCodeEditor(QPlainTextEdit):
    """Monospace code editor with line numbers, syntax highlighting, and error line highlighting."""

    validation_changed = Signal(object)  # Emits ValidationResult
    text_modified = Signal(bool)

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.setObjectName("jsonEditor")
        self.theme = theme

        # Configure font
        code_font = QFont()
        code_font.setFamily(FONT_FAMILY_CODE)
        code_font.setPointSize(10)
        code_font.setStyleHint(QFont.Monospace)
        self.setFont(code_font)

        # Tab width = 2 spaces
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 2)

        # Line number area
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)

        # Highlighter
        self.highlighter = JSONHighlighter(self.document(), theme=self.theme)

        # Debounced validation timer (400ms)
        self.validation_timer = QTimer(self)
        self.validation_timer.setSingleShot(True)
        self.validation_timer.setInterval(400)
        self.validation_timer.timeout.connect(self.run_validation)
        self.textChanged.connect(self._on_text_changed)

        # State tracking
        self.last_validation_result: ValidationResult | None = None
        self.error_line_to_highlight: int | None = None
        self._is_flashing = False

        self.highlight_current_line()

    def set_theme(self, theme: str):
        self.theme = theme
        self.highlighter.set_theme(theme)
        self.highlight_current_line()

    def line_number_area_width(self) -> int:
        digits = max(1, len(str(self.blockCount())))
        space = 20 + self.fontMetrics().horizontalAdvance("9") * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect: QRect, dy: int):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(
                0, rect.y(), self.line_number_area.width(), rect.height()
            )
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(
            QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height())
        )

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        is_dark = self.theme == "dark"
        bg_color = QColor("#090D16") if is_dark else QColor("#F1F5F9")
        text_color = QColor("#64748B") if is_dark else QColor("#94A3B8")

        painter.fillRect(event.rect(), bg_color)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = int(
            self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        )
        bottom = top + int(self.blockBoundingRect(block).height())

        font = self.font()
        font.setPointSize(9)
        painter.setFont(font)

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(text_color)
                painter.drawText(
                    0,
                    top,
                    self.line_number_area.width() - 8,
                    self.fontMetrics().height(),
                    Qt.AlignRight,
                    number,
                )
            block = block.next()
            top = bottom
            bottom = top + int(self.blockBoundingRect(block).height())
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []

        # Current line highlight (subtle)
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            is_dark = self.theme == "dark"
            line_color = QColor(255, 255, 255, 10) if is_dark else QColor(0, 0, 0, 8)
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)

        # Offending error line highlight (translucent red)
        if self.error_line_to_highlight and self.error_line_to_highlight > 0:
            doc = self.document()
            block = doc.findBlockByLineNumber(self.error_line_to_highlight - 1)
            if block.isValid():
                error_sel = QTextEdit.ExtraSelection()
                error_color = QColor(239, 68, 68, 50)  # Red translucent
                error_sel.format.setBackground(error_color)
                error_sel.format.setProperty(QTextFormat.FullWidthSelection, True)
                error_sel.cursor = QTextCursor(block)
                error_sel.cursor.clearSelection()
                extra_selections.append(error_sel)

        self.setExtraSelections(extra_selections)

    def _on_text_changed(self):
        self.text_modified.emit(True)
        self.validation_timer.start()

    def run_validation(self):
        text = self.toPlainText()
        result = validate_database_json(text)
        self.last_validation_result = result

        if not result.is_valid and result.error_line:
            self.error_line_to_highlight = result.error_line
        else:
            self.error_line_to_highlight = None

        self.highlight_current_line()
        self.validation_changed.emit(result)

    def flash_accent(self):
        """Briefly flash accent border when new AI JSON is received."""
        self.setProperty("flashing", "true")
        self.style().unpolish(self)
        self.style().polish(self)
        QTimer.singleShot(1000, self._stop_flash)

    def _stop_flash(self):
        self.setProperty("flashing", "false")
        self.style().unpolish(self)
        self.style().polish(self)


class EditorSection(QWidget):
    """Container widget holding toolbar, JSONCodeEditor, and live status bar."""

    validation_changed = Signal(object)
    status_message_requested = Signal(str)

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Section Header + Action Buttons
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        title_label = QLabel("JSON Schema Editor")
        title_label.setObjectName("sectionHeader")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        # Toolbar buttons
        self.btn_format = QPushButton("Format JSON")
        self.btn_format.setProperty("class", "toolButton")
        self.btn_format.setToolTip("Pretty-print JSON (Ctrl+Shift+F)")
        self.btn_format.clicked.connect(self.format_json)

        self.btn_copy = QPushButton("Copy")
        self.btn_copy.setProperty("class", "toolButton")
        self.btn_copy.setToolTip("Copy JSON to clipboard")
        self.btn_copy.clicked.connect(self.copy_json)

        self.btn_open = QPushButton("Open JSON…")
        self.btn_open.setProperty("class", "toolButton")
        self.btn_open.setToolTip("Open JSON from file (Ctrl+O)")
        self.btn_open.clicked.connect(self.open_json_file)

        self.btn_save = QPushButton("Save JSON…")
        self.btn_save.setProperty("class", "toolButton")
        self.btn_save.setToolTip("Save JSON to file")
        self.btn_save.clicked.connect(self.save_json_file)

        self.btn_clear = QPushButton("Clear")
        self.btn_clear.setProperty("class", "toolButton")
        self.btn_clear.setToolTip("Clear editor content")
        self.btn_clear.clicked.connect(self.clear_content)

        self.btn_template = QPushButton("New Blank Template")
        self.btn_template.setProperty("class", "toolButton")
        self.btn_template.setToolTip("Insert a minimal valid schema skeleton")
        self.btn_template.clicked.connect(self.insert_blank_template)

        for btn in (
            self.btn_format,
            self.btn_copy,
            self.btn_open,
            self.btn_save,
            self.btn_clear,
            self.btn_template,
        ):
            header_layout.addWidget(btn)

        layout.addLayout(header_layout)

        # Editor
        self.editor = JSONCodeEditor(self, theme=self.theme)
        self.editor.validation_changed.connect(self._on_validation_changed)
        layout.addWidget(self.editor, stretch=1)

        # Status Label Under Editor with generous padding and badge styling
        self.status_label = QLabel("✓ Valid JSON")
        self.status_label.setWordWrap(True)
        self.status_label.setContentsMargins(8, 4, 8, 4)
        self.status_label.setStyleSheet(
            "color: #10B981; font-weight: 600; font-size: 12px; "
            "padding: 6px 10px; background-color: rgba(16, 185, 129, 0.1); "
            "border-radius: 6px; margin-top: 4px;"
        )
        layout.addWidget(self.status_label)

    def set_theme(self, theme: str):
        self.theme = theme
        self.editor.set_theme(theme)
        if self.editor.last_validation_result:
            self._update_status_label(self.editor.last_validation_result)

    def set_json_content(self, text: str, ask_confirmation: bool = True) -> bool:
        """Insert or replace editor text, optionally prompting for confirmation."""
        current_text = self.editor.toPlainText().strip()
        if (
            ask_confirmation
            and current_text
            and QApplication.platformName() != "offscreen"
        ):
            reply = QMessageBox.question(
                self,
                "Replace Current JSON?",
                "The editor already contains JSON. Replace it with the new content?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes,
            )
            if reply != QMessageBox.Yes:
                return False

        # Use cursor replacement so Ctrl+Z undo works!
        cursor = self.editor.textCursor()
        cursor.select(QTextCursor.Document)
        cursor.insertText(text)
        self.editor.run_validation()
        self.editor.flash_accent()
        return True

    def get_json_content(self) -> str:
        return self.editor.toPlainText()

    def format_json(self):
        text = self.editor.toPlainText().strip()
        if not text:
            return
        try:
            parsed = json.loads(text)
            formatted = json.dumps(parsed, indent=2)
            cursor = self.editor.textCursor()
            cursor.select(QTextCursor.Document)
            cursor.insertText(formatted)
            self.status_message_requested.emit("JSON formatted")
        except Exception as err:
            self.status_message_requested.emit(f"Could not format: {err}")

    def copy_json(self):
        text = self.editor.toPlainText()
        if text:
            self.editor.selectAll()
            self.editor.copy()
            cursor = self.editor.textCursor()
            cursor.clearSelection()
            self.editor.setTextCursor(cursor)
            self.status_message_requested.emit("JSON copied to clipboard")

    def open_json_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open JSON File", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            self.load_file(file_path)

    def load_file(self, file_path: str):
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # If the file is not valid JSON or doesn't match schema, load text anyway and show error
            self.set_json_content(content, ask_confirmation=False)
            self.status_message_requested.emit(f"Loaded {file_path}")
        except Exception as err:
            QMessageBox.critical(
                self, "Error Opening File", f"Could not read file:\n{err}"
            )

    def save_json_file(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save JSON File",
            "database.json",
            "JSON Files (*.json);;All Files (*)",
        )
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(self.editor.toPlainText())
                self.status_message_requested.emit(f"Saved to {file_path}")
            except Exception as err:
                QMessageBox.critical(
                    self, "Error Saving File", f"Could not save file:\n{err}"
                )

    def clear_content(self):
        if self.editor.toPlainText().strip():
            reply = QMessageBox.question(
                self,
                "Clear Editor?",
                "Are you sure you want to clear the editor?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.editor.clear()
                self.status_message_requested.emit("Editor cleared")

    def insert_blank_template(self):
        template = json.dumps(
            {
                "name": "MyDatabase",
                "entities": [],
                "relationships": [],
            },
            indent=2,
        )
        self.set_json_content(
            template, ask_confirmation=bool(self.editor.toPlainText().strip())
        )

    def _on_validation_changed(self, result: ValidationResult):
        self._update_status_label(result)
        self.validation_changed.emit(result)

    def _update_status_label(self, result: ValidationResult):
        if result.is_valid:
            self.status_label.setText("✓ Valid JSON")
            self.status_label.setStyleSheet(
                "color: #10B981; font-weight: 600; font-size: 12px; "
                "padding: 6px 10px; background-color: rgba(16, 185, 129, 0.1); "
                "border-radius: 6px; margin-top: 4px;"
            )
        else:
            self.status_label.setText(f"✗ Invalid JSON: {result.error_message}")
            self.status_label.setStyleSheet(
                "color: #EF4444; font-weight: 600; font-size: 12px; "
                "padding: 6px 10px; background-color: rgba(239, 68, 68, 0.1); "
                "border-radius: 6px; margin-top: 4px;"
            )
