"""
Layout constants for physics education video production.

Defines canvas sizes, safe zones, grid configuration, semantic zone mappings,
and rendering parameters for both YouTube Long (16:9) and Shorts (9:16) formats.
"""

# ---------------------------------------------------------------------------
# Canvas sizes (width, height) in pixels
# ---------------------------------------------------------------------------
YOUTUBE_LONG = (1920, 1080)   # 16:9 landscape
YOUTUBE_SHORT = (1080, 1920)  # 9:16 portrait

ASPECT_TO_CANVAS = {
    "16:9": YOUTUBE_LONG,
    "9:16": YOUTUBE_SHORT,
}

# ---------------------------------------------------------------------------
# Safe zone fractions (relative to canvas dimensions)
# Content must stay within these margins.
# The subtitle zone occupies the bottom SAFE_BOTTOM fraction — only elements
# with role="subtitle" may be placed there.
# ---------------------------------------------------------------------------
SAFE_TOP = 0.05     # 5%  — reserved for platform UI chrome
SAFE_BOTTOM = 0.20  # 20% — reserved for subtitles
SAFE_LEFT = 0.05    # 5%
SAFE_RIGHT = 0.05   # 5%

# ---------------------------------------------------------------------------
# Content grid: 12 columns × 8 rows within the content-safe area
# (i.e., inside SAFE_LEFT/RIGHT/TOP and above the subtitle zone).
#
# Tuned for video readability:
# - headlines need a wider top band
# - equations need more horizontal breathing room
# - body/caption text should sit above the subtitle reserve
# - lower-thirds should be clearly separated from subtitle text
# ---------------------------------------------------------------------------
GRID_COLS = 12
GRID_ROWS = 8

# ---------------------------------------------------------------------------
# Zone definitions: (col_start, col_end, row_start, row_end) — 0-indexed,
# end is exclusive (like Python slices).
# All zones are defined within the content grid.
# The "subtitle" zone maps to the bottom strip (row 7 in the full 8-row grid,
# which physically sits within the subtitle safe zone).
# ---------------------------------------------------------------------------
ZONES = {
    "character_left":   (0, 3, 0, 7),   # left third, full content height
    "character_right":  (9, 12, 0, 7),  # right third, full content height
    "character_center": (4, 8, 0, 6),   # center, upper portion
    "equation_center":  (2, 10, 3, 5),  # centered, shallower math band
    "equation_right":   (4, 11, 3, 5),  # right-center math band
    "headline":         (1, 11, 0, 1),  # wide top strip for short titles
    "body_text":        (2, 10, 4, 6),   # mid-lower copy, above captions
    "caption":          (1, 11, 5, 7),   # wide lower caption band
    "diagram":          (4, 11, 1, 6),  # center-right diagram area
    "subtitle":         (0, 12, 7, 8),  # bottom strip (the subtitle zone itself)
    "lower_third":      (0, 7, 5, 6),   # lower-left label lane, above subtitles
    "timeline":         (1, 11, 3, 5),  # horizontal band center
}

# Roles whose content is permitted to occupy the subtitle zone
SUBTITLE_ROLES = {"subtitle"}

# ---------------------------------------------------------------------------
# WCAG contrast ratios
# ---------------------------------------------------------------------------
WCAG_AA_NORMAL = 4.5  # minimum ratio for normal text (< 18pt / < 14pt bold)
WCAG_AA_LARGE = 3.0   # minimum ratio for large text (>= 18pt or >= 14pt bold)

# ---------------------------------------------------------------------------
# Z-order: higher number renders on top
# ---------------------------------------------------------------------------
Z_ORDER = {
    "background":       0,
    "diagram":          10,
    "character_left":   20,
    "character_right":  20,
    "character_center": 20,
    "equation_center":  30,
    "equation_right":   30,
    "body_text":        40,
    "headline":         40,
    "caption":          40,
    "lower_third":      45,
    "subtitle":         50,
    "timeline":         15,
}

# Default Z for any role not explicitly listed
Z_ORDER_DEFAULT = 25

# ---------------------------------------------------------------------------
# Typography defaults
# ---------------------------------------------------------------------------
DEFAULT_FONT_SIZE = 36
DEFAULT_TEXT_COLOR = (26, 26, 26)    # near-black #1a1a1a
DEFAULT_FONT_PATH = None             # None = PIL default font; set to .ttf path if available

# ---------------------------------------------------------------------------
# Overlap resolution
# ---------------------------------------------------------------------------
MAX_OVERLAP_ITERATIONS = 10
OVERLAP_PUSH_FACTOR = 0.55  # fraction of overlap distance to push each element per iteration
