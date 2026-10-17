"""Settings dialog for Gemini API key and model selection."""

from __future__ import annotations

import os

from dotenv import load_dotenv, set_key
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
)

AVAILABLE_MODELS = [
    "gemini-3.8-flash",
    "gemini-2.5-flash",
    "gemini-2.5-pro",
    "gemini-1.5-flash",
]

ENV_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env"
)


class SettingsDialog(QDialog):
    """Dialog allowing user to view and update the Gemini API key and model."""

    settings_saved = Signal()

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumWidth(480)
        self.theme = theme
        self._init_ui()
        self._load_current_values()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title_label = QLabel("Application Settings")
        title_label.setObjectName("appTitle")
        layout.addWidget(title_label)

        desc_label = QLabel("Configure your Google Gemini API key and preferred model.")
        desc_label.setStyleSheet("color: #94A3B8; font-size: 12px;")
        layout.addWidget(desc_label)

        # API Key Section
        api_group = QVBoxLayout()
        api_group.setSpacing(6)

        key_label = QLabel("Gemini API Key:")
        key_label.setStyleSheet("font-weight: 600;")
        api_group.addWidget(key_label)

        key_row = QHBoxLayout()
        key_row.setSpacing(6)

        self.key_input = QLineEdit()
        self.key_input.setPlaceholderText("Enter your Gemini API key...")
        self.key_input.setEchoMode(QLineEdit.Password)
        key_row.addWidget(self.key_input)

        self.btn_toggle_key = QPushButton("Show")
        self.btn_toggle_key.setFixedWidth(60)
        self.btn_toggle_key.clicked.connect(self._toggle_key_visibility)
        key_row.addWidget(self.btn_toggle_key)

        api_group.addLayout(key_row)

        api_hint = QLabel(
            "The API key will be stored securely in the local .env file only."
        )
        api_hint.setStyleSheet("color: #64748B; font-size: 11px;")
        api_group.addWidget(api_hint)

        layout.addLayout(api_group)

        # Model Selection Section
        model_group = QVBoxLayout()
        model_group.setSpacing(6)

        model_label = QLabel("Gemini Model:")
        model_label.setStyleSheet("font-weight: 600;")
        model_group.addWidget(model_label)

        self.model_combo = QComboBox()
        self.model_combo.addItems(AVAILABLE_MODELS)
        self.model_combo.setEditable(True)
        model_group.addWidget(self.model_combo)

        layout.addLayout(model_group)

        layout.addSpacing(10)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addWidget(self.btn_cancel)

        self.btn_save = QPushButton("Save Settings")
        self.btn_save.setProperty("class", "primaryButton")
        self.btn_save.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.btn_save)

        layout.addLayout(btn_layout)

    def _toggle_key_visibility(self):
        if self.key_input.echoMode() == QLineEdit.Password:
            self.key_input.setEchoMode(QLineEdit.Normal)
            self.btn_toggle_key.setText("Hide")
        else:
            self.key_input.setEchoMode(QLineEdit.Password)
            self.btn_toggle_key.setText("Show")

    def _load_current_values(self):
        load_dotenv(ENV_FILE_PATH, override=True)
        current_key = os.getenv("GEMINI_API_KEY", "")
        self.key_input.setText(current_key)

        current_model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
        idx = self.model_combo.findText(current_model)
        if idx >= 0:
            self.model_combo.setCurrentIndex(idx)
        else:
            self.model_combo.setEditText(current_model)

    def _save_settings(self):
        new_key = self.key_input.text().strip()
        new_model = self.model_combo.currentText().strip()

        # Update .env file only (per requirement: stored in .env only)
        try:
            # Ensure .env file exists
            if not os.path.exists(ENV_FILE_PATH):
                with open(ENV_FILE_PATH, "w", encoding="utf-8") as f:
                    pass

            set_key(ENV_FILE_PATH, "GEMINI_API_KEY", new_key)
            if new_model:
                set_key(ENV_FILE_PATH, "GEMINI_MODEL", new_model)

            # Reload into process environment
            load_dotenv(ENV_FILE_PATH, override=True)
            os.environ["GEMINI_API_KEY"] = new_key
            if new_model:
                os.environ["GEMINI_MODEL"] = new_model

            self.settings_saved.emit()
            self.accept()

        except Exception as err:
            QMessageBox.critical(
                self, "Error Saving Settings", f"Failed to write to .env file:\n{err}"
            )
