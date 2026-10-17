You are working inside my existing project "Lab-1" (an AI-powered ER Diagram Generator for a Database Systems course). I already have a working CLI version. Your task: build a modern, minimalistic desktop GUI on top of it using PySide6 (already installed). Do NOT break or rewrite the CLI.

## Step 0: Read first

Before writing code, read main.py, ai.py, graph.py, helper_func.py, models.py, file_picker.py and README.md. Understand how the project (1) turns a text description into JSON via the Gemini API, and (2) renders JSON into an ER diagram PNG. Reuse those functions by importing them. If a function mixes logic with print()/input()/CLI code, make a minimal refactor so it can be called from the GUI (return values / raise exceptions instead of printing), while keeping the CLI working. Put all GUI code in new files (e.g. gui.py, plus a gui/ folder if needed). Do not hardcode API keys; keep using the existing .env setup.

## Layout

A single main window, with a minimal, clean split layout:

**Left panel: Input**

1. "AI Prompt" section: a multi-line text box (placeholder: "Describe your system, e.g. A university has students, courses and instructors...") with a "Generate JSON with AI" button below it.
2. "JSON Editor" section: a code-style editor (monospace font, line numbers, JSON syntax highlighting) showing the JSON. The user can either get it from the AI or type/paste/edit it manually.
   - Live validation while typing (debounced ~400ms): a small status indicator under the editor, "✓ Valid JSON" in green, or "✗ Invalid JSON: <message> (line X, col Y)" in red. Highlight the offending line when possible.
   - Beyond syntax, validate against the lab's schema: top-level "entities" (list) and "relationships" (list); each entity has "name" and "attributes"; each attribute has "name" and optional "isPrimaryKey" (bool), "isMultiValued" (bool), "composite" (list of strings); each relationship has "entity1", "entity2", "name", "cardinality"; relationship entities must exist in entities. Show clear, human-readable errors.
   - Buttons: "Format JSON" (pretty-print), "Copy", "Open JSON…", "Save JSON…", "Clear", "New blank template".

**Right panel: Diagram preview**

- A large preview area that shows the generated ER diagram PNG, with a friendly empty state ("Your diagram will appear here").
- A "Generate Diagram" primary button (disabled while JSON is invalid) that renders the editor's JSON using my existing renderer and displays the resulting image.
- Zoom in / zoom out / fit-to-window controls, mouse-wheel zoom (Ctrl+wheel), and drag-to-pan.
- "Save Diagram…" button opening a native save dialog (QFileDialog) so the user chooses where to save. Offer PNG, SVG and PDF if the renderer supports it; otherwise PNG only. Default filename "er-diagram.png".

**Bottom: Status bar** with short messages (e.g. "Diagram generated", "Saved to …", "Generating with AI…").

## Three input paths (all equal)

- The user can fill the JSON Editor in any of three ways: (1) AI generation from the prompt box, (2) typing/pasting JSON manually, (3) importing a .json file via "Open JSON…" or drag & drop.
- The AI prompt box is optional. Generate Diagram must work with no AI prompt and no API key, as long as the editor contains valid JSON.
- If the Gemini API key is missing, only the "Generate JSON with AI" button should be disabled (with a tooltip explaining why). The rest of the app must stay fully usable.
- Imported files go through the same validation as typed JSON. If the file is not valid JSON or doesn't match the schema, load the text into the editor anyway and show the error so the user can fix it.
- "New blank template" (button or Examples entry) inserts a minimal valid skeleton ({"entities": [], "relationships": []}) for users who want to write from scratch.

## AI → Editor → Diagram flow (important)

- When the user clicks "Generate JSON with AI", the AI's JSON must ALWAYS be placed into the JSON Editor so the user can review and edit it. Never render the diagram automatically from the AI response.
- After the JSON is inserted: pretty-print it, run validation immediately, show the status indicator ("✓ Valid JSON" or the error), and show a brief status message ("JSON generated, review it, then click Generate Diagram").
- Briefly highlight/flash the editor (e.g. a subtle accent border for ~1 second) so the user notices the new content.
- If the editor already contains JSON, ask for confirmation before overwriting it ("Replace current JSON?"), or keep an undo step (Ctrl+Z must restore the previous content).
- The diagram is generated only when the user clicks "Generate Diagram" (or presses Ctrl+Enter), using whatever is currently in the editor, including the user's edits.
- Optional: a checkbox "Auto-generate diagram after AI" that is OFF by default.

## UX requirements

- All slow work (Gemini API call, diagram rendering) must run in a background thread (QThread / QThreadPool + signals) so the UI never freezes. While running: show a progress/busy indicator, disable the relevant buttons, and allow cancelling the AI request if feasible.
- Errors (API failure, no internet, missing API key, invalid AI output, renderer failure, missing Graphviz executable) must show a clear non-technical message (inline banner or QMessageBox), never a crash or raw traceback. The full error can go to a collapsible "details" area.
- If the AI returns JSON wrapped in markdown fences or extra text, strip it and still extract valid JSON. If the result is still invalid, put the raw text in the editor and show the error so the user can fix it manually.
- Keyboard shortcuts: Ctrl+Enter = Generate Diagram, Ctrl+G = Generate JSON with AI, Ctrl+S = Save Diagram, Ctrl+O = Open JSON, Ctrl+Shift+F = Format JSON.
- Drag & drop a .json file onto the window to load it.
- Window is resizable with a sensible minimum size (~1000x650); panels in a QSplitter so the user can resize them. Remember window size/splitter position (QSettings).

## Design

- Minimalistic, modern, and polished: generous spacing, rounded corners (8–12px), subtle borders, soft shadows, no clutter.
- Dark theme by default with a light theme toggle (button in the top bar). Use one accent color (e.g. indigo/violet #6366F1) for primary buttons; neutral grays elsewhere; green/red only for success/error.
- Style it via a centralized QSS stylesheet (separate file or constant), not scattered inline styles. Use a clean font (e.g. Inter/Segoe UI/system default) for UI and a monospace font (JetBrains Mono / Consolas / Menlo fallback) for the editor.
- Small top bar with the app title ("ER Diagram Generator") on the left and theme toggle + "Examples" menu on the right.
- Buttons have hover/pressed/disabled states; primary vs secondary vs ghost button styles; tooltips on all icon buttons.

## Extra features

- "Examples" dropdown with 3 ready-made sample descriptions/JSON (e.g. Employee–Department from the lab, University, Hospital) that fill the prompt/editor.
- Prompt history (last ~10 prompts, in a dropdown), saved locally.
- Settings dialog to enter/change the Gemini API key (saved to .env or QSettings) and optionally choose the model name.
- Unsaved-changes confirmation when closing, if the JSON was edited and not saved.
- Automatically save the last generated JSON to generated_database.json (as the CLI does) so both modes stay consistent.

## Deliverables

1. gui.py (entry point: `python gui.py` launches the app) and any supporting modules, with clear structure: separate widgets, worker classes, and styling.
2. requirements.txt updated with PySide6 and anything else needed.
3. README.md updated with a "GUI usage" section: how to run, features, screenshots placeholder.
4. Keep the code well-commented and PEP8-clean. After building, run the app, test the full flow (prompt → AI JSON → review in editor → edit → invalid JSON error → fix → Generate Diagram → zoom → save; also test typing JSON manually and opening a .json file with no API key set), fix any bugs, and summarize what you did and any assumptions.

Since you can't see the window, test the logic headlessly (QT_QPA_PLATFORM=offscreen): JSON validation, the AI-output cleaner, the renderer call and the file save. I will check the visual layout myself.