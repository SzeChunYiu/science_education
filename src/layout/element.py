"""
LayoutElement dataclass — the atomic unit of the scene layout system.

Each element represents one visual component of a video frame: a character
image, an equation, a caption, a subtitle line, etc.  The layout engine
resolves the x, y, w, h, and bbox fields from the role + scale + padding
inputs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, Tuple


@dataclass
class LayoutElement:
    """
    Describes a single renderable element in a video frame.

    Input fields (caller sets these):
        role        -- semantic role; must be a key in constants.ZONES
        asset_path  -- absolute path to a PNG image, or None for text elements
        text        -- text string for text/equation elements, or None for images
        font_size   -- point size for text rendering (ignored for images)
        color       -- (R, G, B) foreground text color (ignored for images)
        scale       -- 0.0–1.0 fraction of the zone dimensions; clamped to [0, 1]
        padding     -- pixels of internal padding inside the zone bounding box

    Resolved fields (set by LayoutEngine.place()):
        x, y        -- top-left corner in canvas pixel coordinates
        w, h        -- width and height in pixels after scaling
        bbox        -- (x, y, x2, y2) convenience tuple; x2 = x+w, y2 = y+h
        z           -- z-order value copied from constants.Z_ORDER
        contrast_fix-- dict describing any applied contrast fix, or None
    """

    # --- caller-supplied ---
    role: str
    asset_path: Optional[str] = None
    text: Optional[str] = None
    font_size: int = 36
    color: Tuple[int, int, int] = (26, 26, 26)
    scale: float = 1.0
    padding: int = 8

    # --- resolved by LayoutEngine ---
    x: int = field(default=0, init=True)
    y: int = field(default=0, init=True)
    w: int = field(default=0, init=True)
    h: int = field(default=0, init=True)
    bbox: Optional[Tuple[int, int, int, int]] = field(default=None, init=True)
    z: int = field(default=0, init=True)
    contrast_fix: Optional[dict] = field(default=None, init=True)
    roll_overflow: bool = field(default=False, init=True)
    roll_by_clause: bool = field(default=False, init=True)
    roll_progress: float = field(default=0.0, init=True)
    rotation_deg: float = field(default=0.0, init=True)
    rotation_pivot_rel: Tuple[float, float] = field(default=(0.5, 0.5), init=True)
    asset_anchor_mode: str = field(default="auto", init=True)

    def __post_init__(self) -> None:
        # Clamp scale to valid range
        self.scale = max(0.0, min(1.0, self.scale))
        self.roll_progress = max(0.0, min(1.0, self.roll_progress))
        self.rotation_deg = float(self.rotation_deg)

        px, py = self.rotation_pivot_rel
        self.rotation_pivot_rel = (
            max(0.0, min(1.0, float(px))),
            max(0.0, min(1.0, float(py))),
        )

        # Validate that element has either an asset or text (or both for labelled images)
        if self.asset_path is None and self.text is None:
            raise ValueError(
                f"LayoutElement with role='{self.role}' must have either "
                "asset_path or text (or both) set."
            )

        # Normalise color to a 3-tuple of ints if passed as hex string
        if isinstance(self.color, str):
            self.color = _hex_to_rgb(self.color)

    def update_bbox(self) -> None:
        """Recompute bbox from current x, y, w, h values."""
        self.bbox = (self.x, self.y, self.x + self.w, self.y + self.h)

    @property
    def is_image(self) -> bool:
        """True if this element is backed by a raster image asset."""
        return self.asset_path is not None

    @property
    def is_text_only(self) -> bool:
        """True if this element has no image asset (pure text)."""
        return self.asset_path is None and self.text is not None

    def __repr__(self) -> str:
        pos = f"({self.x},{self.y})" if self.bbox else "(unplaced)"
        return (
            f"LayoutElement(role={self.role!r}, "
            f"{'img=' + repr(self.asset_path) if self.is_image else 'text=' + repr(self.text)}, "
            f"bbox={self.bbox}, z={self.z})"
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """
    Convert a CSS hex color string (e.g. '#1a1a1a' or '1a1a1a') to
    an (R, G, B) integer tuple.
    """
    hex_color = hex_color.lstrip("#")
    if len(hex_color) not in (3, 6):
        raise ValueError(f"Invalid hex color: #{hex_color!r}")
    if len(hex_color) == 3:
        hex_color = "".join(c * 2 for c in hex_color)
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b)
