"""
layout — scene layout engine for physics education video production.

Public API::

    from layout import LayoutEngine, Compositor, LayoutElement
    from layout import validate_scene, SceneValidationError
    from layout import ValidationReport, LayoutConstraintError
    from layout.contrast import contrast_ratio, auto_fix_text_contrast
    from layout import constants

Typical usage::

    engine = LayoutEngine(aspect="16:9")
    compositor = Compositor(engine)

    scene = {
        "background": "#f5e6d3",
        "elements": [
            {"role": "character_left",  "asset": "char.png", "scale": 0.85},
            {"role": "equation_center", "text": "p = mv",    "font_size": 72},
            {"role": "subtitle",        "text": "momentum",  "font_size": 32},
        ]
    }

    validate_scene(scene)
    compositor.render_frame(scene, "/tmp/frame.png")
"""

from .constants import (           # noqa: F401
    YOUTUBE_LONG,
    YOUTUBE_SHORT,
    ASPECT_TO_CANVAS,
    ZONES,
    Z_ORDER,
    SAFE_TOP,
    SAFE_BOTTOM,
    SAFE_LEFT,
    SAFE_RIGHT,
    WCAG_AA_NORMAL,
    WCAG_AA_LARGE,
)
from .element import LayoutElement           # noqa: F401
from .engine import (                        # noqa: F401
    LayoutEngine,
    LayoutConstraintError,
    ValidationReport,
    CheckResult,
)
from .contrast import (                      # noqa: F401
    contrast_ratio,
    relative_luminance,
    srgb_to_linear,
    auto_fix_text_contrast,
    sample_background_color,
    describe_contrast,
)
from .compositor import Compositor           # noqa: F401
try:
    from .scene_schema import (              # noqa: F401
        validate_scene,
        validate_scene_safe,
        SceneValidationError,
        SCENE_SCHEMA,
    )
except ModuleNotFoundError as exc:  # pragma: no cover - optional dependency path
    if exc.name != "jsonschema":
        raise

    def validate_scene(*args, **kwargs):  # type: ignore[no-redef]
        raise RuntimeError(
            "Scene validation requires the optional 'jsonschema' dependency."
        )

    def validate_scene_safe(*args, **kwargs):  # type: ignore[no-redef]
        return False, "Scene validation requires the optional 'jsonschema' dependency."

    class SceneValidationError(Exception):  # type: ignore[no-redef]
        pass

    SCENE_SCHEMA = None  # type: ignore[no-redef]

__all__ = [
    # Canvas constants
    "YOUTUBE_LONG",
    "YOUTUBE_SHORT",
    "ASPECT_TO_CANVAS",
    "ZONES",
    "Z_ORDER",
    "SAFE_TOP",
    "SAFE_BOTTOM",
    "SAFE_LEFT",
    "SAFE_RIGHT",
    "WCAG_AA_NORMAL",
    "WCAG_AA_LARGE",
    # Core classes
    "LayoutElement",
    "LayoutEngine",
    "Compositor",
    # Reports / exceptions
    "ValidationReport",
    "CheckResult",
    "LayoutConstraintError",
    # Contrast utilities
    "contrast_ratio",
    "relative_luminance",
    "srgb_to_linear",
    "auto_fix_text_contrast",
    "sample_background_color",
    "describe_contrast",
    # Schema
    "validate_scene",
    "validate_scene_safe",
    "SceneValidationError",
    "SCENE_SCHEMA",
]
