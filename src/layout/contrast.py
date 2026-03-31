"""
WCAG-compliant contrast utilities for the layout engine.

Provides:
  - sRGB → linear light conversion
  - Relative luminance (WCAG 2.1 formula)
  - Contrast ratio between two colors
  - Background color sampling from a PIL image region
  - Automatic contrast-fix recommendation for text on complex backgrounds
"""

from __future__ import annotations
from typing import Tuple, Optional
import numpy as np
from PIL import Image


# ---------------------------------------------------------------------------
# Core WCAG math
# ---------------------------------------------------------------------------

def srgb_to_linear(c: int) -> float:
    """
    Convert a single sRGB channel value (0-255) to linear light.

    Uses the IEC 61966-2-1 piecewise formula required by WCAG 2.1.

    Args:
        c: integer channel value in [0, 255]

    Returns:
        Linear light value in [0.0, 1.0]
    """
    normalised = c / 255.0
    if normalised <= 0.04045:
        return normalised / 12.92
    return ((normalised + 0.055) / 1.055) ** 2.4


def relative_luminance(rgb: Tuple[int, int, int]) -> float:
    """
    Compute WCAG 2.1 relative luminance for an (R, G, B) color.

    Args:
        rgb: tuple of integers in [0, 255]

    Returns:
        Relative luminance in [0.0, 1.0] (0 = black, 1 = white)
    """
    r, g, b = rgb
    R = srgb_to_linear(r)
    G = srgb_to_linear(g)
    B = srgb_to_linear(b)
    return 0.2126 * R + 0.7152 * G + 0.0722 * B


def contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
    """
    Compute WCAG 2.1 contrast ratio between two RGB colors.

    The ratio is always >= 1.0.  Maximum is 21:1 (black on white).

    Args:
        color1, color2: (R, G, B) tuples with values in [0, 255]

    Returns:
        Contrast ratio in [1.0, 21.0]
    """
    L1 = relative_luminance(color1)
    L2 = relative_luminance(color2)
    lighter = max(L1, L2)
    darker = min(L1, L2)
    return (lighter + 0.05) / (darker + 0.05)


# ---------------------------------------------------------------------------
# Background sampling
# ---------------------------------------------------------------------------

def sample_background_color(
    image: Image.Image,
    bbox: Tuple[int, int, int, int],
) -> Tuple[int, int, int]:
    """
    Sample the dominant/average color from a PIL image within a bounding box.

    Uses numpy for efficiency.  The region is flattened to RGB (alpha is
    discarded) and the per-channel mean is returned.

    Args:
        image: PIL Image (any mode; will be converted to RGB internally)
        bbox:  (x, y, x2, y2) pixel region to sample

    Returns:
        (R, G, B) tuple of mean color, each channel in [0, 255]
    """
    x, y, x2, y2 = bbox

    # Clamp bbox to image bounds
    iw, ih = image.size
    x  = max(0, min(x,  iw))
    y  = max(0, min(y,  ih))
    x2 = max(0, min(x2, iw))
    y2 = max(0, min(y2, ih))

    if x2 <= x or y2 <= y:
        # Degenerate region — return mid-grey as fallback
        return (128, 128, 128)

    rgb_image = image.convert("RGB")
    region = rgb_image.crop((x, y, x2, y2))
    arr = np.array(region, dtype=np.float32)  # shape: (h, w, 3)

    means = arr.mean(axis=(0, 1))
    return (int(round(means[0])), int(round(means[1])), int(round(means[2])))


def sample_background_color_at_element(
    image: Image.Image,
    bbox: Tuple[int, int, int, int],
    sample_fraction: float = 0.25,
) -> Tuple[int, int, int]:
    """
    Sample background color using only a central sub-region of the bbox.

    This avoids edge artifacts when an element partially overlaps a
    color-boundary on the background.

    Args:
        image:           PIL Image to sample from
        bbox:            (x, y, x2, y2) full element bounding box
        sample_fraction: fraction (each side) to inset for sampling

    Returns:
        (R, G, B) average color of the sampled region
    """
    x, y, x2, y2 = bbox
    dw = int((x2 - x) * sample_fraction)
    dh = int((y2 - y) * sample_fraction)
    sample_bbox = (x + dw, y + dh, x2 - dw, y2 - dh)
    return sample_background_color(image, sample_bbox)


# ---------------------------------------------------------------------------
# Auto contrast fix
# ---------------------------------------------------------------------------

_WHITE  = (255, 255, 255)
_DARK   = (26, 26, 26)     # near-black #1a1a1a


def auto_fix_text_contrast(
    text_color: Tuple[int, int, int],
    bg_color: Tuple[int, int, int],
    min_ratio: float = 4.5,
) -> Optional[dict]:
    """
    Given a text color and a sampled background color, determine whether
    the contrast is sufficient and — if not — recommend the least intrusive fix.

    Fix strategy (in order of preference):
      1. White text + drop shadow  — if white achieves min_ratio on this bg
      2. Dark text (#1a1a1a) + drop shadow — if dark achieves min_ratio
      3. Semi-transparent backing box — last resort; works universally

    Args:
        text_color: (R, G, B) of the proposed text color
        bg_color:   (R, G, B) sampled from the background beneath the text
        min_ratio:  minimum required WCAG contrast ratio (default 4.5 = AA normal)

    Returns:
        None if no fix is needed (contrast already meets min_ratio), otherwise
        a dict with key 'method' plus fix-specific keys:

        Shadow fix:
            {
                'method':       'shadow',
                'new_text_color': (R, G, B),
                'shadow_color': (R, G, B, A),   # RGBA
            }

        Backing-box fix:
            {
                'method':       'backing_box',
                'backing_color': (R, G, B, A),  # RGBA semi-transparent
            }
    """
    # Check current contrast
    current_ratio = contrast_ratio(text_color, bg_color)
    if current_ratio >= min_ratio:
        return None  # already fine

    # Strategy 1: white text
    white_ratio = contrast_ratio(_WHITE, bg_color)
    if white_ratio >= min_ratio:
        return {
            "method": "shadow",
            "new_text_color": _WHITE,
            "shadow_color": (0, 0, 0, 180),  # semi-transparent black shadow
        }

    # Strategy 2: dark text
    dark_ratio = contrast_ratio(_DARK, bg_color)
    if dark_ratio >= min_ratio:
        return {
            "method": "shadow",
            "new_text_color": _DARK,
            "shadow_color": (255, 255, 255, 160),  # light shadow for dark text
        }

    # Strategy 3: backing box (works regardless of bg)
    bg_luminance = relative_luminance(bg_color)
    if bg_luminance > 0.5:
        # Light background — use dark semi-transparent backing
        backing = (0, 0, 0, 153)      # rgba(0,0,0,0.6)
        new_text = _WHITE
    else:
        # Dark background — use light semi-transparent backing
        backing = (255, 255, 255, 217)  # rgba(255,255,255,0.85)
        new_text = _DARK

    return {
        "method": "backing_box",
        "new_text_color": new_text,
        "backing_color": backing,
    }


# ---------------------------------------------------------------------------
# Utility: describe a contrast check result as a human-readable string
# ---------------------------------------------------------------------------

def describe_contrast(
    text_color: Tuple[int, int, int],
    bg_color: Tuple[int, int, int],
    font_size: int = 36,
) -> str:
    """
    Return a human-readable contrast check summary.

    Args:
        text_color: (R, G, B)
        bg_color:   (R, G, B)
        font_size:  point size of text (determines AA threshold)

    Returns:
        String like "PASS 7.42:1 (AA normal)" or "FAIL 2.10:1 (needs 4.5)"
    """
    from .constants import WCAG_AA_NORMAL, WCAG_AA_LARGE
    ratio = contrast_ratio(text_color, bg_color)
    threshold = WCAG_AA_LARGE if font_size >= 18 else WCAG_AA_NORMAL
    level = "AA large" if font_size >= 18 else "AA normal"
    status = "PASS" if ratio >= threshold else "FAIL"
    return f"{status} {ratio:.2f}:1 ({level} threshold={threshold})"
