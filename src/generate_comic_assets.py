#!/usr/bin/env python3
"""
B&W Comic Line Art Asset Generator
===================================
Generates all visual assets for the physics education video series.

Art style: Black ink line drawings on white/cream, inspired by
Frank Rodgers' "Cartoon Art School". Simple cartoon characters,
comic effects, minimal backgrounds.

Replaces the previous colorful board-book style assets.

Usage:
    python3 src/generate_comic_assets.py
"""

import math
import os
import random
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ─── Style Constants ──────────────────────────────────────────────
INK = "#1A1A1A"
INK2 = "#222222"
CREAM = "#FAFAFA"
TRANSPARENT = (0, 0, 0, 0)

# Line widths
OUTLINE = 4        # Main outlines
DETAIL = 2         # Interior details
FINE = 1           # Fine marks / hatching
THICK = 5          # Heavy outlines

# Canvas sizes
CHAR_SIZE = (512, 768)
OBJ_SIZE = (512, 512)
BG_SIZE = (1920, 1080)
ELEM_SIZE = (512, 512)

# Output root
PROJECT = Path(__file__).resolve().parent.parent
OUTPUT = PROJECT / "data" / "assets" / "physics"

# Reproducible randomness for hand-drawn feel
SEED = 42


# ─── Helpers ──────────────────────────────────────────────────────

def jitter(x, y, amount=2, rng=None):
    """Add slight hand-drawn irregularity to a point."""
    if rng is None:
        return (x, y)
    dx = rng.randint(-amount, amount)
    dy = rng.randint(-amount, amount)
    return (x + dx, y + dy)


def jitter_points(points, amount=2, rng=None):
    """Add jitter to a list of (x, y) points."""
    return [jitter(x, y, amount, rng) for x, y in points]


def draw_wobbly_line(draw, points, fill=INK, width=OUTLINE, jitter_amt=1, rng=None):
    """Draw a line with slight wobble for hand-drawn feel."""
    if rng and jitter_amt > 0:
        points = jitter_points(points, jitter_amt, rng)
    draw.line(points, fill=fill, width=width)


def draw_wobbly_ellipse(draw, bbox, outline=INK, width=OUTLINE, fill=None):
    """Draw an ellipse (circles, heads, etc.)."""
    draw.ellipse(bbox, outline=outline, width=width, fill=fill)


def draw_thick_line(draw, points, fill=INK, width=OUTLINE):
    """Draw a simple thick line."""
    draw.line(points, fill=fill, width=width)


def draw_circle(draw, cx, cy, r, outline=INK, width=OUTLINE, fill=None):
    """Draw a circle centered at (cx, cy) with radius r."""
    draw.ellipse(
        [cx - r, cy - r, cx + r, cy + r],
        outline=outline, width=width, fill=fill
    )


def draw_dot(draw, cx, cy, r=4, fill=INK):
    """Draw a filled dot (for eyes, etc.)."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill)


def draw_smile(draw, cx, cy, w=20, fill=INK, width=DETAIL):
    """Draw a simple smile arc."""
    draw.arc([cx - w, cy - w // 2, cx + w, cy + w], 0, 180, fill=fill, width=width)


def draw_frown(draw, cx, cy, w=20, fill=INK, width=DETAIL):
    """Draw a simple frown arc."""
    draw.arc([cx - w, cy - w, cx + w, cy], 180, 360, fill=fill, width=width)


def new_transparent(size):
    """Create a new RGBA transparent image."""
    return Image.new("RGBA", size, TRANSPARENT)


def new_cream(size):
    """Create a new image with cream background."""
    return Image.new("RGBA", size, CREAM)


def save_asset(img, category, name):
    """Save an asset to the correct output directory."""
    out_dir = OUTPUT / category
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{name}.png"
    img.save(path)
    return path


# ─── Character Drawing Functions ──────────────────────────────────

def _draw_base_body(draw, cx=256, head_y=160, head_rx=70, head_ry=80,
                    body_top=240, body_bottom=580, shoulder_w=80,
                    hip_w=50, rng=None):
    """Draw a basic character body outline. Returns key points."""
    # Head
    draw_wobbly_ellipse(draw,
                        [cx - head_rx, head_y - head_ry, cx + head_rx, head_y + head_ry],
                        width=OUTLINE)

    # Neck
    draw_thick_line(draw, [(cx - 10, head_y + head_ry - 5),
                           (cx - 10, body_top),
                           (cx + 10, body_top),
                           (cx + 10, head_y + head_ry - 5)], width=DETAIL)

    # Body (trapezoid)
    body_pts = [
        (cx - shoulder_w, body_top),
        (cx + shoulder_w, body_top),
        (cx + hip_w, body_bottom),
        (cx - hip_w, body_bottom),
        (cx - shoulder_w, body_top),
    ]
    draw.line(body_pts, fill=INK, width=OUTLINE)

    # Arms
    draw_thick_line(draw, [(cx - shoulder_w, body_top + 20),
                           (cx - shoulder_w - 50, body_top + 140),
                           (cx - shoulder_w - 40, body_top + 150)], width=OUTLINE)
    draw_thick_line(draw, [(cx + shoulder_w, body_top + 20),
                           (cx + shoulder_w + 50, body_top + 140),
                           (cx + shoulder_w + 40, body_top + 150)], width=OUTLINE)

    # Legs
    draw_thick_line(draw, [(cx - hip_w + 10, body_bottom),
                           (cx - hip_w, body_bottom + 120),
                           (cx - hip_w - 15, body_bottom + 130)], width=OUTLINE)
    draw_thick_line(draw, [(cx + hip_w - 10, body_bottom),
                           (cx + hip_w, body_bottom + 120),
                           (cx + hip_w + 15, body_bottom + 130)], width=OUTLINE)

    # Shoes (simple ovals)
    draw_wobbly_ellipse(draw,
                        [cx - hip_w - 30, body_bottom + 120,
                         cx - hip_w + 10, body_bottom + 145], width=DETAIL)
    draw_wobbly_ellipse(draw,
                        [cx + hip_w - 10, body_bottom + 120,
                         cx + hip_w + 30, body_bottom + 145], width=DETAIL)

    return {
        "head_center": (cx, head_y),
        "head_rx": head_rx, "head_ry": head_ry,
        "body_top": body_top, "body_bottom": body_bottom,
        "cx": cx,
    }


def _draw_eyes(draw, cx, ey, spacing=25, r=5):
    """Draw simple dot eyes."""
    draw_dot(draw, cx - spacing, ey, r=r)
    draw_dot(draw, cx + spacing, ey, r=r)


def _draw_round_glasses(draw, cx, ey, spacing=25, r=18, width=DETAIL):
    """Draw round spectacles."""
    draw_circle(draw, cx - spacing, ey, r, width=width)
    draw_circle(draw, cx + spacing, ey, r, width=width)
    # Bridge
    draw.line([(cx - spacing + r, ey), (cx + spacing - r, ey)],
              fill=INK, width=FINE)
    # Temples (going to ears)
    draw.line([(cx - spacing - r, ey), (cx - spacing - r - 15, ey - 5)],
              fill=INK, width=FINE)
    draw.line([(cx + spacing + r, ey), (cx + spacing + r + 15, ey - 5)],
              fill=INK, width=FINE)


def _draw_mustache(draw, cx, my, w=30, fill=INK, width=DETAIL):
    """Draw a simple mustache."""
    draw.arc([cx - w, my - 8, cx, my + 12], 200, 340, fill=fill, width=width)
    draw.arc([cx, my - 8, cx + w, my + 12], 200, 340, fill=fill, width=width)


def _draw_beard_short(draw, cx, chin_y, w=40, h=30, fill=INK, width=DETAIL):
    """Draw a short curly beard with small arcs."""
    for i in range(5):
        x = cx - w + i * (2 * w // 4)
        draw.arc([x - 10, chin_y - 5, x + 10, chin_y + h],
                 0, 180, fill=fill, width=width)


def _draw_beard_thick(draw, cx, chin_y, w=50, h=50, fill=INK, width=OUTLINE):
    """Draw a thick bushy beard."""
    pts = []
    for i in range(9):
        angle = math.pi * i / 8
        x = cx + int(w * math.cos(math.pi - angle))
        y = chin_y + int(h * math.sin(angle))
        pts.append((x, y))
    # Wavy bottom
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=fill, width=width)
    # Fill lines
    for i in range(3):
        y = chin_y + 10 + i * 12
        draw.arc([cx - w + 10, y - 8, cx + w - 10, y + 8],
                 0, 180, fill=fill, width=FINE)


def _draw_pointed_beard(draw, cx, chin_y, w=25, h=40, fill=INK, width=DETAIL):
    """Draw a pointed goatee-style beard."""
    draw.polygon([(cx - w, chin_y), (cx, chin_y + h), (cx + w, chin_y)],
                 outline=fill)
    # A few lines for texture
    draw.line([(cx - 10, chin_y + 5), (cx, chin_y + h - 5)], fill=fill, width=FINE)
    draw.line([(cx + 10, chin_y + 5), (cx, chin_y + h - 5)], fill=fill, width=FINE)


def _draw_curly_wig(draw, cx, top_y, rx=90, ry=70, fill=INK, width=OUTLINE):
    """Draw a big curly wig (Newton, etc.) with cloud-like bumps."""
    # Cloud bumps around the head
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        bx = cx + int(rx * math.cos(angle))
        by = top_y + int(ry * math.sin(angle))
        r = 20 + (angle_deg % 60) // 30 * 8
        draw_circle(draw, bx, by, r, outline=fill, width=width)


def _draw_baroque_wig(draw, cx, top_y, rx=95, ry=80, fill=INK, width=OUTLINE):
    """Draw a large baroque wig with voluminous curls (Leibniz)."""
    # Larger, more voluminous than curly wig
    for angle_deg in range(0, 360, 25):
        angle = math.radians(angle_deg)
        bx = cx + int(rx * math.cos(angle))
        by = top_y + int(ry * math.sin(angle))
        r = 22 + (angle_deg % 50) // 25 * 10
        draw_circle(draw, bx, by, r, outline=fill, width=width)
    # Extra curls hanging down sides
    for side in [-1, 1]:
        for i in range(4):
            y = top_y + 40 + i * 25
            x = cx + side * (rx - 10)
            draw.arc([x - 15, y - 10, x + 15, y + 10],
                     0 if side > 0 else 180, 180 if side > 0 else 360,
                     fill=fill, width=DETAIL)


def _draw_18c_wig(draw, cx, top_y, rx=80, ry=60, fill=INK, width=OUTLINE):
    """Draw a smooth 18th-century wig (Euler)."""
    # Smooth dome on top
    draw.arc([cx - rx, top_y - ry, cx + rx, top_y + ry // 2],
             180, 360, fill=fill, width=width)
    # Rolled sides
    for side in [-1, 1]:
        x = cx + side * (rx - 15)
        draw.arc([x - 20, top_y + 10, x + 20, top_y + 70],
                 0 if side > 0 else 180, 180 if side > 0 else 360,
                 fill=fill, width=width)
    # Tied back (ribbon)
    draw.line([(cx + 40, top_y + 30), (cx + 60, top_y + 50)],
              fill=fill, width=DETAIL)


def _draw_wild_hair(draw, cx, top_y, fill=INK, width=OUTLINE):
    """Draw wild spiky hair radiating out (Einstein)."""
    for angle_deg in range(-150, -30, 12):
        angle = math.radians(angle_deg)
        length = 60 + (hash(angle_deg) % 30)
        x1 = cx + int(60 * math.cos(angle))
        y1 = top_y + int(50 * math.sin(angle))
        x2 = cx + int(length * math.cos(angle))
        y2 = top_y + int(length * math.sin(angle)) - 20
        draw.line([(x1, y1), (x2, y2)], fill=fill, width=width)


def _draw_bun_hair(draw, cx, top_y, fill=INK, width=OUTLINE):
    """Draw hair pulled back into a bun (Noether)."""
    # Hair on head
    draw.arc([cx - 70, top_y - 60, cx + 70, top_y + 20],
             180, 360, fill=fill, width=width)
    # Bun circle at back
    draw_circle(draw, cx + 50, top_y - 20, 25, outline=fill, width=width)
    # Lines in bun
    draw.line([(cx + 35, top_y - 30), (cx + 65, top_y - 10)],
              fill=fill, width=FINE)
    draw.line([(cx + 40, top_y - 15), (cx + 60, top_y - 25)],
              fill=fill, width=FINE)


def _draw_wide_brim_hat(draw, cx, top_y, fill=INK, width=OUTLINE):
    """Draw a wide-brim hat (Descartes)."""
    # Brim
    draw.ellipse([cx - 90, top_y - 50, cx + 90, top_y - 20],
                 outline=fill, width=width)
    # Crown
    draw.rectangle([cx - 45, top_y - 100, cx + 45, top_y - 40],
                   outline=fill, width=width)
    # Top
    draw.line([(cx - 45, top_y - 100), (cx + 45, top_y - 100)],
              fill=fill, width=width)


def _draw_shoulder_hair(draw, cx, top_y, fill=INK, width=DETAIL):
    """Draw shoulder-length hair (Descartes, etc.)."""
    for side in [-1, 1]:
        x = cx + side * 55
        for i in range(5):
            y = top_y + 10 + i * 20
            draw.arc([x - 15, y, x + 15, y + 20],
                     0 if side > 0 else 180, 180 if side > 0 else 360,
                     fill=fill, width=width)


def _draw_wavy_hair(draw, cx, top_y, fill=INK, width=OUTLINE):
    """Draw wavy hair swept to side (Faraday, Feynman)."""
    draw.arc([cx - 65, top_y - 70, cx + 65, top_y],
             180, 360, fill=fill, width=width)
    # Waves
    for i in range(3):
        x = cx - 40 + i * 30
        draw.arc([x, top_y - 60, x + 30, top_y - 30],
                 180, 360, fill=fill, width=DETAIL)


def _draw_neat_hair(draw, cx, top_y, fill=INK, width=OUTLINE):
    """Draw neat parted hair."""
    draw.arc([cx - 65, top_y - 65, cx + 65, top_y],
             180, 360, fill=fill, width=width)
    # Part line
    draw.line([(cx - 20, top_y - 65), (cx - 15, top_y - 30)],
              fill=fill, width=DETAIL)


def _draw_receding_hair(draw, cx, top_y, fill=INK, width=OUTLINE):
    """Draw receding hairline."""
    draw.arc([cx - 65, top_y - 50, cx + 65, top_y + 10],
             200, 340, fill=fill, width=width)
    # Side hair
    draw.arc([cx - 70, top_y - 30, cx - 30, top_y + 10],
             90, 270, fill=fill, width=DETAIL)
    draw.arc([cx + 30, top_y - 30, cx + 70, top_y + 10],
             270, 90, fill=fill, width=DETAIL)


def _draw_bald_top(draw, cx, top_y, fill=INK, width=DETAIL):
    """Draw a bald top with side hair (Galileo, Planck)."""
    # Just side tufts
    draw.arc([cx - 75, top_y - 20, cx - 35, top_y + 20],
             90, 270, fill=fill, width=width)
    draw.arc([cx + 35, top_y - 20, cx + 75, top_y + 20],
             270, 90, fill=fill, width=width)


def _draw_renaissance_collar(draw, cx, collar_y, fill=INK, width=DETAIL):
    """Draw a renaissance ruff collar."""
    for i in range(8):
        angle = math.pi * i / 7
        x = cx + int(60 * math.cos(angle - math.pi / 2))
        y = collar_y + int(20 * math.sin(angle - math.pi / 2)) + 15
        draw.arc([x - 12, y - 8, x + 12, y + 8],
                 0, 360, fill=fill, width=width)


def _draw_ruff_collar(draw, cx, collar_y, fill=INK, width=DETAIL):
    """Draw an Elizabethan-style ruff collar."""
    for i in range(10):
        angle = math.pi * i / 9
        x = cx + int(70 * math.cos(angle - math.pi / 2))
        y = collar_y + int(25 * math.sin(angle - math.pi / 2)) + 10
        draw.arc([x - 10, y - 6, x + 10, y + 6],
                 0, 360, fill=fill, width=width)


def _draw_toga(draw, cx, body_top, body_bottom, fill=INK, width=OUTLINE):
    """Draw toga/robe drape lines over the body."""
    # Diagonal drape
    draw.line([(cx + 60, body_top), (cx - 40, body_top + 100)],
              fill=fill, width=DETAIL)
    draw.line([(cx - 40, body_top + 100), (cx - 50, body_bottom)],
              fill=fill, width=DETAIL)
    # Fold lines
    draw.line([(cx + 20, body_top + 50), (cx - 10, body_top + 150)],
              fill=fill, width=FINE)
    draw.line([(cx + 40, body_top + 30), (cx + 10, body_top + 130)],
              fill=fill, width=FINE)


def _draw_byzantine_robe(draw, cx, body_top, body_bottom, fill=INK, width=DETAIL):
    """Draw Byzantine-style robe with decorative bands."""
    # Vertical center line
    draw.line([(cx, body_top), (cx, body_bottom)], fill=fill, width=width)
    # Decorative band at chest
    draw.line([(cx - 60, body_top + 40), (cx + 60, body_top + 40)],
              fill=fill, width=width)
    # Cross pattern on chest
    draw.line([(cx - 15, body_top + 20), (cx + 15, body_top + 20)],
              fill=fill, width=FINE)
    draw.line([(cx, body_top + 5), (cx, body_top + 35)],
              fill=fill, width=FINE)


def _draw_monk_robe(draw, cx, body_top, body_bottom, fill=INK, width=DETAIL):
    """Draw medieval monk robe with hood suggestion and rope belt."""
    # Hood drape at neck
    draw.arc([cx - 40, body_top - 30, cx + 40, body_top + 20],
             0, 180, fill=fill, width=width)
    # Rope belt
    draw.line([(cx - 50, body_top + 120), (cx + 50, body_top + 120)],
              fill=fill, width=width)
    # Hanging rope end
    draw.line([(cx + 30, body_top + 120), (cx + 25, body_top + 170)],
              fill=fill, width=FINE)
    draw_circle(draw, cx + 25, body_top + 175, 5, width=FINE)


def _draw_tonsure(draw, cx, top_y, fill=INK, width=DETAIL):
    """Draw tonsure haircut (bald circle on top, ring of hair)."""
    # Ring of hair around sides
    draw.arc([cx - 70, top_y - 40, cx + 70, top_y + 30],
             180, 360, fill=fill, width=width)
    # Bald spot on top (a lighter circle)
    draw_circle(draw, cx, top_y - 40, 25, outline=fill, width=FINE)


def _draw_tied_back_hair(draw, cx, top_y, fill=INK, width=OUTLINE):
    """Draw hair tied back neatly (Lagrange)."""
    draw.arc([cx - 65, top_y - 65, cx + 65, top_y],
             180, 360, fill=fill, width=width)
    # Ponytail suggestion at back
    draw.line([(cx + 50, top_y - 20), (cx + 70, top_y + 10),
               (cx + 65, top_y + 40)], fill=fill, width=DETAIL)
    # Ribbon
    draw.line([(cx + 65, top_y + 10), (cx + 80, top_y + 5)],
              fill=fill, width=DETAIL)
    draw.line([(cx + 65, top_y + 10), (cx + 80, top_y + 20)],
              fill=fill, width=DETAIL)


def _draw_formal_coat(draw, cx, body_top, body_bottom, fill=INK, width=DETAIL):
    """Draw formal coat details — buttons, lapels."""
    # Center line
    draw.line([(cx, body_top), (cx, body_bottom)], fill=fill, width=width)
    # Buttons
    for i in range(4):
        y = body_top + 40 + i * 50
        draw_dot(draw, cx, y, r=4, fill=fill)
    # Lapels
    draw.line([(cx - 10, body_top), (cx - 40, body_top + 60)],
              fill=fill, width=width)
    draw.line([(cx + 10, body_top), (cx + 40, body_top + 60)],
              fill=fill, width=width)


def _draw_19c_coat(draw, cx, body_top, body_bottom, fill=INK, width=DETAIL):
    """Draw 19th century coat — high collar, fitted."""
    # High collar
    draw.line([(cx - 30, body_top - 10), (cx - 20, body_top + 20)],
              fill=fill, width=width)
    draw.line([(cx + 30, body_top - 10), (cx + 20, body_top + 20)],
              fill=fill, width=width)
    # Center buttons
    draw.line([(cx, body_top + 10), (cx, body_bottom)], fill=fill, width=FINE)
    for i in range(5):
        y = body_top + 30 + i * 40
        draw_dot(draw, cx, y, r=3, fill=fill)


# ─── Individual Character Generators ─────────────────────────────

def gen_char_newton():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(1)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_curly_wig(draw, cx, head_y - 20)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 20)
    _draw_formal_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_aristotle():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(2)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 70)
    _draw_eyes(draw, cx, head_y - 10)
    _draw_beard_short(draw, cx, head_y + 50, w=35, h=25)
    draw_smile(draw, cx, head_y + 20, w=15)
    _draw_toga(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_galileo():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(3)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_bald_top(draw, cx, head_y - 50)
    _draw_pointed_beard(draw, cx, head_y + 50, w=20, h=35)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 15, w=15)
    _draw_renaissance_collar(draw, cx, head_y + 60)
    _draw_formal_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_einstein():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(4)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_wild_hair(draw, cx, head_y - 40)
    _draw_eyes(draw, cx, head_y - 10, r=6)
    _draw_mustache(draw, cx, head_y + 20, w=35)
    draw_smile(draw, cx, head_y + 35, w=25)
    return img


def gen_char_euler():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(5)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_18c_wig(draw, cx, head_y - 40)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 20, w=18)
    _draw_formal_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_kepler():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(6)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, head_rx=65, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 65)
    _draw_eyes(draw, cx, head_y - 10)
    # Sharp nose
    draw.line([(cx, head_y - 5), (cx - 8, head_y + 12), (cx + 5, head_y + 12)],
              fill=INK, width=DETAIL)
    _draw_beard_short(draw, cx, head_y + 45, w=30, h=20)
    _draw_ruff_collar(draw, cx, head_y + 60)
    _draw_formal_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_lagrange():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(7)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_tied_back_hair(draw, cx, head_y - 45)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 20, w=15)
    _draw_formal_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_hamilton():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(8)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 65)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 20, w=15)
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_noether():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(9)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, shoulder_w=70, rng=rng)
    _draw_bun_hair(draw, cx, head_y - 40)
    _draw_round_glasses(draw, cx, head_y - 10, r=16)
    # Dot eyes inside glasses
    draw_dot(draw, cx - 25, head_y - 10, r=4)
    draw_dot(draw, cx + 25, head_y - 10, r=4)
    draw_smile(draw, cx, head_y + 20, w=15)
    return img


def gen_char_descartes():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(10)
    cx, head_y = 256, 190
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_wide_brim_hat(draw, cx, head_y - 55)
    _draw_shoulder_hair(draw, cx, head_y - 30)
    _draw_eyes(draw, cx, head_y - 10)
    _draw_mustache(draw, cx, head_y + 18, w=25)
    draw_smile(draw, cx, head_y + 30, w=12)
    _draw_formal_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_leibniz():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(11)
    cx, head_y = 256, 190
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_baroque_wig(draw, cx, head_y - 20)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 20, w=15)
    _draw_formal_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_maxwell():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(12)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 65)
    _draw_eyes(draw, cx, head_y - 10)
    _draw_beard_thick(draw, cx, head_y + 40, w=45, h=45)
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_faraday():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(13)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_wavy_hair(draw, cx, head_y - 40)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 20, w=20)  # Kind expression
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_boltzmann():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(14)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 65)
    _draw_round_glasses(draw, cx, head_y - 10, r=18)
    draw_dot(draw, cx - 25, head_y - 10, r=4)
    draw_dot(draw, cx + 25, head_y - 10, r=4)
    _draw_beard_thick(draw, cx, head_y + 40, w=50, h=50)
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_planck():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(15)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_bald_top(draw, cx, head_y - 50)
    _draw_round_glasses(draw, cx, head_y - 10, r=16)
    draw_dot(draw, cx - 25, head_y - 10, r=4)
    draw_dot(draw, cx + 25, head_y - 10, r=4)
    _draw_mustache(draw, cx, head_y + 18, w=30)
    draw_smile(draw, cx, head_y + 30, w=12)
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_bohr():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(16)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 65)
    _draw_eyes(draw, cx, head_y - 10, r=5)
    draw_smile(draw, cx, head_y + 20, w=22)  # Friendly smile
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_schrodinger():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(17)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_receding_hair(draw, cx, head_y - 45)
    _draw_round_glasses(draw, cx, head_y - 10, r=16)
    draw_dot(draw, cx - 25, head_y - 10, r=4)
    draw_dot(draw, cx + 25, head_y - 10, r=4)
    # Thin mustache
    draw.line([(cx - 20, head_y + 18), (cx - 5, head_y + 22)],
              fill=INK, width=DETAIL)
    draw.line([(cx + 5, head_y + 22), (cx + 20, head_y + 18)],
              fill=INK, width=DETAIL)
    draw_smile(draw, cx, head_y + 30, w=12)
    return img


def gen_char_dirac():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(18)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, head_rx=60, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 60)
    _draw_eyes(draw, cx, head_y - 10, r=4)  # Smaller, serious eyes
    # Neutral expression (straight line)
    draw.line([(cx - 12, head_y + 22), (cx + 12, head_y + 22)],
              fill=INK, width=DETAIL)
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_feynman():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(19)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_wavy_hair(draw, cx, head_y - 40)
    _draw_eyes(draw, cx, head_y - 10, r=5)
    # Mischievous grin — asymmetric smile
    draw.arc([cx - 25, head_y + 10, cx + 25, head_y + 35],
             0, 180, fill=INK, width=DETAIL)
    # Raised eyebrow
    draw.arc([cx + 10, head_y - 30, cx + 45, head_y - 15],
             180, 360, fill=INK, width=DETAIL)
    draw.arc([cx - 45, head_y - 25, cx - 10, head_y - 15],
             180, 360, fill=INK, width=FINE)
    return img


def gen_char_heisenberg():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(20)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 65)
    _draw_round_glasses(draw, cx, head_y - 10, r=16)
    draw_dot(draw, cx - 25, head_y - 10, r=4)
    draw_dot(draw, cx + 25, head_y - 10, r=4)
    draw_smile(draw, cx, head_y + 20, w=15)
    _draw_19c_coat(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_philoponus():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(21)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_neat_hair(draw, cx, head_y - 65)
    _draw_eyes(draw, cx, head_y - 10)
    _draw_beard_short(draw, cx, head_y + 45, w=30, h=20)
    draw_smile(draw, cx, head_y + 20, w=12)
    _draw_byzantine_robe(draw, cx, info["body_top"], info["body_bottom"])
    return img


def gen_char_buridan():
    img = new_transparent(CHAR_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(22)
    cx, head_y = 256, 180
    info = _draw_base_body(draw, cx=cx, head_y=head_y, rng=rng)
    _draw_tonsure(draw, cx, head_y - 40)
    _draw_eyes(draw, cx, head_y - 10)
    draw_smile(draw, cx, head_y + 20, w=15)
    _draw_monk_robe(draw, cx, info["body_top"], info["body_bottom"])
    return img


# ─── Object Drawing Functions ────────────────────────────────────

def gen_obj_ball_red():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    r = 100
    draw_circle(draw, cx, cy, r, width=OUTLINE)
    # Cross-hatch
    for i in range(-80, 81, 25):
        x1 = cx + i
        # Vertical lines clipped to circle
        h = int(math.sqrt(max(0, r * r - i * i)))
        draw.line([(x1, cy - h), (x1, cy + h)], fill=INK, width=FINE)
    for i in range(-80, 81, 25):
        y1 = cy + i
        w = int(math.sqrt(max(0, r * r - i * i)))
        draw.line([(cx - w, y1), (cx + w, y1)], fill=INK, width=FINE)
    return img


def gen_obj_ramp_wood():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Triangle ramp
    pts = [(80, 400), (430, 400), (80, 180)]
    draw.polygon(pts, outline=INK)
    draw.line(pts + [pts[0]], fill=INK, width=OUTLINE)
    # Wood grain lines
    for i in range(4):
        y = 220 + i * 50
        x_end = 80 + (430 - 80) * (400 - y) // (400 - 180)
        draw.line([(85, y), (x_end, y)], fill=INK, width=FINE)
    return img


def gen_obj_pendulum():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Pivot
    draw.line([(200, 60), (312, 60)], fill=INK, width=OUTLINE)
    # Rod
    draw.line([(256, 60), (300, 380)], fill=INK, width=DETAIL)
    # Bob
    draw_circle(draw, 300, 380, 50, width=OUTLINE)
    # Motion arc (dashed suggestion)
    draw.arc([100, 200, 412, 500], 220, 280, fill=INK, width=FINE)
    return img


def gen_obj_spring():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Zigzag spring
    x_left, x_right = 180, 330
    y_start = 80
    coils = 8
    coil_h = 40
    # Top mount
    draw.line([(256, 60), (256, y_start)], fill=INK, width=OUTLINE)
    for i in range(coils):
        y = y_start + i * coil_h
        if i % 2 == 0:
            draw.line([(x_left, y), (x_right, y + coil_h)], fill=INK, width=OUTLINE)
        else:
            draw.line([(x_right, y), (x_left, y + coil_h)], fill=INK, width=OUTLINE)
    # Weight at bottom
    y_bottom = y_start + coils * coil_h
    draw.rectangle([220, y_bottom, 292, y_bottom + 50], outline=INK, width=OUTLINE)
    return img


def gen_obj_arrow_right():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Thick arrow
    draw.polygon([(80, 230), (330, 230), (330, 180), (430, 256),
                   (330, 332), (330, 282), (80, 282)], outline=INK)
    draw.line([(80, 230), (330, 230), (330, 180), (430, 256),
               (330, 332), (330, 282), (80, 282), (80, 230)],
              fill=INK, width=OUTLINE)
    return img


def gen_obj_telescope():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Tube (cylinder)
    draw.line([(150, 180), (400, 130)], fill=INK, width=OUTLINE)
    draw.line([(150, 220), (400, 170)], fill=INK, width=OUTLINE)
    # Front lens
    draw.ellipse([390, 125, 420, 175], outline=INK, width=DETAIL)
    # Eyepiece
    draw.ellipse([140, 175, 165, 225], outline=INK, width=DETAIL)
    # Tripod legs
    draw.line([(256, 200), (180, 420)], fill=INK, width=OUTLINE)
    draw.line([(256, 200), (340, 420)], fill=INK, width=OUTLINE)
    draw.line([(256, 200), (256, 430)], fill=INK, width=OUTLINE)
    return img


def gen_obj_book_open():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Spine
    draw.line([(256, 120), (256, 400)], fill=INK, width=OUTLINE)
    # Left page
    draw.line([(256, 120), (80, 150), (80, 380), (256, 400)],
              fill=INK, width=OUTLINE)
    # Right page
    draw.line([(256, 120), (432, 150), (432, 380), (256, 400)],
              fill=INK, width=OUTLINE)
    # Text lines on left
    for i in range(6):
        y = 180 + i * 30
        draw.line([(120, y), (230, y)], fill=INK, width=FINE)
    # Text lines on right
    for i in range(6):
        y = 180 + i * 30
        draw.line([(282, y), (400, y)], fill=INK, width=FINE)
    return img


def gen_obj_scroll():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Main body
    draw.rectangle([150, 120, 362, 400], outline=INK, width=OUTLINE)
    # Top roll
    draw.ellipse([140, 100, 372, 140], outline=INK, width=OUTLINE)
    # Bottom roll
    draw.ellipse([140, 380, 372, 420], outline=INK, width=OUTLINE)
    # Text lines
    for i in range(7):
        y = 160 + i * 30
        w = 60 + (i % 3) * 20
        draw.line([(180, y), (180 + w, y)], fill=INK, width=FINE)
    return img


def gen_obj_apple_green():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 280
    # Apple body
    draw_circle(draw, cx, cy, 100, width=OUTLINE)
    # Stem
    draw.line([(cx, cy - 100), (cx + 5, cy - 140)], fill=INK, width=DETAIL)
    # Leaf
    draw.ellipse([cx + 5, cy - 150, cx + 50, cy - 120], outline=INK, width=DETAIL)
    draw.line([(cx + 10, cy - 135), (cx + 45, cy - 135)], fill=INK, width=FINE)
    # Highlight arc
    draw.arc([cx - 60, cy - 60, cx - 20, cy + 20], 150, 300, fill=INK, width=FINE)
    return img


def gen_obj_magnet():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # U-shape magnet
    draw.arc([156, 150, 356, 380], 0, 180, fill=INK, width=THICK)
    # Left pole
    draw.line([(156, 265), (156, 150)], fill=INK, width=THICK)
    # Right pole
    draw.line([(356, 265), (356, 150)], fill=INK, width=THICK)
    # N and S labels
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((140, 110), "N", fill=INK, font=font, anchor="mm")
    draw.text((370, 110), "S", fill=INK, font=font, anchor="mm")
    # Field lines (curved)
    draw.arc([180, 80, 330, 200], 0, 180, fill=INK, width=FINE)
    return img


def gen_obj_lightbulb():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 220
    # Bulb
    draw.arc([cx - 80, cy - 100, cx + 80, cy + 60], 180, 360, fill=INK, width=OUTLINE)
    draw.arc([cx - 80, cy - 100, cx + 80, cy + 60], 0, 180, fill=INK, width=OUTLINE)
    # Base
    draw.rectangle([cx - 35, cy + 55, cx + 35, cy + 110], outline=INK, width=OUTLINE)
    # Screw threads
    for i in range(3):
        y = cy + 65 + i * 15
        draw.line([(cx - 35, y), (cx + 35, y)], fill=INK, width=FINE)
    # Filament
    for i in range(4):
        x = cx - 15 + i * 10
        draw.line([(x, cy + 20), (x, cy - 20)], fill=INK, width=FINE)
    draw.line([(cx - 15, cy - 20), (cx + 15, cy - 20)], fill=INK, width=FINE)
    # Glow lines
    for angle_deg in range(0, 360, 45):
        angle = math.radians(angle_deg)
        x1 = cx + int(95 * math.cos(angle))
        y1 = (cy - 20) + int(95 * math.sin(angle))
        x2 = cx + int(115 * math.cos(angle))
        y2 = (cy - 20) + int(115 * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=INK, width=FINE)
    return img


def gen_obj_thermometer():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx = 256
    # Tube
    draw.rectangle([cx - 15, 80, cx + 15, 350], outline=INK, width=OUTLINE)
    # Bulb at bottom
    draw_circle(draw, cx, 380, 35, width=OUTLINE)
    # Mercury level line
    draw.line([(cx, 380), (cx, 180)], fill=INK, width=DETAIL)
    # Scale marks
    for i in range(8):
        y = 100 + i * 35
        draw.line([(cx + 15, y), (cx + 30, y)], fill=INK, width=FINE)
    return img


def gen_obj_prism():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Triangle prism
    pts = [(256, 100), (120, 400), (392, 400)]
    draw.polygon(pts, outline=INK)
    draw.line(pts + [pts[0]], fill=INK, width=OUTLINE)
    # Light ray entering
    draw.line([(40, 250), (190, 280)], fill=INK, width=DETAIL)
    # Light rays exiting (spread)
    draw.line([(330, 300), (470, 250)], fill=INK, width=FINE)
    draw.line([(330, 310), (470, 300)], fill=INK, width=FINE)
    draw.line([(330, 320), (470, 350)], fill=INK, width=FINE)
    return img


def gen_obj_atom():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    # Nucleus
    draw_circle(draw, cx, cy, 20, width=OUTLINE, fill=INK)
    # Orbits (ellipses at angles)
    for angle_deg in [0, 60, 120]:
        angle = math.radians(angle_deg)
        # Draw rotated ellipse using arc
        draw.ellipse([cx - 120, cy - 40, cx + 120, cy + 40],
                     outline=INK, width=DETAIL)
        # Electron dot on orbit
        ex = cx + int(110 * math.cos(angle + 0.5))
        ey = cy + int(35 * math.sin(angle + 0.5))
        draw_dot(draw, ex, ey, r=8, fill=INK)
    # Rotate two more orbits by drawing tilted
    for tilt in [60, -60]:
        r = math.radians(tilt)
        pts = []
        for a in range(0, 360, 10):
            ar = math.radians(a)
            x = 120 * math.cos(ar)
            y = 40 * math.sin(ar)
            rx = x * math.cos(r) - y * math.sin(r)
            ry = x * math.sin(r) + y * math.cos(r)
            pts.append((cx + int(rx), cy + int(ry)))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=INK, width=DETAIL)
        draw.line([pts[-1], pts[0]], fill=INK, width=DETAIL)
    return img


def gen_obj_gear():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    # Inner circle
    draw_circle(draw, cx, cy, 50, width=OUTLINE)
    # Outer with teeth
    r_inner = 80
    r_outer = 110
    teeth = 12
    pts = []
    for i in range(teeth * 2):
        angle = math.radians(i * 360 / (teeth * 2))
        r = r_outer if i % 2 == 0 else r_inner
        pts.append((cx + int(r * math.cos(angle)),
                     cy + int(r * math.sin(angle))))
    draw.polygon(pts, outline=INK)
    draw.line(pts + [pts[0]], fill=INK, width=OUTLINE)
    # Center hole
    draw_circle(draw, cx, cy, 15, width=DETAIL)
    return img


def gen_obj_candle():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx = 256
    # Body
    draw.rectangle([cx - 30, 200, cx + 30, 420], outline=INK, width=OUTLINE)
    # Wick
    draw.line([(cx, 200), (cx, 160)], fill=INK, width=DETAIL)
    # Flame (teardrop)
    draw.polygon([(cx, 100), (cx - 20, 160), (cx + 20, 160)], outline=INK)
    draw.arc([cx - 20, 140, cx + 20, 175], 0, 180, fill=INK, width=DETAIL)
    # Wax drip
    draw.line([(cx + 25, 200), (cx + 28, 240)], fill=INK, width=FINE)
    draw_dot(draw, cx + 28, 245, r=4, fill=INK)
    return img


def gen_obj_rocket():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx = 256
    # Nose cone
    draw.polygon([(cx, 60), (cx - 40, 160), (cx + 40, 160)], outline=INK)
    draw.line([(cx, 60), (cx - 40, 160), (cx + 40, 160), (cx, 60)],
              fill=INK, width=OUTLINE)
    # Body
    draw.rectangle([cx - 40, 160, cx + 40, 360], outline=INK, width=OUTLINE)
    # Window
    draw_circle(draw, cx, 230, 18, width=DETAIL)
    # Fins
    draw.polygon([(cx - 40, 300), (cx - 80, 380), (cx - 40, 360)], outline=INK)
    draw.line([(cx - 40, 300), (cx - 80, 380), (cx - 40, 360)],
              fill=INK, width=OUTLINE)
    draw.polygon([(cx + 40, 300), (cx + 80, 380), (cx + 40, 360)], outline=INK)
    draw.line([(cx + 40, 300), (cx + 80, 380), (cx + 40, 360)],
              fill=INK, width=OUTLINE)
    # Exhaust
    draw.line([(cx - 20, 360), (cx - 30, 430)], fill=INK, width=DETAIL)
    draw.line([(cx, 360), (cx, 440)], fill=INK, width=DETAIL)
    draw.line([(cx + 20, 360), (cx + 30, 430)], fill=INK, width=DETAIL)
    return img


def gen_obj_car():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Body
    draw.rectangle([80, 250, 430, 350], outline=INK, width=OUTLINE)
    # Roof
    draw.polygon([(150, 250), (200, 170), (350, 170), (380, 250)], outline=INK)
    draw.line([(150, 250), (200, 170), (350, 170), (380, 250)],
              fill=INK, width=OUTLINE)
    # Windows
    draw.line([(260, 175), (260, 248)], fill=INK, width=DETAIL)
    # Wheels
    draw_circle(draw, 160, 355, 35, width=OUTLINE)
    draw_circle(draw, 160, 355, 15, width=FINE)
    draw_circle(draw, 360, 355, 35, width=OUTLINE)
    draw_circle(draw, 360, 355, 15, width=FINE)
    return img


def gen_obj_train():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Body
    draw.rectangle([60, 200, 420, 350], outline=INK, width=OUTLINE)
    # Cab
    draw.rectangle([340, 140, 420, 200], outline=INK, width=OUTLINE)
    # Smokestack
    draw.rectangle([100, 140, 140, 200], outline=INK, width=OUTLINE)
    draw.ellipse([90, 120, 150, 145], outline=INK, width=DETAIL)
    # Smoke puffs
    draw_circle(draw, 120, 100, 15, width=FINE)
    draw_circle(draw, 140, 80, 20, width=FINE)
    draw_circle(draw, 110, 70, 12, width=FINE)
    # Wheels
    draw_circle(draw, 120, 370, 30, width=OUTLINE)
    draw_circle(draw, 220, 370, 30, width=OUTLINE)
    draw_circle(draw, 320, 370, 30, width=OUTLINE)
    # Rail
    draw.line([(30, 400), (470, 400)], fill=INK, width=DETAIL)
    return img


def gen_obj_clock_pendulum():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx = 256
    # Clock face
    draw_circle(draw, cx, 160, 90, width=OUTLINE)
    # Hour marks
    for i in range(12):
        angle = math.radians(i * 30 - 90)
        x1 = cx + int(75 * math.cos(angle))
        y1 = 160 + int(75 * math.sin(angle))
        x2 = cx + int(85 * math.cos(angle))
        y2 = 160 + int(85 * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=INK, width=DETAIL)
    # Hands
    draw.line([(cx, 160), (cx + 30, 110)], fill=INK, width=DETAIL)
    draw.line([(cx, 160), (cx - 15, 130)], fill=INK, width=OUTLINE)
    # Pendulum rod
    draw.line([(cx, 250), (cx + 20, 400)], fill=INK, width=DETAIL)
    # Pendulum bob
    draw_circle(draw, cx + 20, 400, 25, width=OUTLINE)
    return img


def gen_obj_pulley():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx = 256
    # Mount
    draw.line([(200, 60), (312, 60)], fill=INK, width=OUTLINE)
    draw.line([(cx, 60), (cx, 100)], fill=INK, width=DETAIL)
    # Wheel
    draw_circle(draw, cx, 140, 40, width=OUTLINE)
    draw_circle(draw, cx, 140, 5, width=DETAIL)
    # Rope
    draw.line([(cx - 40, 140), (cx - 40, 420)], fill=INK, width=DETAIL)
    draw.line([(cx + 40, 140), (cx + 40, 420)], fill=INK, width=DETAIL)
    # Weight
    draw.rectangle([cx + 20, 380, cx + 60, 430], outline=INK, width=OUTLINE)
    # Pull arrow
    draw.line([(cx - 40, 420), (cx - 40, 380)], fill=INK, width=DETAIL)
    draw.polygon([(cx - 50, 390), (cx - 40, 370), (cx - 30, 390)], fill=INK)
    return img


def gen_obj_cannon():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Barrel
    draw.line([(150, 220), (380, 180)], fill=INK, width=THICK)
    draw.line([(150, 270), (380, 230)], fill=INK, width=THICK)
    # Barrel opening
    draw.ellipse([370, 175, 400, 235], outline=INK, width=OUTLINE)
    # Rear
    draw.arc([130, 215, 170, 275], 90, 270, fill=INK, width=OUTLINE)
    # Carriage
    draw.polygon([(120, 270), (350, 240), (350, 310), (120, 310)], outline=INK)
    draw.line([(120, 270), (350, 240), (350, 310), (120, 310), (120, 270)],
              fill=INK, width=OUTLINE)
    # Wheels
    draw_circle(draw, 160, 340, 30, width=OUTLINE)
    draw_circle(draw, 310, 330, 30, width=OUTLINE)
    return img


def gen_obj_balance_scale():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx = 256
    # Base
    draw.polygon([(cx - 40, 430), (cx + 40, 430), (cx, 400)], outline=INK)
    draw.line([(cx - 40, 430), (cx + 40, 430), (cx, 400), (cx - 40, 430)],
              fill=INK, width=OUTLINE)
    # Pillar
    draw.line([(cx, 400), (cx, 150)], fill=INK, width=OUTLINE)
    # Beam
    draw.line([(100, 160), (412, 140)], fill=INK, width=OUTLINE)
    # Pivot
    draw_circle(draw, cx, 150, 10, width=OUTLINE)
    # Left pan
    draw.line([(100, 160), (80, 280)], fill=INK, width=DETAIL)
    draw.line([(100, 160), (170, 280)], fill=INK, width=DETAIL)
    draw.arc([60, 270, 190, 310], 0, 180, fill=INK, width=OUTLINE)
    # Right pan
    draw.line([(412, 140), (380, 260)], fill=INK, width=DETAIL)
    draw.line([(412, 140), (450, 260)], fill=INK, width=DETAIL)
    draw.arc([360, 250, 470, 290], 0, 180, fill=INK, width=OUTLINE)
    return img


def gen_obj_electron():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    draw_circle(draw, cx, cy, 60, width=OUTLINE)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((cx, cy), "\u2212", fill=INK, font=font, anchor="mm")
    return img


def gen_obj_proton():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    draw_circle(draw, cx, cy, 60, width=OUTLINE)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 72)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((cx, cy), "+", fill=INK, font=font, anchor="mm")
    return img


def gen_obj_wave():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    pts = []
    for x in range(60, 460):
        y = 256 + int(80 * math.sin((x - 60) * 4 * math.pi / 400))
        pts.append((x, y))
    for i in range(len(pts) - 1):
        draw.line([pts[i], pts[i + 1]], fill=INK, width=OUTLINE)
    # Axis
    draw.line([(50, 256), (470, 256)], fill=INK, width=FINE)
    return img


def gen_obj_compass():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    draw_circle(draw, cx, cy, 110, width=OUTLINE)
    draw_circle(draw, cx, cy, 100, width=DETAIL)
    # Cardinal directions
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((cx, cy - 85), "N", fill=INK, font=font, anchor="mm")
    draw.text((cx, cy + 85), "S", fill=INK, font=font, anchor="mm")
    draw.text((cx + 85, cy), "E", fill=INK, font=font, anchor="mm")
    draw.text((cx - 85, cy), "W", fill=INK, font=font, anchor="mm")
    # Needle
    draw.polygon([(cx, cy - 70), (cx - 10, cy), (cx + 10, cy)], fill=INK)
    draw.polygon([(cx, cy + 70), (cx - 10, cy), (cx + 10, cy)], outline=INK)
    draw_dot(draw, cx, cy, r=6, fill=INK)
    return img


def gen_obj_beaker():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    # Trapezoid body
    draw.line([(160, 100), (140, 400), (370, 400), (350, 100)],
              fill=INK, width=OUTLINE)
    # Spout
    draw.line([(160, 100), (140, 80)], fill=INK, width=OUTLINE)
    # Liquid line
    draw.line([(148, 250), (358, 250)], fill=INK, width=DETAIL)
    # Measurement lines
    for i in range(5):
        y = 150 + i * 50
        draw.line([(350 - (350 - 160) * (y - 100) // 300 + 5, y),
                   (350 - (350 - 160) * (y - 100) // 300 + 25, y)],
                  fill=INK, width=FINE)
    return img


def gen_obj_hourglass():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx = 256
    # Top frame
    draw.line([(160, 80), (352, 80)], fill=INK, width=OUTLINE)
    # Bottom frame
    draw.line([(160, 430), (352, 430)], fill=INK, width=OUTLINE)
    # Glass shape — two triangles meeting at center
    draw.line([(170, 90), (cx, 255)], fill=INK, width=OUTLINE)
    draw.line([(342, 90), (cx, 255)], fill=INK, width=OUTLINE)
    draw.line([(170, 420), (cx, 255)], fill=INK, width=OUTLINE)
    draw.line([(342, 420), (cx, 255)], fill=INK, width=OUTLINE)
    # Sand dots in bottom
    for i in range(8):
        x = cx - 20 + (i % 4) * 12
        y = 350 + (i // 4) * 15
        draw_dot(draw, x, y, r=3, fill=INK)
    # Sand stream
    draw.line([(cx, 260), (cx, 340)], fill=INK, width=FINE)
    return img


def gen_obj_lens():
    img = new_transparent(OBJ_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    # Convex lens (two arcs)
    draw.arc([cx - 120, cy - 120, cx + 20, cy + 120], 300, 60, fill=INK, width=OUTLINE)
    draw.arc([cx - 20, cy - 120, cx + 120, cy + 120], 120, 240, fill=INK, width=OUTLINE)
    # Light rays
    draw.line([(40, 200), (cx - 30, 240)], fill=INK, width=DETAIL)
    draw.line([(40, 256), (cx - 30, 256)], fill=INK, width=DETAIL)
    draw.line([(40, 310), (cx - 30, 272)], fill=INK, width=DETAIL)
    # Converging rays
    draw.line([(cx + 30, 248), (430, 256)], fill=INK, width=DETAIL)
    draw.line([(cx + 30, 256), (430, 256)], fill=INK, width=DETAIL)
    draw.line([(cx + 30, 264), (430, 256)], fill=INK, width=DETAIL)
    # Focal point
    draw_dot(draw, 430, 256, r=5, fill=INK)
    return img


# ─── Background Drawing Functions ────────────────────────────────

def gen_bg_study():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Desk
    draw.line([(200, 700), (1720, 700)], fill=INK, width=OUTLINE)
    draw.line([(200, 700), (200, 900)], fill=INK, width=DETAIL)
    draw.line([(1720, 700), (1720, 900)], fill=INK, width=DETAIL)
    # Bookshelf on wall
    draw.rectangle([100, 100, 500, 500], outline=INK, width=OUTLINE)
    for i in range(4):
        y = 100 + i * 100
        draw.line([(100, y), (500, y)], fill=INK, width=DETAIL)
    # Books on shelf (vertical lines)
    for shelf in range(3):
        sy = 110 + shelf * 100
        for i in range(8):
            x = 120 + i * 45
            h = 60 + (i * 7) % 30
            draw.rectangle([x, sy + (90 - h), x + 30, sy + 90],
                           outline=INK, width=FINE)
    # Window
    draw.rectangle([1400, 100, 1800, 500], outline=INK, width=OUTLINE)
    draw.line([(1600, 100), (1600, 500)], fill=INK, width=DETAIL)
    draw.line([(1400, 300), (1800, 300)], fill=INK, width=DETAIL)
    return img


def gen_bg_laboratory():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Table
    draw.line([(100, 650), (1820, 650)], fill=INK, width=OUTLINE)
    draw.line([(100, 650), (100, 900)], fill=INK, width=DETAIL)
    draw.line([(1820, 650), (1820, 900)], fill=INK, width=DETAIL)
    # Shelf
    draw.line([(100, 200), (800, 200)], fill=INK, width=DETAIL)
    # Flask outlines on shelf
    # Erlenmeyer flask
    draw.line([(200, 200), (180, 140), (220, 100), (260, 140), (240, 200)],
              fill=INK, width=DETAIL)
    # Round bottom flask
    draw_circle(draw, 400, 160, 35, width=DETAIL)
    draw.line([(400, 125), (400, 100)], fill=INK, width=DETAIL)
    # Test tubes on table
    for i in range(3):
        x = 300 + i * 80
        draw.rectangle([x, 550, x + 20, 645], outline=INK, width=DETAIL)
        draw.arc([x, 635, x + 20, 655], 0, 180, fill=INK, width=DETAIL)
    return img


def gen_bg_chalkboard():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Board frame (dark fill inside)
    draw.rectangle([100, 80, 1820, 800], fill="#2A2A2A", outline=INK, width=THICK)
    # Inner border
    draw.rectangle([120, 100, 1800, 780], outline="#555555", width=DETAIL)
    # Chalk ledge
    draw.rectangle([100, 800, 1820, 840], outline=INK, width=OUTLINE)
    # Chalk pieces on ledge
    draw.rectangle([400, 810, 460, 825], outline="#CCCCCC", width=FINE)
    draw.rectangle([500, 810, 540, 825], outline="#CCCCCC", width=FINE)
    # Eraser
    draw.rectangle([700, 805, 780, 835], outline="#CCCCCC", width=DETAIL)
    return img


def gen_bg_grass_field():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Horizon
    draw.line([(0, 500), (1920, 500)], fill=INK, width=DETAIL)
    # Rolling hills
    draw.arc([-200, 350, 600, 550], 180, 360, fill=INK, width=DETAIL)
    draw.arc([400, 380, 1200, 560], 180, 360, fill=INK, width=DETAIL)
    draw.arc([1000, 360, 2100, 540], 180, 360, fill=INK, width=DETAIL)
    # Tree (stick + circle canopy)
    tx = 1600
    draw.line([(tx, 500), (tx, 320)], fill=INK, width=OUTLINE)
    draw_circle(draw, tx, 270, 60, width=OUTLINE)
    # Second tree
    tx2 = 300
    draw.line([(tx2, 500), (tx2, 350)], fill=INK, width=DETAIL)
    draw_circle(draw, tx2, 310, 45, width=DETAIL)
    # Grass tufts
    for x in range(100, 1800, 200):
        draw.line([(x, 520), (x - 8, 500)], fill=INK, width=FINE)
        draw.line([(x, 520), (x + 5, 498)], fill=INK, width=FINE)
        draw.line([(x, 520), (x + 12, 502)], fill=INK, width=FINE)
    return img


def gen_bg_ancient_greek_courtyard():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Floor tile lines
    for i in range(10):
        x = i * 200
        draw.line([(x, 700), (x, 1080)], fill=INK, width=FINE)
    for i in range(4):
        y = 700 + i * 100
        draw.line([(0, y), (1920, y)], fill=INK, width=FINE)
    # Three columns
    for i, cx in enumerate([400, 960, 1520]):
        # Column shaft
        draw.rectangle([cx - 30, 150, cx + 30, 700], outline=INK, width=OUTLINE)
        # Capital (top)
        draw.rectangle([cx - 45, 130, cx + 45, 160], outline=INK, width=DETAIL)
        # Base
        draw.rectangle([cx - 40, 690, cx + 40, 710], outline=INK, width=DETAIL)
        # Fluting (vertical lines)
        for j in range(-2, 3):
            draw.line([(cx + j * 12, 160), (cx + j * 12, 690)],
                      fill=INK, width=FINE)
    # Entablature
    draw.line([(350, 130), (1570, 130)], fill=INK, width=OUTLINE)
    draw.line([(350, 110), (1570, 110)], fill=INK, width=DETAIL)
    return img


def gen_bg_outer_space():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(42)
    # Stars (scattered dots)
    for _ in range(80):
        x = rng.randint(20, 1900)
        y = rng.randint(20, 1060)
        r = rng.choice([1, 1, 2, 2, 3])
        draw_dot(draw, x, y, r=r, fill=INK)
    # Crescent moon
    draw_circle(draw, 1600, 200, 80, width=OUTLINE)
    draw.ellipse([1570, 130, 1700, 270], fill=CREAM)
    draw_circle(draw, 1630, 195, 70, width=OUTLINE)
    return img


def gen_bg_ice_surface():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Horizon
    draw.line([(0, 400), (1920, 400)], fill=INK, width=OUTLINE)
    # Ice texture (dashed lines)
    rng = random.Random(43)
    for i in range(20):
        x1 = rng.randint(0, 1800)
        y1 = rng.randint(420, 1000)
        length = rng.randint(40, 150)
        draw.line([(x1, y1), (x1 + length, y1 + rng.randint(-10, 10))],
                  fill=INK, width=FINE)
    # Distant mountains
    draw.line([(0, 400), (300, 250), (600, 350), (900, 200),
               (1200, 320), (1500, 230), (1920, 400)],
              fill=INK, width=DETAIL)
    return img


def gen_bg_deep_space():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    rng = random.Random(44)
    # Stars
    for _ in range(120):
        x = rng.randint(10, 1910)
        y = rng.randint(10, 1070)
        r = rng.choice([1, 1, 1, 2, 2, 3])
        draw_dot(draw, x, y, r=r, fill=INK)
    # Planet circle
    draw_circle(draw, 400, 600, 150, width=OUTLINE)
    # Planet ring
    draw.arc([200, 550, 600, 680], 160, 380, fill=INK, width=DETAIL)
    return img


def gen_bg_ocean():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Horizon
    draw.line([(0, 350), (1920, 350)], fill=INK, width=OUTLINE)
    # Wavy water lines
    for row in range(8):
        y = 380 + row * 80
        pts = []
        for x in range(0, 1921, 5):
            offset = 15 * math.sin(x * 0.02 + row * 1.5)
            pts.append((x, int(y + offset)))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=INK, width=FINE if row > 2 else DETAIL)
    return img


def gen_bg_mountain():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Mountain peaks
    draw.polygon([(600, 150), (300, 600), (900, 600)], outline=INK)
    draw.line([(600, 150), (300, 600), (900, 600), (600, 150)],
              fill=INK, width=OUTLINE)
    draw.polygon([(1200, 200), (900, 600), (1500, 600)], outline=INK)
    draw.line([(1200, 200), (900, 600), (1500, 600), (1200, 200)],
              fill=INK, width=OUTLINE)
    # Smaller peak
    draw.line([(200, 400), (0, 600)], fill=INK, width=DETAIL)
    draw.line([(200, 400), (400, 600)], fill=INK, width=DETAIL)
    # Rolling foreground
    draw.arc([-100, 500, 800, 750], 180, 360, fill=INK, width=DETAIL)
    draw.arc([600, 520, 1400, 730], 180, 360, fill=INK, width=DETAIL)
    draw.arc([1200, 510, 2000, 740], 180, 360, fill=INK, width=DETAIL)
    return img


def gen_bg_spacetime():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Grid lines curving downward (gravitational well)
    cx, cy = 960, 540
    # Horizontal grid lines
    for row in range(-4, 5):
        pts = []
        for x in range(0, 1921, 20):
            base_y = cy + row * 100
            dx = x - cx
            dy_factor = max(0, 1 - (dx * dx + (row * 100) ** 2) / (600 * 600))
            dip = int(150 * dy_factor)
            pts.append((x, base_y + dip))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=INK, width=FINE)
    # Vertical grid lines
    for col in range(-8, 9):
        pts = []
        for y_step in range(-4, 5):
            base_x = cx + col * 120
            base_y = cy + y_step * 100
            dx = base_x - cx
            dy_factor = max(0, 1 - (dx * dx + (y_step * 100) ** 2) / (600 * 600))
            dip = int(150 * dy_factor)
            pts.append((base_x, base_y + dip))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=INK, width=FINE)
    # Star dots
    rng = random.Random(45)
    for _ in range(20):
        x = rng.randint(20, 1900)
        y = rng.randint(20, 200)
        draw_dot(draw, x, y, r=2, fill=INK)
    return img


def gen_bg_quantum():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 960, 540
    # Concentric circle orbits
    for r in range(80, 400, 70):
        draw_circle(draw, cx, cy, r, width=FINE)
    # Electron dots on orbits
    rng = random.Random(46)
    for r in range(80, 400, 70):
        n_electrons = r // 80 + 1
        for i in range(n_electrons):
            angle = rng.random() * 2 * math.pi
            ex = cx + int(r * math.cos(angle))
            ey = cy + int(r * math.sin(angle))
            draw_dot(draw, ex, ey, r=5, fill=INK)
    # Nucleus
    draw_circle(draw, cx, cy, 25, width=OUTLINE, fill=INK)
    return img


def gen_bg_electromagnetic():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Positive charge
    draw_circle(draw, 600, 540, 30, width=OUTLINE)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((600, 540), "+", fill=INK, font=font, anchor="mm")
    # Negative charge
    draw_circle(draw, 1320, 540, 30, width=OUTLINE)
    draw.text((1320, 540), "\u2212", fill=INK, font=font, anchor="mm")
    # Curved field lines from + to -
    for offset in [-200, -100, 0, 100, 200]:
        draw.arc([500, 340 + offset, 1420, 740 + offset],
                 160, 380, fill=INK, width=FINE)
    # More field lines
    for offset in [-150, -50, 50, 150]:
        draw.arc([550, 380 + offset, 1370, 700 + offset],
                 340, 200, fill=INK, width=FINE)
    return img


def gen_bg_thermal():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Wavy horizontal heat lines
    for row in range(12):
        y = 80 + row * 80
        pts = []
        amplitude = 10 + row * 3
        for x in range(0, 1921, 5):
            offset = amplitude * math.sin(x * 0.015 + row * 0.7)
            pts.append((x, int(y + offset)))
        for i in range(len(pts) - 1):
            draw.line([pts[i], pts[i + 1]], fill=INK,
                      width=DETAIL if row < 6 else FINE)
    return img


def gen_bg_library():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Tall bookshelves
    for shelf_x in [100, 700, 1300]:
        draw.rectangle([shelf_x, 50, shelf_x + 500, 900],
                       outline=INK, width=OUTLINE)
        # Shelves
        for i in range(6):
            y = 50 + i * 140
            draw.line([(shelf_x, y), (shelf_x + 500, y)],
                      fill=INK, width=DETAIL)
        # Books
        for shelf_i in range(5):
            sy = 60 + shelf_i * 140
            for j in range(10):
                bx = shelf_x + 15 + j * 48
                h = 80 + (j * 13) % 40
                draw.rectangle([bx, sy + (130 - h), bx + 35, sy + 130],
                               outline=INK, width=FINE)
    return img


def gen_bg_workshop():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Workbench
    draw.line([(100, 650), (1820, 650)], fill=INK, width=OUTLINE)
    draw.line([(100, 650), (100, 950)], fill=INK, width=DETAIL)
    draw.line([(1820, 650), (1820, 950)], fill=INK, width=DETAIL)
    # Pegboard on wall
    draw.rectangle([200, 100, 1000, 500], outline=INK, width=DETAIL)
    # Hanging tools
    # Hammer
    draw.line([(350, 150), (350, 300)], fill=INK, width=DETAIL)
    draw.rectangle([330, 140, 370, 170], outline=INK, width=DETAIL)
    # Wrench
    draw.line([(500, 150), (500, 320)], fill=INK, width=DETAIL)
    draw_circle(draw, 500, 150, 15, width=DETAIL)
    # Saw
    draw.line([(650, 150), (650, 200)], fill=INK, width=DETAIL)
    draw.polygon([(650, 200), (620, 350), (680, 350)], outline=INK)
    # Pliers
    draw.line([(800, 150), (780, 300)], fill=INK, width=DETAIL)
    draw.line([(800, 150), (820, 300)], fill=INK, width=DETAIL)
    return img


def gen_bg_desert():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Sun
    draw_circle(draw, 1600, 200, 80, width=OUTLINE)
    # Rays
    for angle_deg in range(0, 360, 30):
        angle = math.radians(angle_deg)
        x1 = 1600 + int(95 * math.cos(angle))
        y1 = 200 + int(95 * math.sin(angle))
        x2 = 1600 + int(120 * math.cos(angle))
        y2 = 200 + int(120 * math.sin(angle))
        draw.line([(x1, y1), (x2, y2)], fill=INK, width=DETAIL)
    # Sand dunes (wavy lines)
    draw.arc([-200, 400, 800, 700], 180, 360, fill=INK, width=OUTLINE)
    draw.arc([500, 350, 1400, 680], 180, 360, fill=INK, width=OUTLINE)
    draw.arc([1100, 380, 2100, 720], 180, 360, fill=INK, width=OUTLINE)
    return img


def gen_bg_road_highway():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Vanishing point
    vx, vy = 960, 300
    # Road edges converging
    draw.line([(0, 1080), (vx, vy)], fill=INK, width=OUTLINE)
    draw.line([(1920, 1080), (vx, vy)], fill=INK, width=OUTLINE)
    # Center dashes
    for i in range(12):
        t1 = 0.1 + i * 0.075
        t2 = t1 + 0.04
        x1 = int(960 + (960 - 960) * (1 - t1))
        y1 = int(vy + (1080 - vy) * t1)
        x2 = int(960 + (960 - 960) * (1 - t2))
        y2 = int(vy + (1080 - vy) * t2)
        draw.line([(x1, y1), (x2, y2)], fill=INK, width=DETAIL)
    # Horizon
    draw.line([(0, vy), (1920, vy)], fill=INK, width=FINE)
    return img


def gen_bg_observatory():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Dome arc
    draw.arc([400, 100, 1520, 800], 180, 360, fill=INK, width=OUTLINE)
    # Dome slit (opening)
    draw.line([(940, 100), (940, 450)], fill=INK, width=DETAIL)
    draw.line([(980, 100), (980, 450)], fill=INK, width=DETAIL)
    # Telescope inside (simple)
    draw.line([(800, 600), (960, 300)], fill=INK, width=OUTLINE)
    draw.line([(800, 630), (960, 330)], fill=INK, width=OUTLINE)
    # Building base
    draw.rectangle([400, 450, 1520, 900], outline=INK, width=OUTLINE)
    # Stars
    rng = random.Random(47)
    for _ in range(30):
        x = rng.randint(20, 1900)
        y = rng.randint(20, 250)
        draw_dot(draw, x, y, r=rng.choice([1, 2, 2]), fill=INK)
    return img


def gen_bg_patent_office():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Desk
    draw.rectangle([300, 550, 1200, 620], outline=INK, width=OUTLINE)
    draw.line([(300, 620), (300, 900)], fill=INK, width=DETAIL)
    draw.line([(1200, 620), (1200, 900)], fill=INK, width=DETAIL)
    # Window
    draw.rectangle([1400, 100, 1800, 500], outline=INK, width=OUTLINE)
    draw.line([(1600, 100), (1600, 500)], fill=INK, width=DETAIL)
    draw.line([(1400, 300), (1800, 300)], fill=INK, width=DETAIL)
    # Papers on desk
    for i in range(4):
        x = 400 + i * 160
        draw.rectangle([x, 480, x + 100, 545], outline=INK, width=FINE)
        # Text lines on paper
        for j in range(4):
            draw.line([(x + 10, 495 + j * 12), (x + 80, 495 + j * 12)],
                      fill=INK, width=FINE)
    # Filing cabinet
    draw.rectangle([100, 200, 250, 800], outline=INK, width=OUTLINE)
    for i in range(4):
        y = 200 + i * 150
        draw.line([(100, y), (250, y)], fill=INK, width=DETAIL)
        draw.rectangle([155, y + 50, 195, y + 70], outline=INK, width=FINE)
    return img


def gen_bg_pisa_tower():
    img = new_cream(BG_SIZE)
    draw = ImageDraw.Draw(img)
    # Tilted stacked rectangles (the tower)
    tilt = 0.08  # radians
    cx_base = 900
    floors = 7
    floor_h = 80
    floor_w = 120
    for i in range(floors):
        # Each floor offset by tilt
        x_offset = int(i * floor_h * math.sin(tilt))
        y_base = 800 - i * floor_h
        x1 = cx_base - floor_w // 2 + x_offset
        x2 = cx_base + floor_w // 2 + x_offset
        y1 = y_base - floor_h
        y2 = y_base
        draw.rectangle([x1, y1, x2, y2], outline=INK, width=OUTLINE)
        # Columns on each floor
        for j in range(3):
            col_x = x1 + 20 + j * 35
            draw.line([(col_x, y1 + 10), (col_x, y2 - 5)],
                      fill=INK, width=FINE)
    # Hill curve
    draw.arc([500, 700, 1400, 950], 180, 360, fill=INK, width=OUTLINE)
    # Ground line
    draw.line([(0, 850), (1920, 850)], fill=INK, width=DETAIL)
    return img


# ─── Comic Element Drawing Functions ─────────────────────────────

def gen_elem_thought_bubble():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    # Main cloud shape
    centers = [(256, 200), (200, 180), (310, 180), (220, 230), (290, 230),
               (256, 160), (180, 210), (330, 210)]
    for cx, cy in centers:
        r = 50 + ((cx + cy) % 20)
        draw_circle(draw, cx, cy, r, width=OUTLINE)
    # Trailing dots
    draw_circle(draw, 220, 340, 18, width=OUTLINE)
    draw_circle(draw, 200, 390, 12, width=OUTLINE)
    draw_circle(draw, 185, 430, 8, width=OUTLINE)
    return img


def gen_elem_speech_bubble():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    # Smooth oval
    draw.ellipse([80, 60, 432, 340], outline=INK, width=OUTLINE)
    # Pointer triangle
    draw.polygon([(200, 330), (160, 440), (260, 335)], outline=INK)
    draw.line([(200, 330), (160, 440), (260, 335)], fill=INK, width=OUTLINE)
    return img


def gen_elem_motion_lines():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    # 4 horizontal speed lines
    for i, y in enumerate([180, 230, 280, 330]):
        x_start = 80 + i * 20
        x_end = 430 - i * 15
        draw.line([(x_start, y), (x_end, y)], fill=INK, width=OUTLINE)
    return img


def gen_elem_impact_star():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    cx, cy = 256, 256
    # Jagged starburst
    points = []
    num_points = 12
    for i in range(num_points * 2):
        angle = math.radians(i * 360 / (num_points * 2) - 90)
        r = 180 if i % 2 == 0 else 80
        points.append((cx + int(r * math.cos(angle)),
                        cy + int(r * math.sin(angle))))
    draw.polygon(points, outline=INK)
    draw.line(points + [points[0]], fill=INK, width=OUTLINE)
    return img


def gen_elem_question_mark():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 300)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((256, 256), "?", fill=INK, font=font, anchor="mm")
    return img


def gen_elem_exclamation():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 300)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((256, 256), "!", fill=INK, font=font, anchor="mm")
    return img


def gen_elem_arrow_curved():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    # Curved arrow
    draw.arc([100, 100, 412, 412], 200, 340, fill=INK, width=OUTLINE)
    # Arrowhead at end of arc
    # End point of arc at 340 degrees
    angle = math.radians(340)
    ex = 256 + int(156 * math.cos(angle))
    ey = 256 + int(156 * math.sin(angle))
    # Arrow head
    a1 = math.radians(310)
    a2 = math.radians(350)
    draw.polygon([
        (ex, ey),
        (ex + int(30 * math.cos(a1)), ey + int(30 * math.sin(a1))),
        (ex + int(30 * math.cos(a2)), ey + int(30 * math.sin(a2))),
    ], fill=INK)
    return img


def gen_elem_force_arrow():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    # Thick bold arrow
    draw.polygon([
        (60, 220), (340, 220), (340, 170),
        (450, 256),
        (340, 342), (340, 292), (60, 292)
    ], outline=INK, fill=INK)
    return img


def gen_elem_lightning():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    # Zigzag bolt
    pts = [(280, 50), (220, 200), (300, 200), (200, 350),
           (290, 350), (180, 470)]
    draw.line(pts, fill=INK, width=THICK)
    # Offset line for thickness
    pts2 = [(x + 15, y) for x, y in pts]
    draw.line(pts2, fill=INK, width=OUTLINE)
    return img


def gen_elem_equals_sign():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 300)
    except (OSError, IOError):
        font = ImageFont.load_default()
    draw.text((256, 256), "=", fill=INK, font=font, anchor="mm")
    return img


def gen_elem_checkmark():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    draw.line([(120, 280), (220, 400), (400, 120)], fill=INK, width=THICK)
    return img


def gen_elem_crossmark():
    img = new_transparent(ELEM_SIZE)
    draw = ImageDraw.Draw(img)
    draw.line([(120, 120), (392, 392)], fill=INK, width=THICK)
    draw.line([(392, 120), (120, 392)], fill=INK, width=THICK)
    return img


# ─── Asset Registry ──────────────────────────────────────────────

CHARACTERS = {
    "char_newton": gen_char_newton,
    "char_aristotle": gen_char_aristotle,
    "char_galileo": gen_char_galileo,
    "char_einstein": gen_char_einstein,
    "char_euler": gen_char_euler,
    "char_kepler": gen_char_kepler,
    "char_lagrange": gen_char_lagrange,
    "char_hamilton": gen_char_hamilton,
    "char_noether": gen_char_noether,
    "char_descartes": gen_char_descartes,
    "char_leibniz": gen_char_leibniz,
    "char_maxwell": gen_char_maxwell,
    "char_faraday": gen_char_faraday,
    "char_boltzmann": gen_char_boltzmann,
    "char_planck": gen_char_planck,
    "char_bohr": gen_char_bohr,
    "char_schrodinger": gen_char_schrodinger,
    "char_dirac": gen_char_dirac,
    "char_feynman": gen_char_feynman,
    "char_heisenberg": gen_char_heisenberg,
    "char_philoponus": gen_char_philoponus,
    "char_buridan": gen_char_buridan,
}

OBJECTS = {
    "obj_ball_red": gen_obj_ball_red,
    "obj_ramp_wood": gen_obj_ramp_wood,
    "obj_pendulum": gen_obj_pendulum,
    "obj_spring": gen_obj_spring,
    "obj_arrow_right": gen_obj_arrow_right,
    "obj_telescope": gen_obj_telescope,
    "obj_book_open": gen_obj_book_open,
    "obj_scroll": gen_obj_scroll,
    "obj_apple_green": gen_obj_apple_green,
    "obj_magnet": gen_obj_magnet,
    "obj_lightbulb": gen_obj_lightbulb,
    "obj_thermometer": gen_obj_thermometer,
    "obj_prism": gen_obj_prism,
    "obj_atom": gen_obj_atom,
    "obj_gear": gen_obj_gear,
    "obj_candle": gen_obj_candle,
    "obj_rocket": gen_obj_rocket,
    "obj_car": gen_obj_car,
    "obj_train": gen_obj_train,
    "obj_clock_pendulum": gen_obj_clock_pendulum,
    "obj_pulley": gen_obj_pulley,
    "obj_cannon": gen_obj_cannon,
    "obj_balance_scale": gen_obj_balance_scale,
    "obj_electron": gen_obj_electron,
    "obj_proton": gen_obj_proton,
    "obj_wave": gen_obj_wave,
    "obj_compass": gen_obj_compass,
    "obj_beaker": gen_obj_beaker,
    "obj_hourglass": gen_obj_hourglass,
    "obj_lens": gen_obj_lens,
}

BACKGROUNDS = {
    "bg_study": gen_bg_study,
    "bg_laboratory": gen_bg_laboratory,
    "bg_chalkboard": gen_bg_chalkboard,
    "bg_grass_field": gen_bg_grass_field,
    "bg_ancient_greek_courtyard": gen_bg_ancient_greek_courtyard,
    "bg_outer_space": gen_bg_outer_space,
    "bg_ice_surface": gen_bg_ice_surface,
    "bg_deep_space": gen_bg_deep_space,
    "bg_ocean": gen_bg_ocean,
    "bg_mountain": gen_bg_mountain,
    "bg_spacetime": gen_bg_spacetime,
    "bg_quantum": gen_bg_quantum,
    "bg_electromagnetic": gen_bg_electromagnetic,
    "bg_thermal": gen_bg_thermal,
    "bg_library": gen_bg_library,
    "bg_workshop": gen_bg_workshop,
    "bg_desert": gen_bg_desert,
    "bg_road_highway": gen_bg_road_highway,
    "bg_observatory": gen_bg_observatory,
    "bg_patent_office": gen_bg_patent_office,
    "bg_pisa_tower": gen_bg_pisa_tower,
}

ELEMENTS = {
    "elem_thought_bubble": gen_elem_thought_bubble,
    "elem_speech_bubble": gen_elem_speech_bubble,
    "elem_motion_lines": gen_elem_motion_lines,
    "elem_impact_star": gen_elem_impact_star,
    "elem_question_mark": gen_elem_question_mark,
    "elem_exclamation": gen_elem_exclamation,
    "elem_arrow_curved": gen_elem_arrow_curved,
    "elem_force_arrow": gen_elem_force_arrow,
    "elem_lightning": gen_elem_lightning,
    "elem_equals_sign": gen_elem_equals_sign,
    "elem_checkmark": gen_elem_checkmark,
    "elem_crossmark": gen_elem_crossmark,
}


# ─── Main ────────────────────────────────────────────────────────

def generate_all():
    """Generate all assets."""
    total = len(CHARACTERS) + len(OBJECTS) + len(BACKGROUNDS) + len(ELEMENTS)
    count = 0

    print(f"Generating {total} B&W comic line art assets...")
    print(f"Output: {OUTPUT}\n")

    print(f"--- Characters ({len(CHARACTERS)}) ---")
    for name, gen_fn in CHARACTERS.items():
        img = gen_fn()
        path = save_asset(img, "characters", name)
        count += 1
        print(f"  [{count}/{total}] {name} -> {path.name}")

    print(f"\n--- Objects ({len(OBJECTS)}) ---")
    for name, gen_fn in OBJECTS.items():
        img = gen_fn()
        path = save_asset(img, "objects", name)
        count += 1
        print(f"  [{count}/{total}] {name} -> {path.name}")

    print(f"\n--- Backgrounds ({len(BACKGROUNDS)}) ---")
    for name, gen_fn in BACKGROUNDS.items():
        img = gen_fn()
        path = save_asset(img, "backgrounds", name)
        count += 1
        print(f"  [{count}/{total}] {name} -> {path.name}")

    print(f"\n--- Comic Elements ({len(ELEMENTS)}) ---")
    for name, gen_fn in ELEMENTS.items():
        img = gen_fn()
        path = save_asset(img, "elements", name)
        count += 1
        print(f"  [{count}/{total}] {name} -> {path.name}")

    print(f"\nDone! Generated {count} assets.")


if __name__ == "__main__":
    generate_all()
