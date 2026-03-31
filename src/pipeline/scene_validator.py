"""
scene_validator.py — Validates a list of scene descriptor dicts.

Validation rules
----------------
1. REQUIRED FIELDS: every scene must have ``template``, ``duration``,
   and ``elements``.  Missing ``scene_id`` or ``background`` are warnings,
   not errors.

2. DURATION TOO SHORT: duration < 1.0 seconds → error.

3. DURATION TOO LONG: duration > 15.0 seconds without a visual cue
   (i.e. no ``_source_visual_cue`` or it is None) → warning.

4. UNKNOWN TEMPLATE: template not in the known TEMPLATES set → warning.

5. ASSET PATHS: any element ``asset_path`` that is not None, not a
   ``PLACEHOLDER:`` string, and does not exist on disk → warning.

6. UNKNOWN ROLE: any element ``role`` that is not in the constants.ZONES
   set → warning.

7. EMPTY ELEMENTS: scenes with an empty ``elements`` list → warning.

8. MISSING TEXT AND ASSET: element has neither ``text`` nor ``asset_path``
   → error.

9. NO SCENES: empty scene list → error.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any

# Known templates (must stay in sync with scene_mapper.TEMPLATES)
_KNOWN_TEMPLATES = {
    "equation_reveal",
    "derivation_step",
    "character_scene",
    "two_element_comparison",
    "diagram_explanation",
    "animation_scene",
    "narration_with_caption",
}

# Known element roles from layout/constants.py ZONES + 'background'
_KNOWN_ROLES = {
    "character_left",
    "character_right",
    "character_center",
    "equation_center",
    "equation_right",
    "headline",
    "body_text",
    "caption",
    "diagram",
    "subtitle",
    "lower_third",
    "timeline",
    "background",
}

_MIN_DURATION = 1.0   # seconds
_MAX_DURATION = 15.0  # seconds — beyond this a lack of visual cue is flagged


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass
class ValidationIssue:
    """
    A single validation finding.

    Attributes
    ----------
    severity : str
        Either ``"error"`` (pipeline-blocking) or ``"warning"`` (advisory).
    scene_id : str or None
        The scene_id of the affected scene, or None for global issues.
    field : str or None
        The field name that triggered the issue, or None for structural issues.
    message : str
        Human-readable description.
    """

    severity: str   # "error" | "warning"
    scene_id: str | None
    field: str | None
    message: str

    def __str__(self) -> str:
        loc = self.scene_id or "GLOBAL"
        fld = f".{self.field}" if self.field else ""
        return f"[{self.severity.upper()}] {loc}{fld}: {self.message}"


@dataclass
class ValidationReport:
    """
    Aggregated result of scene validation.

    Attributes
    ----------
    scene_count : int
        Number of scenes examined.
    errors : list[ValidationIssue]
        Fatal issues that should block downstream processing.
    warnings : list[ValidationIssue]
        Advisory issues that should be reviewed but do not block.
    passed : bool
        True when ``errors`` is empty.
    """

    scene_count: int = 0
    errors: list[ValidationIssue] = field(default_factory=list)
    warnings: list[ValidationIssue] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """True when there are no errors (warnings are permitted)."""
        return len(self.errors) == 0

    def summary(self) -> str:
        """Return a compact one-line summary string."""
        status = "PASS" if self.passed else "FAIL"
        return (
            f"[{status}] {self.scene_count} scenes | "
            f"{len(self.errors)} error(s), {len(self.warnings)} warning(s)"
        )

    def print_report(self) -> None:
        """Print all issues to stdout, grouped by severity."""
        print(self.summary())
        for issue in self.errors:
            print(f"  {issue}")
        for issue in self.warnings:
            print(f"  {issue}")


# ---------------------------------------------------------------------------
# Validator
# ---------------------------------------------------------------------------

def validate_scene_sequence(scenes: list[dict]) -> ValidationReport:
    """
    Validate a list of scene descriptor dicts.

    Parameters
    ----------
    scenes : list[dict]
        Scene descriptors as produced by :func:`~scene_mapper.map_script_to_scenes`.

    Returns
    -------
    ValidationReport
        A report object containing errors, warnings, and a ``passed`` flag.

    Notes
    -----
    * The validator never raises — all issues are captured into the report.
    * Asset path existence is checked relative to the filesystem at call time.
      ``PLACEHOLDER:...`` strings are always accepted without a disk check.
    """
    report = ValidationReport(scene_count=len(scenes))

    def err(scene_id: str | None, field_name: str | None, msg: str) -> None:
        report.errors.append(ValidationIssue("error", scene_id, field_name, msg))

    def warn(scene_id: str | None, field_name: str | None, msg: str) -> None:
        report.warnings.append(ValidationIssue("warning", scene_id, field_name, msg))

    # Rule 9: empty scene list
    if not scenes:
        err(None, None, "Scene list is empty — no scenes to render.")
        return report

    seen_ids: set[str] = set()

    for i, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            err(None, None, f"Scene at index {i} is not a dict (got {type(scene).__name__}).")
            continue

        sid = scene.get("scene_id") or f"(index {i})"

        # Warn on duplicate scene_ids
        if scene.get("scene_id") in seen_ids:
            warn(sid, "scene_id", f"Duplicate scene_id '{sid}'.")
        if scene.get("scene_id"):
            seen_ids.add(scene["scene_id"])

        # Rule 1: required fields
        for required in ("template", "duration", "elements"):
            if required not in scene:
                err(sid, required, f"Required field '{required}' is missing.")

        if "scene_id" not in scene:
            warn(sid, "scene_id", "Field 'scene_id' is missing.")
        if "background" not in scene:
            warn(sid, "background", "Field 'background' is missing.")

        # Rule 4: unknown template
        template = scene.get("template", "")
        if template and template not in _KNOWN_TEMPLATES:
            warn(sid, "template", f"Unknown template '{template}'.")

        # Rules 2 & 3: duration
        duration = scene.get("duration")
        if duration is not None:
            try:
                dur_f = float(duration)
                if dur_f < _MIN_DURATION:
                    err(sid, "duration", f"Duration {dur_f:.2f}s is below minimum {_MIN_DURATION}s.")
                elif dur_f > _MAX_DURATION:
                    has_cue = bool(scene.get("_source_visual_cue"))
                    if not has_cue:
                        warn(
                            sid, "duration",
                            f"Duration {dur_f:.2f}s exceeds {_MAX_DURATION}s with no visual cue — "
                            "consider splitting this scene.",
                        )
            except (TypeError, ValueError):
                err(sid, "duration", f"Duration value {duration!r} is not numeric.")

        # Rule 7: empty elements
        elements = scene.get("elements")
        if elements is not None and isinstance(elements, list) and len(elements) == 0:
            warn(sid, "elements", "Scene has an empty elements list.")

        # Per-element validation
        if isinstance(elements, list):
            for j, elem in enumerate(elements):
                if not isinstance(elem, dict):
                    err(sid, f"elements[{j}]", f"Element is not a dict (got {type(elem).__name__}).")
                    continue

                elem_loc = f"elements[{j}]"

                # Rule 6: unknown role
                role = elem.get("role")
                if role and role not in _KNOWN_ROLES:
                    warn(sid, f"{elem_loc}.role", f"Unknown role '{role}'.")

                # Rule 8: missing text AND asset_path
                has_text = elem.get("text") is not None
                has_asset = elem.get("asset_path") is not None
                if not has_text and not has_asset:
                    err(sid, elem_loc, "Element has neither 'text' nor 'asset_path'.")

                # Rule 5: asset path existence
                asset_path = elem.get("asset_path")
                if asset_path and not str(asset_path).startswith("PLACEHOLDER:"):
                    if not os.path.exists(str(asset_path)):
                        warn(
                            sid,
                            f"{elem_loc}.asset_path",
                            f"Asset path does not exist: '{asset_path}'.",
                        )

    return report
