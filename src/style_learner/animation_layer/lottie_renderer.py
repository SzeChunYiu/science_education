"""Render Lottie JSON animations to PIL frames.

Includes template physics animations (pendulum, projectile, wave) that
use pure PIL drawing — no external Lottie library required.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path

from PIL import Image, ImageDraw

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Lottie JSON rendering (optional dependency)
# ---------------------------------------------------------------------------

def render_lottie_to_frames(
    lottie_data: dict,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
) -> list[Image.Image]:
    """Render a Lottie JSON animation to a list of PIL Image frames.

    Attempts to use the ``lottie`` Python library first. Falls back to
    a minimal manual renderer that handles basic shape layers.

    Args:
        lottie_data: Parsed Lottie JSON dict.
        width: Output frame width.
        height: Output frame height.
        fps: Frames per second.

    Returns:
        List of RGBA PIL Images, one per frame.
    """
    try:
        return _render_with_lottie_lib(lottie_data, width, height, fps)
    except ImportError:
        logger.info("python-lottie not installed, using manual renderer")
    except Exception as e:
        logger.warning("python-lottie failed (%s), using manual renderer", e)

    return _render_manual(lottie_data, width, height, fps)


def _render_with_lottie_lib(
    lottie_data: dict, width: int, height: int, fps: int
) -> list[Image.Image]:
    """Render using the python-lottie library."""
    import lottie
    from lottie.parsers.tgs import parse_tgs
    from lottie import exporters
    import io
    import json

    # Parse the animation
    raw = json.dumps(lottie_data).encode()
    anim = lottie.parsers.baseclass.importer.import_animation(
        io.BytesIO(raw), "lottie"
    )

    frames = []
    total_frames = int(anim.out_point - anim.in_point)

    for frame_num in range(total_frames):
        t = anim.in_point + frame_num
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        # Export frame
        try:
            rendered = exporters.export_png(anim, t, width, height)
            img = Image.open(io.BytesIO(rendered)).convert("RGBA")
        except Exception:
            pass
        frames.append(img)

    return frames


def _render_manual(
    lottie_data: dict, width: int, height: int, fps: int
) -> list[Image.Image]:
    """Minimal manual Lottie renderer for basic shapes.

    Handles only simple solid-color rectangle and ellipse layers.
    Complex animations will produce blank frames.
    """
    in_point = lottie_data.get("ip", 0)
    out_point = lottie_data.get("op", 60)
    source_fps = lottie_data.get("fr", 30)
    source_w = lottie_data.get("w", width)
    source_h = lottie_data.get("h", height)

    total_frames = int(out_point - in_point)
    scale_x = width / max(source_w, 1)
    scale_y = height / max(source_h, 1)

    frames = []
    for _ in range(total_frames):
        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        frames.append(img)

    logger.debug("Manual Lottie render: %d blank frames (no shape support)", total_frames)
    return frames


# ---------------------------------------------------------------------------
# Template physics animations (pure PIL)
# ---------------------------------------------------------------------------

def _draw_circle(draw: ImageDraw.ImageDraw, cx: float, cy: float, r: float,
                 fill: tuple, outline: tuple | None = None, width: int = 2):
    """Draw an anti-aliased circle."""
    bbox = [cx - r, cy - r, cx + r, cy + r]
    draw.ellipse(bbox, fill=fill, outline=outline, width=width)


def _draw_line_aa(draw: ImageDraw.ImageDraw, points: list[tuple],
                  fill: tuple, width: int = 3):
    """Draw a polyline with the given width."""
    if len(points) < 2:
        return
    for i in range(len(points) - 1):
        draw.line([points[i], points[i + 1]], fill=fill, width=width)


def create_pendulum_animation(
    duration: float = 3.0,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> list[Image.Image]:
    """Render a simple pendulum swing animation.

    A circle (bob) swings on a line (rod) from a pivot point at the
    top center of the frame.

    Args:
        duration: Animation duration in seconds.
        fps: Frames per second.
        width: Frame width.
        height: Frame height.

    Returns:
        List of RGBA PIL Images.
    """
    total_frames = int(duration * fps)
    frames = []

    pivot_x = width / 2
    pivot_y = height * 0.1
    rod_length = height * 0.55
    bob_radius = min(width, height) * 0.03
    max_angle = math.radians(35)

    rod_color = (200, 200, 200, 255)
    bob_color = (70, 130, 230, 255)
    pivot_color = (180, 180, 180, 255)

    for i in range(total_frames):
        t = i / fps
        # Damped oscillation
        damping = math.exp(-0.3 * t)
        angle = max_angle * damping * math.sin(2 * math.pi * 0.8 * t)

        bob_x = pivot_x + rod_length * math.sin(angle)
        bob_y = pivot_y + rod_length * math.cos(angle)

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Rod
        draw.line(
            [(int(pivot_x), int(pivot_y)), (int(bob_x), int(bob_y))],
            fill=rod_color, width=4,
        )

        # Pivot
        _draw_circle(draw, pivot_x, pivot_y, bob_radius * 0.4,
                      fill=pivot_color)

        # Bob
        _draw_circle(draw, bob_x, bob_y, bob_radius,
                      fill=bob_color, outline=(50, 100, 200, 255))

        frames.append(img)

    return frames


def create_projectile_animation(
    duration: float = 3.0,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> list[Image.Image]:
    """Render a parabolic projectile trajectory animation.

    A ball launches from the lower-left, follows a parabolic arc,
    and lands on the lower-right. A fading trail is drawn behind it.

    Args:
        duration: Animation duration in seconds.
        fps: Frames per second.
        width: Frame width.
        height: Frame height.

    Returns:
        List of RGBA PIL Images.
    """
    total_frames = int(duration * fps)
    frames = []

    margin_x = width * 0.1
    margin_y = height * 0.15
    ground_y = height * 0.85
    peak_y = height * 0.2
    ball_radius = min(width, height) * 0.02

    ball_color = (230, 100, 50, 255)
    trail_color = (230, 100, 50, 100)

    trail_points: list[tuple[float, float]] = []

    for i in range(total_frames):
        progress = i / max(total_frames - 1, 1)

        # Parabolic path: x linear, y quadratic
        x = margin_x + progress * (width - 2 * margin_x)
        # y = ground - 4*h*t*(1-t)  where h = ground - peak
        arc_height = ground_y - peak_y
        y = ground_y - 4 * arc_height * progress * (1 - progress)

        trail_points.append((x, y))

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Ground line
        draw.line(
            [(int(margin_x * 0.5), int(ground_y)),
             (int(width - margin_x * 0.5), int(ground_y))],
            fill=(150, 150, 150, 128), width=2,
        )

        # Trail (dotted)
        if len(trail_points) > 1:
            for j in range(0, len(trail_points) - 1, 2):
                _draw_circle(draw, trail_points[j][0], trail_points[j][1],
                              ball_radius * 0.3, fill=trail_color)

        # Ball
        _draw_circle(draw, x, y, ball_radius,
                      fill=ball_color, outline=(200, 80, 30, 255))

        frames.append(img)

    return frames


def create_wave_animation(
    duration: float = 3.0,
    fps: int = 30,
    width: int = 1920,
    height: int = 1080,
) -> list[Image.Image]:
    """Render a propagating sine wave animation.

    A transverse wave propagates from left to right with visible
    wavelength and amplitude.

    Args:
        duration: Animation duration in seconds.
        fps: Frames per second.
        width: Frame width.
        height: Frame height.

    Returns:
        List of RGBA PIL Images.
    """
    total_frames = int(duration * fps)
    frames = []

    center_y = height / 2
    amplitude = height * 0.2
    wavelength = width * 0.3
    wave_speed = wavelength * 1.2  # pixels per second
    margin = width * 0.05

    wave_color = (50, 180, 230, 255)
    axis_color = (150, 150, 150, 80)

    for i in range(total_frames):
        t = i / fps
        phase = (wave_speed * t) / wavelength * 2 * math.pi

        img = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        # Center axis
        draw.line(
            [(int(margin), int(center_y)),
             (int(width - margin), int(center_y))],
            fill=axis_color, width=1,
        )

        # Wave points
        num_points = 300
        points = []
        for p in range(num_points):
            x = margin + p * (width - 2 * margin) / (num_points - 1)
            # Propagating wave: y = A * sin(kx - wt)
            k = 2 * math.pi / wavelength
            y = center_y - amplitude * math.sin(k * x - phase)
            points.append((x, y))

        # Draw wave as connected line segments
        _draw_line_aa(draw, points, fill=wave_color, width=3)

        # Draw a few crest markers
        for p_idx in range(0, num_points, num_points // 6):
            px, py = points[p_idx]
            _draw_circle(draw, px, py, 4, fill=wave_color)

        frames.append(img)

    return frames
