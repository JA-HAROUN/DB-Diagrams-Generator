"""Background worker threads for AI generation and Graphviz diagram rendering."""

from __future__ import annotations

import os
import tempfile
import traceback

from PySide6.QtCore import QThread, Signal

from ai import generate_database
from graph import db_drawing
from models import Database


class AIWorker(QThread):
    """Executes Gemini AI model generation in a background thread."""

    success = Signal(object, str)  # (Database instance, formatted JSON string)
    error = Signal(str, str)  # (short_message, detailed_traceback)
    finished = Signal()

    def __init__(self, prompt: str, model: str | None = None, parent=None):
        super().__init__(parent)
        self.prompt = prompt
        self.model = model
        self._is_cancelled = False

    def cancel(self):
        self._is_cancelled = True

    def run(self):
        try:
            if self._is_cancelled:
                return

            database = generate_database(self.prompt, model=self.model)

            if self._is_cancelled:
                return

            if database is None:
                self.error.emit(
                    "The AI did not return a valid database structure.",
                    "The response could not be parsed into the required ER model.",
                )
                return

            json_str = database.model_dump_json(indent=2)
            self.success.emit(database, json_str)

        except Exception as err:
            if self._is_cancelled:
                return

            err_str = str(err)
            detail = traceback.format_exc()

            if "API_KEY_INVALID" in err_str or "API key not valid" in err_str:
                short_msg = "Invalid Gemini API key. Please check your key in Settings."
            elif "ResourceExhausted" in err_str or "429" in err_str:
                short_msg = (
                    "Gemini API rate limit exceeded. Please try again in a few moments."
                )
            elif "getaddrinfo failed" in err_str or "ConnectionError" in err_str:
                short_msg = (
                    "Network connection failed. Please check your internet connection."
                )
            else:
                short_msg = f"AI Generation failed: {err}"

            self.error.emit(short_msg, detail)

        finally:
            self.finished.emit()


class RenderWorker(QThread):
    """Executes Graphviz ER diagram rendering in a background thread into a temp or target file."""

    success = Signal(str)  # Rendered file path
    error = Signal(str, str)  # (short_message, detailed_traceback)
    finished = Signal()

    def __init__(
        self,
        database: Database,
        output_format: str = "png",
        target_path: str | None = None,
        parent=None,
    ):
        super().__init__(parent)
        self.database = database
        self.output_format = output_format
        self.target_path = target_path

    def run(self):
        try:
            # If target_path is specified, save there; otherwise render into a temp file
            if self.target_path:
                base_name = os.path.splitext(self.target_path)[0]
                rendered = db_drawing(
                    self.database,
                    filename=base_name,
                    format=self.output_format,
                    view=False,
                )
                # Guarantee the exported file is at exactly the path requested
                if rendered != self.target_path and os.path.exists(rendered):
                    import shutil

                    shutil.move(rendered, self.target_path)
                    rendered = self.target_path
            else:
                # Render preview to a temporary file
                temp_dir = tempfile.gettempdir()
                temp_base = os.path.join(temp_dir, f"er_preview_{os.getpid()}")
                rendered = db_drawing(
                    self.database,
                    filename=temp_base,
                    format="png",
                    view=False,
                )

            self.success.emit(rendered)

        except Exception as err:
            err_str = str(err)
            detail = traceback.format_exc()

            if (
                "failed to execute" in err_str
                or "ExecutableNotFound" in err_str
                or "No such file" in err_str
            ):
                short_msg = "Graphviz 'dot' executable was not found. Please verify Graphviz is installed."
            else:
                short_msg = f"Diagram rendering failed: {err}"

            self.error.emit(short_msg, detail)

        finally:
            self.finished.emit()
