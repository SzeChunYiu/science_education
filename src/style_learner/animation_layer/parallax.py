"""
Multi-layer parallax animation renderer.

Composites depth-split foreground / midground / background layers with
differential motion to create a parallax effect from static illustrations.
This is the core of the TED-Ed-style "camera motion on stills" approach.

All compositing uses PIL (no OpenCV dependency).
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
from typing import Optional

from PIL import Image

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MOTION_MULTIPLIERS = {
    "foreground": 1.0,
    "midground": 0.6,
    "background": 0.3,
}

CAMERA_MOTIONS = {
    "static": (0, 0),
    "pan_left": (-1, 0),
    "pan_right": (1, 0),
    "pan_up": (0, -1),
    "pan_down": (0, 1),
    "zoom_in": "zoom",
    "zoom_out": "zoom",
    "parallax": (1, 0),
}

MAGNITUDE_MAP = {
    "slow": 0.02,
    "medium": 0.05,
    "fast": 0.08,
}


# ---------------------------------------------------------------------------
# Easing
# ---------------------------------------------------------------------------

def _ease_in_out(t: float) -> float:
    """Cubic Hermite ease-in-out: smooth start and end."""
    t = max(0.0, min(1.0, t))
    return t * t * (3.0 - 2.0 * t)


# ---------------------------------------------------------------------------
# Core parallax renderer
# ---------------------------------------------------------------------------

def render_parallax_frames(
    fg: Image.Image,
    mid: Image.Image,
    bg: Image.Image,
    motion: str = "parallax",
    magnitude: str = "medium",
    duration: float = 5.0,
    fps: int = 30,
    canvas_size: tuple[int, int] = (1920, 1080),
) -> list[Image.Image]:
    """
    Render parallax animation frames from three depth-split layers.

    Parameters
    ----------
    fg : PIL.Image.Image
        Foreground layer (RGBA).
    mid : PIL.Image.Image
        Midground layer (RGBA).
    bg : PIL.Image.Image
        Background layer (RGBA).
    motion : str
        Camera motion type (key from ``CAMERA_MOTIONS``).
    magnitude : str
        Motion magnitude: ``"slow"``, ``"medium"``, or ``"fast"``.
    duration : float
        Duration in seconds.
    fps : int
        Frames per second (default 30).
    canvas_size : tuple[int, int]
        Output canvas (width, height).

    Returns
    -------
    list[PIL.Image.Image]
        List of composited RGBA frames.
    """
    if motion not in CAMERA_MOTIONS:
        logger.warning("Unknown motion %r, falling back to 'static'", motion)
        motion = "static"

    mag = MAGNITUDE_MAP.get(magnitude, MAGNITUDE_MAP["medium"])
    total_frames = max(1, int(duration * fps))
    cw, ch = canvas_size

    # Pre-scale layers to canvas size
    fg_scaled = _fit_to_canvas(fg, canvas_size)
    mid_scaled = _fit_to_canvas(mid, canvas_size)
    bg_scaled = _fit_to_canvas(bg, canvas_size)

    frames: list[Image.Image] = []

    for i in range(total_frames):
        t = i / max(1, total_frames - 1)  # normalised 0..1
        eased_t = _ease_in_out(t)

        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 255))

        motion_def = CAMERA_MOTIONS[motion]

        if motion_def == "zoom":
            # Zoom: differential scaling per layer
            is_zoom_in = (motion == "zoom_in")
            canvas = _composite_zoom(
                canvas, fg_scaled, mid_scaled, bg_scaled,
                eased_t, mag, is_zoom_in, canvas_size,
            )
        else:
            # Pan / parallax: differential translation per layer
            dx_dir, dy_dir = motion_def
            canvas = _composite_pan(
                canvas, fg_scaled, mid_scaled, bg_scaled,
                eased_t, mag, dx_dir, dy_dir, canvas_size,
            )

        frames.append(canvas)

    logger.info(
        "Rendered %d parallax frames (%s, %s, %.1fs @ %dfps)",
        len(frames), motion, magnitude, duration, fps,
    )
    return frames


# ---------------------------------------------------------------------------
# Compositing helpers
# ---------------------------------------------------------------------------

def _fit_to_canvas(
    layer: Image.Image,
    canvas_size: tuple[int, int],
) -> Image.Image:
    """Resize layer to cover canvas (maintain aspect ratio, crop overflow)."""
    cw, ch = canvas_size
    lw, lh = layer.size

    # Scale to cover canvas
    scale = max(cw / lw, ch / lh)
    new_w = int(lw * scale)
    new_h = int(lh * scale)

    resized = layer.resize((new_w, new_h), Image.LANCZOS)

    # Center-crop to canvas size
    left = (new_w - cw) // 2
    top = (new_h - ch) // 2
    cropped = resized.crop((left, top, left + cw, top + ch))

    return cropped


def _composite_pan(
    canvas: Image.Image,
    fg: Image.Image,
    mid: Image.Image,
    bg: Image.Image,
    eased_t: float,
    magnitude: float,
    dx_dir: int,
    dy_dir: int,
    canvas_size: tuple[int, int],
) -> Image.Image:
    """Composite three layers with differential pan offsets."""
    cw, ch = canvas_size
    max_dx = int(cw * magnitude)
    max_dy = int(ch * magnitude)

    layers = [
        (bg, MOTION_MULTIPLIERS["background"]),
        (mid, MOTION_MULTIPLIERS["midground"]),
        (fg, MOTION_MULTIPLIERS["foreground"]),
    ]

    for layer, mult in layers:
        dx = int(dx_dir * max_dx * mult * eased_t)
        dy = int(dy_dir * max_dy * mult * eased_t)
        canvas = _paste_with_offset(canvas, layer, dx, dy)

    return canvas


def _composite_zoom(
    canvas: Image.Image,
    fg: Image.Image,
    mid: Image.Image,
    bg: Image.Image,
    eased_t: float,
    magnitude: float,
    is_zoom_in: bool,
    canvas_size: tuple[int, int],
) -> Image.Image:
    """Composite three layers with differential zoom scaling."""
    cw, ch = canvas_size

    layers = [
        (bg, MOTION_MULTIPLIERS["background"]),
        (mid, MOTION_MULTIPLIERS["midground"]),
        (fg, MOTION_MULTIPLIERS["foreground"]),
    ]

    for layer, mult in layers:
        # Zoom factor: 1.0 at t=0, 1.0 + magnitude*mult at t=1
        zoom = magnitude * mult * eased_t
        if not is_zoom_in:
            zoom = -zoom  # zoom out: shrink
        scale = 1.0 + zoom

        if scale <= 0.01:
            # Avoid degenerate scaling
            canvas.paste(layer, (0, 0), layer)
            continue

        new_w = int(cw * scale)
        new_h = int(ch * scale)
        if new_w < 1 or new_h < 1:
            continue

        scaled = layer.resize((new_w, new_h), Image.LANCZOS)

        # Center on canvas
        paste_x = (cw - new_w) // 2
        paste_y = (ch - new_h) // 2

        # If scaled is larger than canvas, crop to canvas
        if new_w > cw or new_h > ch:
            left = max(0, (new_w - cw) // 2)
            top = max(0, (new_h - ch) // 2)
            cropped = scaled.crop((left, top, left + cw, top + ch))
            canvas.paste(cropped, (0, 0), cropped)
        else:
            canvas.paste(scaled, (paste_x, paste_y), scaled)

    return canvas


def _paste_with_offset(
    canvas: Image.Image,
    layer: Image.Image,
    dx: int,
    dy: int,
) -> Image.Image:
    """Paste a layer onto canvas with a pixel offset, using alpha compositing."""
    canvas.paste(layer, (dx, dy), layer)
    return canvas


# ---------------------------------------------------------------------------
# Frame export
# ---------------------------------------------------------------------------

def save_frames(
    frames: list[Image.Image],
    output_dir: Path,
    prefix: str = "frame_",
) -> list[Path]:
    """
    Save a list of PIL frames as numbered PNGs.

    Parameters
    ----------
    frames : list[PIL.Image.Image]
        Frames to save.
    output_dir : Path
        Directory to write frames into (created if missing).
    prefix : str
        Filename prefix (default ``"frame_"``).

    Returns
    -------
    list[Path]
        Paths to the saved frame files.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    pad = len(str(len(frames)))
    paths: list[Path] = []

    for i, frame in enumerate(frames):
        filename = f"{prefix}{str(i).zfill(pad)}.png"
        path = output_dir / filename
        # Convert RGBA to RGB for PNG compatibility with ffmpeg
        if frame.mode == "RGBA":
            rgb = Image.new("RGB", frame.size, (0, 0, 0))
            rgb.paste(frame, mask=frame.split()[3])
            rgb.save(path)
        else:
            frame.save(path)
        paths.append(path)

    logger.info("Saved %d frames to %s", len(paths), output_dir)
    return paths
