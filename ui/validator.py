"""JSON syntax and Database schema validator based on models.py."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any

from pydantic import ValidationError

from models import Database


@dataclass
class ValidationResult:
    is_valid: bool
    error_message: str | None = None
    error_line: int | None = None
    error_col: int | None = None
    database: Database | None = None


def find_line_for_token(text: str, token: str) -> int | None:
    """Find 1-indexed line number where token first appears."""
    if not token:
        return None
    for line_idx, line in enumerate(text.splitlines(), start=1):
        if token in line:
            return line_idx
    return None


def clean_json_text(text: str) -> str:
    """
    Clean AI output by stripping markdown code fences and extraneous text.
    Returns cleaned JSON string if possible, or stripped text.
    """
    if not text:
        return ""

    cleaned = text.strip()

    # Match ```json ... ``` or ``` ... ```
    fence_pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(fence_pattern, cleaned, re.IGNORECASE)
    if match:
        extracted = match.group(1).strip()
        try:
            json.loads(extracted)
            return extracted
        except Exception:
            cleaned = extracted

    # Try extracting outermost JSON object {...}
    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start != -1 and end != -1 and end > start:
        candidate = cleaned[start : end + 1]
        try:
            json.loads(candidate)
            return candidate
        except Exception:
            pass

    return cleaned


def validate_database_json(text: str) -> ValidationResult:
    """
    Validates JSON string against syntax rules and models.Database schema.
    Returns ValidationResult with detailed error message and line number if invalid.
    """
    if not text or not text.strip():
        return ValidationResult(
            is_valid=False,
            error_message="Editor is empty. Paste or generate JSON to begin.",
            error_line=1,
            error_col=1,
        )

    # 1. Syntax Validation
    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        return ValidationResult(
            is_valid=False,
            error_message=f"{err.msg} (line {err.lineno}, col {err.colno})",
            error_line=err.lineno,
            error_col=err.colno,
        )

    if not isinstance(data, dict):
        return ValidationResult(
            is_valid=False,
            error_message="Top-level JSON must be an object {...}",
            error_line=1,
            error_col=1,
        )

    # 2. Structural checks required by schema
    if "entities" not in data:
        return ValidationResult(
            is_valid=False,
            error_message="Missing required top-level 'entities' list.",
            error_line=1,
            error_col=1,
        )
    if not isinstance(data["entities"], list):
        return ValidationResult(
            is_valid=False,
            error_message="'entities' must be a list.",
            error_line=find_line_for_token(text, '"entities"'),
        )

    if "relationships" not in data:
        return ValidationResult(
            is_valid=False,
            error_message="Missing required top-level 'relationships' list.",
            error_line=1,
            error_col=1,
        )
    if not isinstance(data["relationships"], list):
        return ValidationResult(
            is_valid=False,
            error_message="'relationships' must be a list.",
            error_line=find_line_for_token(text, '"relationships"'),
        )

    # 3. Entity and Attribute field checks
    for idx, ent in enumerate(data["entities"], start=1):
        if not isinstance(ent, dict):
            return ValidationResult(
                is_valid=False,
                error_message=f"Entity #{idx} must be a JSON object.",
                error_line=find_line_for_token(text, f'"entities"'),
            )
        ent_name = ent.get("name")
        if not ent_name or not isinstance(ent_name, str):
            return ValidationResult(
                is_valid=False,
                error_message=f"Entity #{idx} is missing a valid 'name'.",
                error_line=find_line_for_token(text, str(ent_name or "name")),
            )
        if "attributes" not in ent or not isinstance(ent["attributes"], list):
            return ValidationResult(
                is_valid=False,
                error_message=f"Entity '{ent_name}' must have an 'attributes' list.",
                error_line=find_line_for_token(text, ent_name),
            )
        for a_idx, attr in enumerate(ent["attributes"], start=1):
            if not isinstance(attr, dict):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Attribute #{a_idx} in '{ent_name}' must be an object.",
                    error_line=find_line_for_token(text, ent_name),
                )
            if not attr.get("name"):
                return ValidationResult(
                    is_valid=False,
                    error_message=f"Attribute #{a_idx} in '{ent_name}' is missing 'name'.",
                    error_line=find_line_for_token(text, ent_name),
                )

    # 4. Pydantic Model Validation (based on models.py)
    try:
        db = Database.model_validate(data)
    except ValidationError as err:
        first_err = err.errors()[0]
        loc = " -> ".join(str(x) for x in first_err.get("loc", []))
        msg = first_err.get("msg", "Invalid schema")
        token_to_search = str(first_err["loc"][-1]) if first_err.get("loc") else ""
        err_line = find_line_for_token(text, token_to_search)
        return ValidationResult(
            is_valid=False,
            error_message=f"Schema error at {loc}: {msg}",
            error_line=err_line,
        )

    # 5. Semantic Validation: Relationship entities must exist in entities
    known_entities = {e.name.strip() for e in db.entities if e.name}
    for rel in db.relationships:
        rel_name = rel.name or "Unnamed relationship"
        if not rel.entities:
            return ValidationResult(
                is_valid=False,
                error_message=f"Relationship '{rel_name}' specifies no connected entities.",
                error_line=find_line_for_token(text, rel.name),
            )
        for target_entity in rel.entities:
            if target_entity not in known_entities:
                return ValidationResult(
                    is_valid=False,
                    error_message=(
                        f"Relationship '{rel_name}' references unknown entity "
                        f"'{target_entity}'. Entity does not exist in 'entities'."
                    ),
                    error_line=find_line_for_token(text, target_entity),
                )

    return ValidationResult(is_valid=True, database=db)
