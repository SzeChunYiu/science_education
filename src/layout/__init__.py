"""
layout — scene layout elements and constants for physics education video production.
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
]
