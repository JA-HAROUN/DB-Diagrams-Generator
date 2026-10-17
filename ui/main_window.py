"""Main application window for the ER Diagram Generator desktop GUI."""

from __future__ import annotations

import logging
import os

from dotenv import load_dotenv
from PySide6.QtCore import QSettings, Qt, QTimer
from PySide6.QtGui import (
    QDragEnterEvent,
    QDropEvent,
    QKeySequence,
    QShortcut,
)
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from models import Database
from ui.editor import EditorSection
from ui.examples import EXAMPLES
from ui.preview import DiagramPreviewWidget
from ui.settings_dialog import SettingsDialog
from ui.styles import get_stylesheet
from ui.validator import ValidationResult, clean_json_text
from ui.workers import AIWorker, RenderWorker

AI_STATUS_MESSAGES = [
    "Reading your system description",
    "Identifying entities and attributes",
    "Finding primary keys",
    "Detecting multivalued and composite attributes",
    "Working out relationships and cardinalities",
    "Structuring the JSON",
    "Almost there, checking the output",
    "Still working, thanks for waiting",
]

RENDER_STATUS_MESSAGES = [
    "Laying out entities",
    "Drawing relationships",
    "Rendering high-resolution image",
    "Finalizing diagram layout",
]


class MainWindow(QMainWindow):
    """Modern ER Diagram Generator desktop application."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("ER Diagram Generator")
        self.setMinimumSize(1000, 650)
        self.setAcceptDrops(True)

        self.theme = "dark"
        self.settings = QSettings("DatabaseLabs", "ERDiagramGenerator")

        self.current_database: Database | None = None
        self.ai_worker: AIWorker | None = None
        self.render_worker: RenderWorker | None = None
        self.save_worker: RenderWorker | None = None
        self.is_document_modified = False

        # Rotating status feedback
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self._on_status_tick)
        self.active_status_messages: list[str] = []
        self.status_msg_index = 0
        self.status_dot_count = 0
        self.status_tick_count = 0

        self._init_ui()
        self._setup_shortcuts()
        self._load_window_settings()
        self._check_api_key_status()

    def _init_ui(self):
        # Central widget
        central = QWidget(self)
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # 1. Top Bar
        top_bar = self._create_top_bar()
        main_layout.addWidget(top_bar)

        # 2. Split Panels Area
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setContentsMargins(12, 12, 12, 12)

        left_panel = self._create_left_panel()
        right_panel = self._create_right_panel()

        self.splitter.addWidget(left_panel)
        self.splitter.addWidget(right_panel)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

        main_layout.addWidget(self.splitter, stretch=1)

        # 3. Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)

        self.status_message = QLabel("Ready")
        self.status_bar.addWidget(self.status_message, stretch=1)

        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.setFixedWidth(120)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)

        self.apply_theme(self.theme)

    def _create_top_bar(self) -> QWidget:
        top_bar = QFrame(self)
        top_bar.setObjectName("topBar")
        bar_layout = QHBoxLayout(top_bar)
        bar_layout.setContentsMargins(16, 8, 16, 8)
        bar_layout.setSpacing(12)

        # App Logo & Title
        title_label = QLabel("ER Diagram Generator")
        title_label.setObjectName("appTitle")
        bar_layout.addWidget(title_label)

        badge_label = QLabel("AI Powered")
        badge_label.setStyleSheet(
            "background-color: #6366F1; color: white; border-radius: 4px; "
            "padding: 2px 6px; font-size: 10px; font-weight: bold;"
        )
        bar_layout.addWidget(badge_label)

        bar_layout.addStretch()

        # Examples Menu Button
        self.btn_examples = QPushButton("Examples ▾")
        self.btn_examples.setProperty("class", "ghostButton")
        self.btn_examples.setToolTip("Explore ready-made database schemas")
        examples_menu = QMenu(self)
        for name, data in EXAMPLES.items():
            action = examples_menu.addAction(name)
            action.triggered.connect(lambda checked=False, d=data: self.load_example(d))
        self.btn_examples.setMenu(examples_menu)
        bar_layout.addWidget(self.btn_examples)

        # Theme Toggle
        self.btn_theme_toggle = QPushButton("🌙 Dark")
        self.btn_theme_toggle.setProperty("class", "ghostButton")
        self.btn_theme_toggle.setToolTip("Toggle between Dark and Light mode")
        self.btn_theme_toggle.clicked.connect(self.toggle_theme)
        bar_layout.addWidget(self.btn_theme_toggle)

        # Settings Button
        self.btn_settings = QPushButton("⚙ Settings")
        self.btn_settings.setProperty("class", "ghostButton")
        self.btn_settings.setToolTip("Configure Gemini API key and model")
        self.btn_settings.clicked.connect(self.open_settings)
        bar_layout.addWidget(self.btn_settings)

        return top_bar

    def _create_left_panel(self) -> QWidget:
        container = QFrame()
        container.setProperty("class", "panelFrame")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Section 1: AI Prompt
        prompt_header = QHBoxLayout()
        prompt_title = QLabel("AI Database Prompt")
        prompt_title.setObjectName("sectionHeader")
        prompt_header.addWidget(prompt_title)
        prompt_header.addStretch()

        # Prompt history dropdown
        self.history_combo = QComboBox()
        self.history_combo.setPlaceholderText("Prompt History (Recent 10)")
        self.history_combo.setToolTip("Select a recent prompt to load")
        self.history_combo.setFixedWidth(200)
        self.history_combo.currentIndexChanged.connect(self._on_history_selected)
        self._load_prompt_history()
        prompt_header.addWidget(self.history_combo)

        layout.addLayout(prompt_header)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "Describe your system, e.g. A university has students, courses and instructors..."
        )
        self.prompt_input.setMaximumHeight(90)
        layout.addWidget(self.prompt_input)

        # AI Action Row
        ai_action_row = QHBoxLayout()
        ai_action_row.setSpacing(8)

        self.chk_auto_generate = QCheckBox("Auto-generate diagram after AI")
        self.chk_auto_generate.setChecked(False)
        self.chk_auto_generate.setToolTip(
            "Automatically render diagram when AI completes"
        )
        ai_action_row.addWidget(self.chk_auto_generate)

        ai_action_row.addStretch()

        self.btn_cancel_ai = QPushButton("Cancel")
        self.btn_cancel_ai.setProperty("class", "ghostButton")
        self.btn_cancel_ai.setVisible(False)
        self.btn_cancel_ai.clicked.connect(self.cancel_ai_generation)
        ai_action_row.addWidget(self.btn_cancel_ai)

        self.btn_generate_ai = QPushButton("✨ Generate JSON with AI")
        self.btn_generate_ai.setProperty("class", "primaryButton")
        self.btn_generate_ai.setToolTip("Generate ER schema from description (Ctrl+G)")
        self.btn_generate_ai.clicked.connect(self.generate_with_ai)
        ai_action_row.addWidget(self.btn_generate_ai)

        layout.addLayout(ai_action_row)

        # Subtle separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #334155;")
        layout.addWidget(sep)

        # Section 2: JSON Editor
        self.editor_section = EditorSection(self, theme=self.theme)
        self.editor_section.validation_changed.connect(self._on_validation_changed)
        self.editor_section.status_message_requested.connect(self.set_status_message)
        self.editor_section.editor.text_modified.connect(self._on_text_modified)
        layout.addWidget(self.editor_section, stretch=1)

        return container

    def _create_right_panel(self) -> QWidget:
        container = QFrame()
        container.setProperty("class", "panelFrame")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        self.preview_widget = DiagramPreviewWidget(self, theme=self.theme)
        self.preview_widget.generate_diagram_requested.connect(self.generate_diagram)
        self.preview_widget.save_diagram_requested.connect(self.save_diagram_to_path)
        self.preview_widget.status_message_requested.connect(self.set_status_message)

        layout.addWidget(self.preview_widget, stretch=1)
        return container

    def _setup_shortcuts(self):
        # Ctrl+Enter: Generate Diagram
        QShortcut(QKeySequence("Ctrl+Return"), self, self.generate_diagram)
        QShortcut(QKeySequence("Ctrl+Enter"), self, self.generate_diagram)

        # Ctrl+G: Generate JSON with AI
        QShortcut(QKeySequence("Ctrl+G"), self, self.generate_with_ai)

        # Ctrl+S: Save Diagram
        QShortcut(QKeySequence("Ctrl+S"), self, self.preview_widget.prompt_save_diagram)

        # Ctrl+O: Open JSON
        QShortcut(QKeySequence("Ctrl+O"), self, self.editor_section.open_json_file)

        # Ctrl+Shift+F: Format JSON
        QShortcut(QKeySequence("Ctrl+Shift+F"), self, self.editor_section.format_json)

    def apply_theme(self, theme: str):
        self.theme = theme
        self.setStyleSheet(get_stylesheet(theme))
        self.editor_section.set_theme(theme)
        self.preview_widget.set_theme(theme)
        self.btn_theme_toggle.setText("☀️ Light" if theme == "dark" else "🌙 Dark")

    def toggle_theme(self):
        new_theme = "light" if self.theme == "dark" else "dark"
        self.apply_theme(new_theme)
        self.settings.setValue("theme", new_theme)

    def set_status_message(self, message: str):
        self.status_message.setText(message)

    def _check_api_key_status(self):
        api_key = os.getenv("GEMINI_API_KEY", "").strip()
        if not api_key:
            self.btn_generate_ai.setEnabled(False)
            self.btn_generate_ai.setToolTip(
                "Gemini API key is not set. Add it in Settings (top right) or .env file to enable AI."
            )
        else:
            self.btn_generate_ai.setEnabled(True)
            self.btn_generate_ai.setToolTip(
                "Generate ER schema from description (Ctrl+G)"
            )

    def open_settings(self):
        dialog = SettingsDialog(self, theme=self.theme)
        dialog.settings_saved.connect(
            lambda: (load_dotenv(override=True), self._check_api_key_status())
        )
        dialog.exec()

    # --- Status Rotation Feedback ---
    def start_status_rotation(self, messages: list[str]):
        self.active_status_messages = list(messages)
        self.status_msg_index = 0
        self.status_dot_count = 0
        self.status_tick_count = 0
        self.progress_bar.setVisible(True)
        self._update_rotating_status_text()
        self.status_timer.start(400)

    def _on_status_tick(self):
        self.status_tick_count += 1
        self.status_dot_count = (self.status_dot_count % 3) + 1
        # Advance to next message every 2 seconds (5 ticks * 400ms = 2000ms)
        if self.status_tick_count % 5 == 0 and self.active_status_messages:
            if self.status_msg_index < len(self.active_status_messages) - 1:
                self.status_msg_index += 1
            else:
                self.status_msg_index = max(0, len(self.active_status_messages) - 2)
        self._update_rotating_status_text()

    def _update_rotating_status_text(self):
        if not self.active_status_messages:
            return
        msg = self.active_status_messages[self.status_msg_index].rstrip(".… ")
        dots = "." * self.status_dot_count
        self.set_status_message(f"{msg}{dots}")

    def stop_status_rotation(self, final_message: str | None = None):
        self.status_timer.stop()
        self.progress_bar.setVisible(False)
        if final_message:
            self.set_status_message(final_message)

    # --- AI Flow ---
    def generate_with_ai(self):
        prompt = self.prompt_input.toPlainText().strip()
        if not prompt:
            QMessageBox.information(
                self,
                "Prompt Required",
                "Please describe your database in the AI Prompt box first.",
            )
            return

        self._check_api_key_status()
        if not self.btn_generate_ai.isEnabled():
            self.open_settings()
            return

        self.btn_generate_ai.setEnabled(False)
        self.btn_cancel_ai.setVisible(True)
        self.start_status_rotation(AI_STATUS_MESSAGES)

        self.ai_worker = AIWorker(prompt=prompt)
        self.ai_worker.success.connect(self._on_ai_success)
        self.ai_worker.error.connect(self._on_ai_error)
        self.ai_worker.finished.connect(self._on_ai_finished)
        self.ai_worker.start()

    def cancel_ai_generation(self):
        if self.ai_worker and self.ai_worker.isRunning():
            self.ai_worker.cancel()
            self.stop_status_rotation("AI generation cancelled.")
            self._on_ai_finished()

    def _on_ai_success(self, database: Database, json_str: str):
        cleaned_json = clean_json_text(json_str)

        # Place into JSON Editor so user can review and edit it
        replaced = self.editor_section.set_json_content(
            cleaned_json, ask_confirmation=True
        )
        if not replaced:
            self.stop_status_rotation("AI response discarded by user.")
            return

        # Save prompt to history
        self._add_to_prompt_history(self.prompt_input.toPlainText().strip())

        # Automatically save last generated JSON to generated_database.json (as CLI does)
        try:
            with open("generated_database.json", "w", encoding="utf-8") as f:
                f.write(cleaned_json)
        except OSError:
            logging.exception("Failed to save generated database JSON")

        self.stop_status_rotation(
            "JSON generated, review it, then click Generate Diagram."
        )

        # Optional auto-generate
        if self.chk_auto_generate.isChecked():
            self.generate_diagram()

    def _on_ai_error(self, short_msg: str, detail_msg: str):
        self.stop_status_rotation(f"Error: {short_msg}")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setWindowTitle("AI Generation Failed")
        msg_box.setText(short_msg)
        msg_box.setDetailedText(detail_msg)
        msg_box.exec()

    def _on_ai_finished(self):
        self.progress_bar.setVisible(False)
        self.btn_cancel_ai.setVisible(False)
        self._check_api_key_status()
        self.ai_worker = None

    # --- Validation & Editing ---
    def _on_validation_changed(self, result: ValidationResult):
        if result.is_valid:
            self.current_database = result.database
            self.preview_widget.btn_generate.setEnabled(True)
        else:
            self.current_database = None
            self.preview_widget.btn_generate.setEnabled(False)

    def _on_text_modified(self, modified: bool):
        self.is_document_modified = modified

    # --- Diagram Rendering ---
    def generate_diagram(self):
        if not self.current_database:
            QMessageBox.warning(
                self,
                "Invalid Schema",
                "Cannot generate diagram: Please fix the JSON errors in the editor first.",
            )
            return

        self.preview_widget.btn_generate.setEnabled(False)
        self.start_status_rotation(RENDER_STATUS_MESSAGES)

        # Renders into a temporary directory per instruction #3
        self.render_worker = RenderWorker(
            database=self.current_database, output_format="png"
        )
        self.render_worker.success.connect(self._on_render_success)
        self.render_worker.error.connect(self._on_render_error)
        self.render_worker.finished.connect(self._on_render_finished)
        self.render_worker.start()

    def _on_render_success(self, image_path: str):
        self.preview_widget.display_image(image_path)
        self.stop_status_rotation("Diagram generated successfully.")

    def _on_render_error(self, short_msg: str, detail_msg: str):
        self.stop_status_rotation(f"Rendering failed: {short_msg}")
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Critical)
        msg_box.setWindowTitle("Diagram Rendering Error")
        msg_box.setText(short_msg)
        msg_box.setDetailedText(detail_msg)
        msg_box.exec()

    def _on_render_finished(self):
        self.progress_bar.setVisible(False)
        if self.current_database:
            self.preview_widget.btn_generate.setEnabled(True)
        self.render_worker = None

    def save_diagram_to_path(self, target_path: str, fmt: str, *args):
        if not self.current_database:
            QMessageBox.warning(
                self, "No Diagram", "No diagram has been generated yet to save."
            )
            return

        try:
            # Stop previous save worker if still active
            if self.save_worker and self.save_worker.isRunning():
                self.save_worker.wait()

            self.progress_bar.setVisible(True)
            self.set_status_message(f"Saving diagram to {target_path}…")

            self.save_worker = RenderWorker(
                database=self.current_database,
                output_format=fmt,
                target_path=target_path,
                parent=self,
            )

            def on_save_success(path):
                self.set_status_message(f"Saved to {path}")
                self.save_worker = None

            def on_save_error(msg, detail):
                self.set_status_message(f"Failed to save diagram: {msg}")
                QMessageBox.critical(self, "Save Error", f"{msg}\n\nDetails:\n{detail}")
                self.save_worker = None

            def on_save_finished():
                self.progress_bar.setVisible(False)

            self.save_worker.success.connect(on_save_success)
            self.save_worker.error.connect(on_save_error)
            self.save_worker.finished.connect(on_save_finished)
            self.save_worker.start()

        except Exception as err:
            self.progress_bar.setVisible(False)
            self.set_status_message(f"Save failed: {err}")
            QMessageBox.critical(
                self, "Save Error", f"Unexpected error while saving diagram:\n{err}"
            )

    # --- Examples & History ---
    def load_example(self, example_data: dict):
        desc = example_data.get("description", "")
        json_content = example_data.get("json", "")
        self.prompt_input.setPlainText(desc)
        self.editor_section.set_json_content(
            json_content,
            ask_confirmation=bool(self.editor_section.get_json_content().strip()),
        )
        self.set_status_message("Loaded example schema.")

    def _load_prompt_history(self):
        history = self.settings.value("prompt_history", [])
        if isinstance(history, list):
            self.history_combo.blockSignals(True)
            self.history_combo.clear()
            self.history_combo.addItem("History ▾", "")
            for p in history:
                short_p = (p[:35] + "…") if len(p) > 35 else p
                self.history_combo.addItem(short_p, p)
            self.history_combo.blockSignals(False)

    def _add_to_prompt_history(self, prompt: str):
        if not prompt:
            return
        history = self.settings.value("prompt_history", [])
        if not isinstance(history, list):
            history = []
        if prompt in history:
            history.remove(prompt)
        history.insert(0, prompt)
        history = history[:10]  # Keep last 10
        self.settings.setValue("prompt_history", history)
        self._load_prompt_history()

    def _on_history_selected(self, index: int):
        if index <= 0:
            return
        data = self.history_combo.currentData()
        if data:
            self.prompt_input.setPlainText(data)
            self.history_combo.setCurrentIndex(0)

    # --- Drag & Drop ---
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if any(u.toLocalFile().lower().endswith(".json") for u in urls):
                event.acceptProposedAction()
                return
        event.ignore()

    def dropEvent(self, event: QDropEvent):
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith(".json") and os.path.exists(file_path):
                self.editor_section.load_file(file_path)
                event.acceptProposedAction()
                break

    # --- Window State & Unsaved Changes ---
    def _load_window_settings(self):
        saved_theme = self.settings.value("theme", "dark")
        self.apply_theme(saved_theme)

        # Open maximized to full screen by default
        has_opened_max = self.settings.value(
            "has_opened_maximized_v3", False, type=bool
        )
        if not has_opened_max:
            self.showMaximized()
            self.settings.setValue("has_opened_maximized_v3", True)
        else:
            geometry = self.settings.value("geometry")
            if geometry:
                self.restoreGeometry(geometry)
            else:
                self.showMaximized()

        splitter_state = self.settings.value("splitter_state")
        if splitter_state:
            self.splitter.restoreState(splitter_state)

    def closeEvent(self, event):
        # Unsaved changes check (avoid modal hanging during headless testing)
        if (
            self.is_document_modified
            and self.editor_section.get_json_content().strip()
            and QApplication.platformName() != "offscreen"
        ):
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes in the editor. Do you really want to quit?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return

        # Save window state
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("splitter_state", self.splitter.saveState())
        event.accept()
