"""Diagram preview area with zoom, drag-to-pan, and export capabilities."""

from __future__ import annotations

import os

from PySide6.QtCore import QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QImageReader, QPainter, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGraphicsPixmapItem,
    QGraphicsScene,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class DiagramGraphicsView(QGraphicsView):
    """QGraphicsView with smooth Ctrl+wheel zoom and drag-to-pan."""

    def __init__(self, scene: QGraphicsScene, parent=None):
        super().__init__(scene, parent)
        QImageReader.setAllocationLimit(512)
        self.setRenderHints(
            QPainter.Antialiasing
            | QPainter.SmoothPixmapTransform
            | QPainter.TextAntialiasing
        )
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.NoFrame)
        self._current_zoom = 1.0

    def wheelEvent(self, event: QWheelEvent):
        # Ctrl + Wheel for zoom
        if event.modifiers() & Qt.ControlModifier:
            delta = event.angleDelta().y()
            if delta > 0:
                self.zoom_in(1.15)
            elif delta < 0:
                self.zoom_out(1.15)
            event.accept()
        else:
            super().wheelEvent(event)

    def zoom_in(self, factor: float = 1.2):
        self.scale(factor, factor)
        self._current_zoom *= factor

    def zoom_out(self, factor: float = 1.2):
        self.scale(1.0 / factor, 1.0 / factor)
        self._current_zoom /= factor

    def reset_zoom(self):
        self.resetTransform()
        self._current_zoom = 1.0


class DiagramPreviewWidget(QWidget):
    """Complete diagram preview section with controls and empty-state display."""

    generate_diagram_requested = Signal()
    save_diagram_requested = Signal(str, str, int)  # (path, format, dpi)
    status_message_requested = Signal(str)

    def __init__(self, parent=None, theme: str = "dark"):
        super().__init__(parent)
        self.theme = theme
        self.current_image_path: str | None = None
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Control Bar
        controls_layout = QHBoxLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(6)

        title_label = QLabel("ER Diagram Preview")
        title_label.setObjectName("sectionHeader")
        controls_layout.addWidget(title_label)

        controls_layout.addStretch()

        # Primary Generate Diagram Button (disabled while JSON is invalid/empty)
        self.btn_generate = QPushButton("▶ Generate Diagram")
        self.btn_generate.setProperty("class", "primaryButton")
        self.btn_generate.setToolTip("Render diagram from current JSON (Ctrl+Enter)")
        self.btn_generate.clicked.connect(self.generate_diagram_requested.emit)
        self.btn_generate.setEnabled(False)
        controls_layout.addWidget(self.btn_generate)

        # Zoom Controls
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_in.setProperty("class", "toolButton")
        self.btn_zoom_in.setToolTip("Zoom In")
        self.btn_zoom_in.setFixedWidth(30)
        self.btn_zoom_in.clicked.connect(self.zoom_in)

        self.btn_zoom_out = QPushButton("−")
        self.btn_zoom_out.setProperty("class", "toolButton")
        self.btn_zoom_out.setToolTip("Zoom Out")
        self.btn_zoom_out.setFixedWidth(30)
        self.btn_zoom_out.clicked.connect(self.zoom_out)

        self.btn_fit = QPushButton("Fit")
        self.btn_fit.setProperty("class", "toolButton")
        self.btn_fit.setToolTip("Fit diagram to window")
        self.btn_fit.clicked.connect(self.fit_to_window)

        controls_layout.addWidget(self.btn_zoom_in)
        controls_layout.addWidget(self.btn_zoom_out)
        controls_layout.addWidget(self.btn_fit)

        # DPI Selector for Export
        dpi_label = QLabel("DPI:")
        dpi_label.setStyleSheet("color: #94A3B8; font-size: 11px; margin-left: 4px;")
        self.dpi_combo = QComboBox()
        self.dpi_combo.addItems(["600", "300", "150"])
        self.dpi_combo.setToolTip(
            "Export DPI for PNG (SVG & PDF are vector formats and always sharp)"
        )
        self.dpi_combo.setFixedWidth(68)
        controls_layout.addWidget(dpi_label)
        controls_layout.addWidget(self.dpi_combo)

        # Save Diagram Button
        self.btn_save = QPushButton("Save Diagram…")
        self.btn_save.setProperty("class", "toolButton")
        self.btn_save.setToolTip("Save diagram as PNG, SVG or PDF (Ctrl+S)")
        self.btn_save.clicked.connect(self.prompt_save_diagram)
        self.btn_save.setEnabled(False)
        controls_layout.addWidget(self.btn_save)

        layout.addLayout(controls_layout)

        # Preview Container Frame
        self.preview_frame = QFrame()
        self.preview_frame.setObjectName("previewContainer")
        self.preview_frame.setProperty("class", "panelFrame")
        frame_layout = QVBoxLayout(self.preview_frame)
        frame_layout.setContentsMargins(0, 0, 0, 0)

        # Scene and GraphicsView
        self.scene = QGraphicsScene(self)
        self.view = DiagramGraphicsView(self.scene, self)
        frame_layout.addWidget(self.view)

        # Empty State Placeholder Overlay
        self.empty_widget = QWidget(self.preview_frame)
        empty_layout = QVBoxLayout(self.empty_widget)
        empty_layout.setAlignment(Qt.AlignCenter)
        empty_layout.setSpacing(10)

        self.empty_icon = QLabel("📊")
        self.empty_icon.setAlignment(Qt.AlignCenter)
        font_icon = QFont()
        font_icon.setPointSize(36)
        self.empty_icon.setFont(font_icon)

        self.empty_title = QLabel("Your diagram will appear here")
        self.empty_title.setAlignment(Qt.AlignCenter)
        font_title = QFont()
        font_title.setPointSize(14)
        font_title.setBold(True)
        self.empty_title.setFont(font_title)

        self.empty_desc = QLabel(
            "Describe your database on the left or edit the JSON,\nthen click 'Generate Diagram' to render."
        )
        self.empty_desc.setAlignment(Qt.AlignCenter)
        self.empty_desc.setStyleSheet("color: #64748B; font-size: 13px;")

        empty_layout.addWidget(self.empty_icon)
        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_desc)

        frame_layout.addWidget(self.empty_widget)
        layout.addWidget(self.preview_frame, stretch=1)

        self.pixmap_item: QGraphicsPixmapItem | None = None
        self._update_theme_colors()

    def set_theme(self, theme: str):
        self.theme = theme
        self._update_theme_colors()

    def _update_theme_colors(self):
        is_dark = self.theme == "dark"
        bg_color = QColor("#0B1120") if is_dark else QColor("#F8FAFC")
        self.scene.setBackgroundBrush(bg_color)
        title_color = "#F8FAFC" if is_dark else "#0F172A"
        self.empty_title.setStyleSheet(f"color: {title_color}; font-weight: 600;")

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.empty_widget.isVisible():
            self.empty_widget.setGeometry(self.preview_frame.rect())

    def display_image(self, image_path: str):
        """Displays the generated diagram image and fits it to view."""
        if not os.path.exists(image_path):
            return

        self.current_image_path = image_path
        pixmap = QPixmap(image_path)
        if pixmap.isNull():
            return

        self.scene.clear()
        self.pixmap_item = self.scene.addPixmap(pixmap)
        self.scene.setSceneRect(QRectF(pixmap.rect()))

        self.empty_widget.setVisible(False)
        self.view.setVisible(True)
        self.btn_save.setEnabled(True)

        self.fit_to_window()
        # Ensure diagram fills the preview area once geometry finishes layout
        QTimer.singleShot(60, self.fit_to_window)

    def clear_preview(self):
        self.scene.clear()
        self.pixmap_item = None
        self.current_image_path = None
        self.empty_widget.setVisible(True)
        self.btn_save.setEnabled(False)

    def zoom_in(self):
        if self.pixmap_item:
            self.view.zoom_in(1.25)

    def zoom_out(self):
        if self.pixmap_item:
            self.view.zoom_out(1.25)

    def fit_to_window(self):
        if self.pixmap_item:
            self.view.reset_zoom()
            self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def prompt_save_diagram(self):
        if not self.current_image_path:
            return

        file_filter = (
            "PNG High-Res Image (*.png);;"
            "SVG Vector Graphic (Sharp at any size) (*.svg);;"
            "PDF Vector Document (Sharp at any size) (*.pdf)"
        )
        chosen_path, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Save Diagram",
            "er-diagram.png",
            file_filter,
        )

        if chosen_path:
            # Determine format
            ext = os.path.splitext(chosen_path)[1].lower().lstrip(".")
            if not ext:
                if "svg" in selected_filter.lower():
                    ext = "svg"
                    chosen_path += ".svg"
                elif "pdf" in selected_filter.lower():
                    ext = "pdf"
                    chosen_path += ".pdf"
                else:
                    ext = "png"
                    chosen_path += ".png"
            elif "svg" in selected_filter.lower() and ext != "svg":
                ext = "svg"
                chosen_path += ".svg"
            elif "pdf" in selected_filter.lower() and ext != "pdf":
                ext = "pdf"
                chosen_path += ".pdf"

            try:
                dpi = int(self.dpi_combo.currentText())
            except (ValueError, TypeError):
                dpi = 600

            self.save_diagram_requested.emit(chosen_path, ext, dpi)
