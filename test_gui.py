"""Headless automated test suite for ER Diagram Generator Desktop GUI."""

import json
import os
import sys
import tempfile
import unittest

# Ensure headless Qt platform
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import QPoint, Qt
from PySide6.QtGui import QImage, QTextCursor
from PySide6.QtWidgets import QApplication

from graph import db_drawing
from models import Attribute, Database, Entity, Relationship
from ui.editor import EditorSection
from ui.examples import EXAMPLES
from ui.main_window import MainWindow
from ui.preview import DiagramPreviewWidget
from ui.validator import ValidationResult, clean_json_text, validate_database_json

# Global QApplication instance for headless tests
app = QApplication.instance() or QApplication(sys.argv)


SAMPLE_VALID_JSON = """{
  "name": "TestCompany",
  "entities": [
    {
      "name": "Employee",
      "weak": false,
      "attributes": [
        {"name": "emp_id", "isPrimaryKey": true},
        {"name": "full_name", "composite": ["first", "last"]},
        {"name": "phone", "isMultiValued": true},
        {"name": "years_service", "derived": true}
      ]
    },
    {
      "name": "Department",
      "weak": false,
      "attributes": [
        {"name": "dept_id", "isPrimaryKey": true},
        {"name": "dname"}
      ]
    }
  ],
  "relationships": [
    {
      "name": "Manages",
      "entities": ["Employee", "Department"],
      "cardinalities": ["1", "1"],
      "participations": ["partial", "total"]
    }
  ]
}"""


class TestValidator(unittest.TestCase):
    """Unit tests for JSON syntax and schema validation."""

    def test_valid_json_schema(self):
        result = validate_database_json(SAMPLE_VALID_JSON)
        self.assertTrue(result.is_valid)
        self.assertIsNone(result.error_message)
        self.assertIsNotNone(result.database)
        self.assertEqual(result.database.name, "TestCompany")
        self.assertEqual(len(result.database.entities), 2)
        self.assertEqual(len(result.database.relationships), 1)

    def test_empty_json(self):
        result = validate_database_json("   ")
        self.assertFalse(result.is_valid)
        self.assertIn("empty", result.error_message.lower())

    def test_syntax_error_reporting(self):
        invalid_syntax = """{
  "name": "TestCompany",
  "entities": [
    { "name": "Employee",
  ]
}"""
        result = validate_database_json(invalid_syntax)
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.error_line)
        self.assertIsNotNone(result.error_col)

    def test_missing_entities_or_relationships(self):
        no_entities = '{"name": "Test", "relationships": []}'
        result = validate_database_json(no_entities)
        self.assertFalse(result.is_valid)
        self.assertIn("entities", result.error_message)

        no_relationships = '{"name": "Test", "entities": []}'
        result = validate_database_json(no_relationships)
        self.assertFalse(result.is_valid)
        self.assertIn("relationships", result.error_message)

    def test_relationship_referencing_unknown_entity(self):
        bad_ref = """{
  "entities": [
    {"name": "Employee", "attributes": [{"name": "id", "isPrimaryKey": true}]}
  ],
  "relationships": [
    {
      "name": "Works_In",
      "entities": ["Employee", "UnknownDepartment"],
      "cardinalities": ["N", "1"]
    }
  ]
}"""
        result = validate_database_json(bad_ref)
        self.assertFalse(result.is_valid)
        self.assertIn("UnknownDepartment", result.error_message)

    def test_flexible_cardinality_strings(self):
        """Verify unusual and varied cardinality formats (N:1, 1:N, M:N, 1:1, N:M) are accepted."""
        for card in ["N:1", "1:N", "M:N", "1:1", "N:M", "1:M:N"]:
            json_text = f"""{{
  "entities": [
    {{"name": "A", "attributes": [{{"name": "id", "isPrimaryKey": true}}]}},
    {{"name": "B", "attributes": [{{"name": "id", "isPrimaryKey": true}}]}}
  ],
  "relationships": [
    {{
      "name": "Rel",
      "entity1": "A", "entity2": "B",
      "cardinality": "{card}"
    }}
  ]
}}"""
            res = validate_database_json(json_text)
            self.assertTrue(res.is_valid, f"Failed to accept cardinality: {card}")


class TestAICleaner(unittest.TestCase):
    """Unit tests for clean_json_text function."""

    def test_clean_fenced_json(self):
        raw = "```json\n" + SAMPLE_VALID_JSON + "\n```"
        cleaned = clean_json_text(raw)
        parsed = json.loads(cleaned)
        self.assertEqual(parsed["name"], "TestCompany")

    def test_clean_raw_fence_without_tag(self):
        raw = "```\n" + SAMPLE_VALID_JSON + "\n```"
        cleaned = clean_json_text(raw)
        parsed = json.loads(cleaned)
        self.assertEqual(parsed["name"], "TestCompany")

    def test_clean_surrounding_conversational_text(self):
        raw = f"Here is the database you requested:\n```json\n{SAMPLE_VALID_JSON}\n```\nHope this helps!"
        cleaned = clean_json_text(raw)
        parsed = json.loads(cleaned)
        self.assertEqual(parsed["name"], "TestCompany")


class TestRenderer(unittest.TestCase):
    """Unit tests for rendering diagrams in temp directories."""

    def setUp(self):
        self.result = validate_database_json(SAMPLE_VALID_JSON)
        self.database = self.result.database

    def test_render_png_at_high_dpi(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "test_diagram_450")
            out_path = db_drawing(
                self.database, filename=temp_file, format="png", view=False
            )
            self.assertTrue(os.path.exists(out_path))
            self.assertTrue(out_path.endswith(".png"))
            self.assertGreater(os.path.getsize(out_path), 5000)

            img = QImage(out_path)
            self.assertFalse(img.isNull())
            self.assertGreater(img.width(), 800)
            self.assertGreater(img.height(), 400)

    def test_render_svg_vector(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "test_diagram")
            out_path = db_drawing(
                self.database, filename=temp_file, format="svg", view=False
            )
            self.assertTrue(os.path.exists(out_path))
            self.assertTrue(out_path.endswith(".svg"))
            with open(out_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("<svg", content)

    def test_render_pdf_vector(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_file = os.path.join(temp_dir, "test_diagram")
            out_path = db_drawing(
                self.database, filename=temp_file, format="pdf", view=False
            )
            self.assertTrue(os.path.exists(out_path))
            self.assertTrue(out_path.endswith(".pdf"))
            with open(out_path, "rb") as f:
                header = f.read(5)
            self.assertEqual(header, b"%PDF-")


class TestGUIFullFlow(unittest.TestCase):
    """End-to-end integration tests of MainWindow workflows headlessly."""

    def setUp(self):
        self.window = MainWindow()
        self.window.show()
        QApplication.processEvents()

    def tearDown(self):
        self.window.close()
        QApplication.processEvents()

    def test_initial_window_state(self):
        """Initial state: empty editor, disabled generate diagram button, empty preview."""
        self.assertEqual(self.window.editor_section.get_json_content(), "")
        self.assertFalse(self.window.preview_widget.btn_generate.isEnabled())
        self.assertTrue(self.window.preview_widget.empty_widget.isVisible())

    def test_load_example_and_validation(self):
        """Loading an example populates prompt and editor and triggers validation."""
        example = EXAMPLES["Company (Lab 1)"]
        self.window.load_example(example)

        self.assertIn("Employee", self.window.editor_section.get_json_content())
        self.assertEqual(self.window.prompt_input.toPlainText(), example["description"])

        # Run validation
        self.window.editor_section.editor.run_validation()
        self.assertTrue(self.window.preview_widget.btn_generate.isEnabled())
        self.assertIn("Valid", self.window.editor_section.status_label.text())

    def test_edit_json_to_invalid_and_fix(self):
        """Typing invalid JSON disables Generate Diagram; fixing it re-enables it."""
        # Start with valid JSON
        self.window.editor_section.set_json_content(
            SAMPLE_VALID_JSON, ask_confirmation=False
        )
        self.window.editor_section.editor.run_validation()
        self.assertTrue(self.window.preview_widget.btn_generate.isEnabled())

        # Break JSON syntax
        self.window.editor_section.editor.setPlainText('{"entities": [ invalid syntax }')
        self.window.editor_section.editor.run_validation()
        self.assertFalse(self.window.preview_widget.btn_generate.isEnabled())
        self.assertIn("Invalid", self.window.editor_section.status_label.text())
        self.assertIsNotNone(self.window.editor_section.editor.error_line_to_highlight)

        # Fix JSON syntax
        self.window.editor_section.editor.setPlainText(SAMPLE_VALID_JSON)
        self.window.editor_section.editor.run_validation()
        self.assertTrue(self.window.preview_widget.btn_generate.isEnabled())
        self.assertIn("Valid", self.window.editor_section.status_label.text())

    def test_render_and_preview_controls(self):
        """Test diagram rendering into preview widget and zoom controls."""
        self.window.editor_section.set_json_content(
            SAMPLE_VALID_JSON, ask_confirmation=False
        )
        self.window.editor_section.editor.run_validation()

        # Render diagram synchronously for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = os.path.join(temp_dir, "preview_test")
            rendered = db_drawing(
                self.window.current_database,
                filename=temp_path,
                format="png",
                view=False,
            )
            self.window.preview_widget.display_image(rendered)

            # Preview assertions
            self.assertFalse(self.window.preview_widget.empty_widget.isVisible())
            self.assertTrue(self.window.preview_widget.btn_save.isEnabled())

            # Zoom controls
            init_zoom = self.window.preview_widget.view._current_zoom
            self.window.preview_widget.zoom_in()
            self.assertGreater(self.window.preview_widget.view._current_zoom, init_zoom)
            self.window.preview_widget.zoom_out()
            self.window.preview_widget.fit_to_window()

    def test_save_diagram_png_svg_pdf_and_double_save(self):
        """
        Verify Bug 1 fix:
        Saving diagram must NOT close the app, must save to chosen path,
        and must allow saving twice in a row (PNG, SVG, PDF).
        """
        self.window.editor_section.set_json_content(
            SAMPLE_VALID_JSON, ask_confirmation=False
        )
        self.window.editor_section.editor.run_validation()

        with tempfile.TemporaryDirectory() as temp_dir:
            # 1. First Save: PNG
            target_png = os.path.join(temp_dir, "exported_er.png")
            self.window.save_diagram_to_path(target_png, "png")

            # Wait for save worker thread to finish
            if self.window.save_worker:
                self.window.save_worker.wait(5000)
            QApplication.processEvents()

            self.assertTrue(os.path.exists(target_png))
            self.assertGreater(os.path.getsize(target_png), 1000)

            # Verify image validity and dimensions via QImage
            qimg = QImage(target_png)
            self.assertFalse(qimg.isNull())
            self.assertGreater(qimg.width(), 800)

            # Verify status message
            self.assertIn("Saved to", self.window.status_message.text())
            self.assertIn(target_png, self.window.status_message.text())

            # Verify window object is alive and usable
            self.assertIsNotNone(self.window.editor_section)

            # 2. Second Save in a row: SVG vector format
            target_svg = os.path.join(temp_dir, "exported_er.svg")
            self.window.save_diagram_to_path(target_svg, "svg")

            if self.window.save_worker:
                self.window.save_worker.wait(5000)
            QApplication.processEvents()

            self.assertTrue(os.path.exists(target_svg))
            with open(target_svg, "r", encoding="utf-8") as f:
                self.assertIn("<svg", f.read())

            self.assertIn("Saved to", self.window.status_message.text())
            self.assertIn(target_svg, self.window.status_message.text())

            # 3. Third Save: PDF format
            target_pdf = os.path.join(temp_dir, "exported_er.pdf")
            self.window.save_diagram_to_path(target_pdf, "pdf")

            if self.window.save_worker:
                self.window.save_worker.wait(5000)
            QApplication.processEvents()

            self.assertTrue(os.path.exists(target_pdf))
            with open(target_pdf, "rb") as f:
                self.assertEqual(f.read(5), b"%PDF-")

    def test_rotating_status_feedback(self):
        """Verify rotating feedback messages in status bar while task runs."""
        test_messages = ["Step 1: Reading description", "Step 2: Structuring schema"]
        self.window.start_status_rotation(test_messages)
        QApplication.processEvents()
        self.assertTrue(self.window.status_timer.isActive())
        self.assertFalse(self.window.progress_bar.isHidden())

        # Tick 1: should append animated dots
        self.window._on_status_tick()
        status_text = self.window.status_message.text()
        self.assertIn("Reading description", status_text)
        self.assertIn(".", status_text)

        # Stop rotation
        self.window.stop_status_rotation("Operation completed successfully.")
        self.assertFalse(self.window.status_timer.isActive())
        self.assertFalse(self.window.progress_bar.isVisible())
        self.assertEqual(self.window.status_message.text(), "Operation completed successfully.")

    def test_blank_template_and_format(self):
        """Test inserting new blank template and formatting JSON."""
        self.window.editor_section.insert_blank_template()
        content = self.window.editor_section.get_json_content()
        self.assertIn('"entities"', content)
        self.assertIn('"relationships"', content)

        # Format JSON
        self.window.editor_section.format_json()
        self.assertIn("entities", self.window.editor_section.get_json_content())

    def test_file_load_and_save(self):
        """Test loading JSON from file."""
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            f.write(SAMPLE_VALID_JSON)
            temp_filename = f.name

        try:
            self.window.editor_section.load_file(temp_filename)
            self.assertIn("TestCompany", self.window.editor_section.get_json_content())
        finally:
            if os.path.exists(temp_filename):
                os.remove(temp_filename)

    def test_missing_api_key_disables_ai_only(self):
        """When API key is missing, only AI button is disabled; app stays fully usable."""
        orig_key = os.environ.get("GEMINI_API_KEY")
        try:
            os.environ.pop("GEMINI_API_KEY", None)
            self.window._check_api_key_status()
            self.assertFalse(self.window.btn_generate_ai.isEnabled())
            self.assertIn(
                "Gemini API key is not set", self.window.btn_generate_ai.toolTip()
            )

            # Editor and Diagram preview must stay fully usable
            self.window.editor_section.set_json_content(
                SAMPLE_VALID_JSON, ask_confirmation=False
            )
            self.window.editor_section.editor.run_validation()
            self.assertTrue(self.window.preview_widget.btn_generate.isEnabled())
        finally:
            if orig_key:
                os.environ["GEMINI_API_KEY"] = orig_key

    def test_ai_response_review_flow(self):
        """Simulate AI response: inserted into editor, validates, not auto-rendered by default."""
        res = validate_database_json(SAMPLE_VALID_JSON)
        self.window._on_ai_success(res.database, SAMPLE_VALID_JSON)

        # JSON is in editor for review
        self.assertIn("TestCompany", self.window.editor_section.get_json_content())
        # Automatically saved to generated_database.json
        self.assertTrue(os.path.exists("generated_database.json"))

        # Status message instructs user to review before generating
        self.assertIn("review it", self.window.status_message.text().lower())

    def test_theme_toggle(self):
        """Toggle theme changes dark/light styles."""
        initial_theme = self.window.theme
        self.window.toggle_theme()
        self.assertNotEqual(self.window.theme, initial_theme)
        self.window.toggle_theme()
        self.assertEqual(self.window.theme, initial_theme)


if __name__ == "__main__":
    unittest.main()
