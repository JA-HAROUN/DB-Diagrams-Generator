"""Centralized styling and themes for the ER Diagram Generator GUI."""

FONT_FAMILY_UI = (
    "system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"
)
FONT_FAMILY_CODE = (
    "'JetBrains Mono', 'Fira Code', 'Cascadia Code', 'Consolas', 'Menlo', monospace"
)

DARK_COLORS = {
    "bg_main": "#0F172A",  # slate-900
    "bg_surface": "#1E293B",  # slate-800
    "bg_elevated": "#334155",  # slate-700
    "bg_input": "#0F172A",
    "border_subtle": "#334155",
    "border_focus": "#6366F1",  # Indigo accent
    "text_primary": "#F8FAFC",
    "text_secondary": "#94A3B8",
    "text_muted": "#64748B",
    "accent_primary": "#6366F1",  # Indigo-500
    "accent_hover": "#4F46E5",  # Indigo-600
    "accent_pressed": "#4338CA",  # Indigo-700
    "accent_disabled": "#334155",
    "success": "#10B981",  # Emerald-500
    "error": "#EF4444",  # Red-500
    "warning": "#F59E0B",  # Amber-500
}

LIGHT_COLORS = {
    "bg_main": "#F8FAFC",  # slate-50
    "bg_surface": "#FFFFFF",
    "bg_elevated": "#F1F5F9",  # slate-100
    "bg_input": "#FFFFFF",
    "border_subtle": "#E2E8F0",  # slate-200
    "border_focus": "#6366F1",
    "text_primary": "#0F172A",  # slate-900
    "text_secondary": "#475569",  # slate-600
    "text_muted": "#94A3B8",  # slate-400
    "accent_primary": "#6366F1",
    "accent_hover": "#4F46E5",
    "accent_pressed": "#4338CA",
    "accent_disabled": "#CBD5E1",
    "success": "#059669",
    "error": "#DC2626",
    "warning": "#D97706",
}


def get_stylesheet(theme: str = "dark") -> str:
    c = DARK_COLORS if theme == "dark" else LIGHT_COLORS

    return f"""
    /* Global Base */
    QMainWindow, QDialog, QWidget#centralWidget {{
        background-color: {c["bg_main"]};
        color: {c["text_primary"]};
        font-family: {FONT_FAMILY_UI};
        font-size: 13px;
    }}

    /* Panels & Containers */
    QFrame.panelFrame {{
        background-color: {c["bg_surface"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: 10px;
        padding: 8px;
    }}

    /* Top Bar */
    QFrame#topBar {{
        background-color: {c["bg_surface"]};
        border-bottom: 1px solid {c["border_subtle"]};
        padding: 6px 16px;
    }}

    QLabel#appTitle {{
        font-size: 16px;
        font-weight: 700;
        color: {c["text_primary"]};
        letter-spacing: -0.3px;
    }}

    QLabel#sectionHeader {{
        font-size: 13px;
        font-weight: 600;
        color: {c["text_secondary"]};
        text-transform: uppercase;
        letter-spacing: 0.5px;
        padding-bottom: 4px;
    }}

    /* Buttons */
    QPushButton {{
        background-color: {c["bg_elevated"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: 6px;
        padding: 7px 14px;
        font-size: 13px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {c["border_subtle"] if theme == "dark" else "#E2E8F0"};
        border-color: {c["text_muted"]};
    }}

    QPushButton:pressed {{
        background-color: {c["bg_main"]};
    }}

    QPushButton:disabled {{
        background-color: {c["bg_elevated"]};
        color: {c["text_muted"]};
        border-color: transparent;
    }}

    /* Primary Accent Button */
    QPushButton.primaryButton {{
        background-color: {c["accent_primary"]};
        color: #FFFFFF;
        border: 1px solid {c["accent_primary"]};
        font-weight: 600;
        border-radius: 8px;
    }}

    QPushButton.primaryButton:hover {{
        background-color: {c["accent_hover"]};
        border-color: {c["accent_hover"]};
    }}

    QPushButton.primaryButton:pressed {{
        background-color: {c["accent_pressed"]};
        border-color: {c["accent_pressed"]};
    }}

    QPushButton.primaryButton:disabled {{
        background-color: {c["accent_disabled"]};
        color: {c["text_muted"]};
        border-color: {c["accent_disabled"]};
    }}

    /* Ghost / Icon Buttons */
    QPushButton.ghostButton {{
        background-color: transparent;
        border: 1px solid transparent;
        padding: 5px 10px;
        border-radius: 6px;
    }}

    QPushButton.ghostButton:hover {{
        background-color: {c["bg_elevated"]};
        border-color: {c["border_subtle"]};
    }}

    /* Small Toolbar Buttons */
    QPushButton.toolButton {{
        background-color: {c["bg_elevated"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: 5px;
        padding: 4px 8px;
        font-size: 12px;
    }}

    QPushButton.toolButton:hover {{
        border-color: {c["accent_primary"]};
    }}

    /* Text Inputs */
    QTextEdit, QPlainTextEdit, QLineEdit {{
        background-color: {c["bg_input"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: 8px;
        padding: 8px;
        selection-background-color: {c["accent_primary"]};
        selection-color: #FFFFFF;
    }}

    QTextEdit:focus, QPlainTextEdit:focus, QLineEdit:focus {{
        border: 1.5px solid {c["border_focus"]};
    }}

    /* Code Editor Specific */
    QPlainTextEdit#jsonEditor {{
        font-family: {FONT_FAMILY_CODE};
        font-size: 12.5px;
        line-height: 1.4;
        border: 1px solid {c["border_subtle"]};
        border-radius: 8px;
        background-color: {c["bg_input"]};
    }}

    /* Flash Highlight for Editor */
    QPlainTextEdit#jsonEditor[flashing="true"] {{
        border: 2px solid {c["accent_primary"]};
    }}

    /* Combobox */
    QComboBox {{
        background-color: {c["bg_elevated"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: 6px;
        padding: 5px 10px;
        min-height: 24px;
    }}

    QComboBox:hover {{
        border-color: {c["accent_primary"]};
    }}

    QComboBox::drop-down {{
        border: 0;
        width: 20px;
    }}

    QComboBox QAbstractItemView {{
        background-color: {c["bg_surface"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_subtle"]};
        selection-background-color: {c["accent_primary"]};
        selection-color: #FFFFFF;
        border-radius: 6px;
        padding: 4px;
    }}

    /* Splitter */
    QSplitter::handle {{
        background-color: {c["border_subtle"]};
        width: 3px;
        height: 3px;
        margin: 0px 4px;
    }}

    QSplitter::handle:hover {{
        background-color: {c["accent_primary"]};
    }}

    /* Checkbox */
    QCheckBox {{
        color: {c["text_secondary"]};
        font-size: 12px;
        spacing: 6px;
    }}

    QCheckBox::indicator {{
        width: 16px;
        height: 16px;
        border-radius: 4px;
        border: 1px solid {c["border_subtle"]};
        background-color: {c["bg_input"]};
    }}

    QCheckBox::indicator:checked {{
        background-color: {c["accent_primary"]};
        border-color: {c["accent_primary"]};
    }}

    /* Status Bar */
    QStatusBar {{
        background-color: {c["bg_surface"]};
        border-top: 1px solid {c["border_subtle"]};
        color: {c["text_secondary"]};
        font-size: 12px;
        padding: 4px 12px;
    }}

    /* Progress Bar */
    QProgressBar {{
        border: none;
        background-color: {c["bg_elevated"]};
        height: 4px;
        text-align: center;
        border-radius: 2px;
    }}

    QProgressBar::chunk {{
        background-color: {c["accent_primary"]};
        border-radius: 2px;
    }}

    /* Tooltips */
    QToolTip {{
        background-color: {c["bg_surface"]};
        color: {c["text_primary"]};
        border: 1px solid {c["border_subtle"]};
        border-radius: 6px;
        padding: 5px 8px;
        font-size: 12px;
    }}

    /* Scrollbars */
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:vertical {{
        background: {c["border_subtle"]};
        min-height: 20px;
        border-radius: 5px;
        margin: 2px;
    }}

    QScrollBar::handle:vertical:hover {{
        background: {c["text_muted"]};
    }}

    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{
        background: none;
        border: none;
    }}

    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 0px;
    }}

    QScrollBar::handle:horizontal {{
        background: {c["border_subtle"]};
        min-width: 20px;
        border-radius: 5px;
        margin: 2px;
    }}

    QScrollBar::handle:horizontal:hover {{
        background: {c["text_muted"]};
    }}

    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal,
    QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {{
        background: none;
        border: none;
    }}
    """
