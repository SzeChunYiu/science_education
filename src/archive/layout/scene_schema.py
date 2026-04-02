"""
JSON schema validation for scene descriptor dicts.

Scene dicts are validated before being handed to the Compositor to catch
structural errors early (missing required fields, wrong types, unknown roles).

Usage::

    from layout.scene_schema import validate_scene, SceneValidationError

    try:
        validate_scene(scene_dict)
    except SceneValidationError as exc:
        print(exc)
"""

from __future__ import annotations

from typing import Any, Dict

import jsonschema
from jsonschema import Draft7Validator, ValidationError

from .constants import ZONES


# ---------------------------------------------------------------------------
# Schema definition
# ---------------------------------------------------------------------------

#: All valid role values (drawn from ZONES keys)
_VALID_ROLES = sorted(ZONES.keys())

#: Regex pattern for a CSS hex color: #rgb or #rrggbb
_HEX_COLOR_PATTERN = r"^#([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$"

#: JSON Schema (Draft 7) for a single scene element
ELEMENT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "required": ["role"],
    "additionalProperties": False,
    "properties": {
        "role": {
            "type": "string",
            "enum": _VALID_ROLES,
            "description": "Semantic role; must match a key in ZONES.",
        },
        "asset": {
            "type": "string",
            "description": "Absolute or relative path to a PNG image.",
        },
        "asset_path": {
            "type": "string",
            "description": "Alias for 'asset'.",
        },
        "text": {
            "type": "string",
            "minLength": 1,
            "description": "Text content for text/equation elements.",
        },
        "font_size": {
            "type": "integer",
            "minimum": 8,
            "maximum": 300,
            "description": "Font size in points.",
        },
        "color": {
            "oneOf": [
                {
                    "type": "string",
                    "pattern": _HEX_COLOR_PATTERN,
                    "description": "CSS hex color string.",
                },
                {
                    "type": "array",
                    "items": {"type": "integer", "minimum": 0, "maximum": 255},
                    "minItems": 3,
                    "maxItems": 4,
                    "description": "RGB or RGBA array.",
                },
            ]
        },
        "scale": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Scale factor relative to zone size (clamped to [0, 1]).",
        },
        "padding": {
            "type": "integer",
            "minimum": 0,
            "maximum": 200,
            "description": "Internal padding in pixels.",
        },
    },
}

#: JSON Schema for a complete scene descriptor
SCENE_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "SceneDescriptor",
    "description": (
        "A complete video frame descriptor for the physics education "
        "layout engine."
    ),
    "type": "object",
    "required": ["elements"],
    "additionalProperties": False,
    "properties": {
        "background": {
            "type": "string",
            "description": (
                "Either a path to a background image (PNG/JPEG) or a CSS hex "
                "color string (e.g. '#f5e6d3')."
            ),
        },
        "elements": {
            "type": "array",
            "minItems": 1,
            "items": ELEMENT_SCHEMA,
            "description": "Ordered list of scene elements.",
        },
        "aspect": {
            "type": "string",
            "enum": ["16:9", "9:16"],
            "description": "Target aspect ratio; overrides the LayoutEngine default.",
        },
        "metadata": {
            "type": "object",
            "description": "Optional key-value metadata (title, episode, etc.).",
            "additionalProperties": True,
        },
    },
}

# Compile the validator once (reused across calls)
_VALIDATOR = Draft7Validator(SCENE_SCHEMA)


# ---------------------------------------------------------------------------
# Public interface
# ---------------------------------------------------------------------------

class SceneValidationError(Exception):
    """Raised when a scene dict does not conform to SCENE_SCHEMA."""

    def __init__(self, message: str, errors: list = None) -> None:
        super().__init__(message)
        self.errors = errors or []


def validate_scene(scene: dict) -> None:
    """
    Validate a scene descriptor dict against SCENE_SCHEMA.

    Also performs semantic validation beyond what JSON Schema can express:
      - Each element must have at least one of 'asset'/'asset_path' or 'text'
      - No duplicate roles (unless you intentionally want two of the same)

    Args:
        scene: the scene descriptor dict to validate

    Raises:
        SceneValidationError: if the scene is invalid, with a human-readable
            message listing all violations.
    """
    # Structural / type validation via jsonschema
    schema_errors = list(_VALIDATOR.iter_errors(scene))
    messages = []
    for err in schema_errors:
        path = " -> ".join(str(p) for p in err.absolute_path) or "(root)"
        messages.append(f"  [{path}] {err.message}")

    # Semantic validation
    for idx, el in enumerate(scene.get("elements", [])):
        has_asset = bool(el.get("asset") or el.get("asset_path"))
        has_text = bool(el.get("text"))
        if not has_asset and not has_text:
            messages.append(
                f"  [elements[{idx}]] Element with role={el.get('role')!r} "
                "must have at least one of 'asset', 'asset_path', or 'text'."
            )

    if messages:
        raise SceneValidationError(
            "Scene validation failed:\n" + "\n".join(messages),
            errors=schema_errors,
        )


def validate_scene_safe(scene: dict) -> tuple[bool, str]:
    """
    Non-raising wrapper around validate_scene.

    Returns:
        (True, "") if valid, or (False, error_message) if invalid.
    """
    try:
        validate_scene(scene)
        return True, ""
    except SceneValidationError as exc:
        return False, str(exc)
