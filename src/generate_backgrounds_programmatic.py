#!/usr/bin/env python3
"""
Generate ALL background assets programmatically using PIL.
Art style: "My First Heroes" board-book — flat solid colors, simple geometric shapes,
rounded hills, rectangles, circles, minimal detail, no gradients, no texture.

Usage:
    python3 src/generate_backgrounds_programmatic.py
"""

import os
import math
from PIL import Image, ImageDraw

# ── Output directory ──
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(BASE_DIR, "data", "assets", "physics", "backgrounds")

# ── Color Palette ──
CREAM = "#FFF5E6"
CORAL_RED = "#E85D5D"
NAVY = "#1A2744"
SAGE_GREEN = "#7FB685"
GOLD = "#F5C518"
LAVENDER = "#C5A3D9"
SKY_BLUE = "#87CEEB"
SOFT_PINK = "#F4B8C1"

# Extended palette for specific scenes
DARK_GREEN = "#2D5A3D"
BROWN = "#8B6F47"
DARK_BROWN = "#5C3D2E"
LIGHT_GRAY = "#E8E8E8"
MEDIUM_GRAY = "#B0B0B0"
DARK_GRAY = "#4A4A4A"
WHITE = "#FFFFFF"
TAN = "#D4B896"
ORANGE = "#E8914A"
DEEP_PURPLE = "#3D1F56"
CYAN = "#4DD9D9"
PALE_BLUE = "#C5E3F0"
WARM_BROWN = "#A0784A"
WOOD_BROWN = "#7A5C3A"
LIGHT_WOOD = "#C4A06A"
DARK_WOOD = "#4A3520"


def ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


# ── Helper drawing functions ──

def draw_rounded_rect(draw, bbox, radius, fill):
    """Draw a rounded rectangle."""
    x0, y0, x1, y1 = bbox
    draw.rounded_rectangle(bbox, radius=radius, fill=fill)


def draw_cloud(draw, cx, cy, size, color=WHITE):
    """Draw a simple cloud from overlapping ellipses."""
    s = size
    draw.ellipse([cx - s, cy - s * 0.5, cx + s, cy + s * 0.5], fill=color)
    draw.ellipse([cx - s * 1.3, cy - s * 0.2, cx - s * 0.1, cy + s * 0.6], fill=color)
    draw.ellipse([cx + s * 0.1, cy - s * 0.2, cx + s * 1.3, cy + s * 0.6], fill=color)
    draw.ellipse([cx - s * 0.7, cy - s * 0.8, cx + s * 0.7, cy + s * 0.1], fill=color)


def draw_sun(draw, cx, cy, radius, color=GOLD):
    """Draw a simple circle sun."""
    draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius], fill=color)


def draw_star(draw, cx, cy, size, color=GOLD):
    """Draw a small star as a diamond/dot."""
    draw.ellipse([cx - size, cy - size, cx + size, cy + size], fill=color)


def draw_book_rect(draw, x, y, w, h, color):
    """Draw a simple book rectangle on a shelf."""
    draw.rectangle([x, y, x + w, y + h], fill=color)


def draw_window(draw, x, y, w, h, frame_color=BROWN, sky_color=SKY_BLUE):
    """Draw a simple window with frame."""
    draw.rectangle([x - 4, y - 4, x + w + 4, y + h + 4], fill=frame_color)
    draw.rectangle([x, y, x + w, y + h], fill=sky_color)
    # Cross bars
    draw.rectangle([x + w // 2 - 2, y, x + w // 2 + 2, y + h], fill=frame_color)
    draw.rectangle([x, y + h // 2 - 2, x + w, y + h // 2 + 2], fill=frame_color)


def draw_arched_window(draw, x, y, w, h, frame_color=BROWN, sky_color=SKY_BLUE):
    """Draw an arched window."""
    draw.rectangle([x - 4, y, x + w + 4, y + h + 4], fill=frame_color)
    draw.rectangle([x, y, x + w, y + h], fill=sky_color)
    # Arch top
    draw.pieslice([x - 4, y - h // 3, x + w + 4, y + h // 3], 180, 360, fill=frame_color)
    draw.pieslice([x, y - h // 3 + 4, x + w, y + h // 3 + 4], 180, 360, fill=sky_color)


def draw_bookshelf(draw, x, y, w, h, shelf_color=BROWN):
    """Draw a bookshelf with colored books."""
    draw.rectangle([x, y, x + w, y + h], fill=shelf_color)
    book_colors = [CORAL_RED, NAVY, SAGE_GREEN, GOLD, LAVENDER, SKY_BLUE, SOFT_PINK, ORANGE]
    num_shelves = 4
    shelf_h = h // num_shelves
    for s in range(num_shelves):
        sy = y + s * shelf_h
        # Shelf plank
        draw.rectangle([x, sy + shelf_h - 6, x + w, sy + shelf_h], fill=DARK_BROWN)
        # Books on this shelf
        bx = x + 6
        book_i = 0
        while bx < x + w - 15:
            bw = 14 + (book_i * 3) % 10
            bh = shelf_h - 14 + (book_i * 5) % 8
            color = book_colors[(s * 3 + book_i) % len(book_colors)]
            draw_book_rect(draw, bx, sy + shelf_h - 6 - bh, bw, bh, color)
            bx += bw + 3
            book_i += 1


def draw_rolling_hills(draw, y_base, width, colors, heights):
    """Draw overlapping rounded hill shapes."""
    for i, (color, h) in enumerate(zip(colors, heights)):
        points = []
        for x in range(0, width + 20, 20):
            y_offset = h * math.sin(x * 0.003 + i * 1.5) + h * 0.5 * math.sin(x * 0.007 + i * 2.3)
            points.append((x, y_base - y_offset))
        points.append((width, y_base + 200))
        points.append((0, y_base + 200))
        draw.polygon(points, fill=color)


# ── Background generators ──

def bg_study(W=1920, H=1080):
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    # Floor
    draw.rectangle([0, H * 0.7, W, H], fill=LIGHT_WOOD)
    # Back wall
    draw.rectangle([0, 0, W, H * 0.7], fill=CREAM)
    # Window on right
    draw_window(draw, W - 350, 80, 200, 280, BROWN, SKY_BLUE)
    # Bookshelf on left
    draw_bookshelf(draw, 60, 60, 280, 500, BROWN)
    # Desk
    draw.rounded_rectangle([500, H * 0.55, W - 200, H * 0.65], radius=8, fill=BROWN)
    # Desk legs
    draw.rectangle([520, H * 0.65, 540, H * 0.82], fill=DARK_BROWN)
    draw.rectangle([W - 240, H * 0.65, W - 220, H * 0.82], fill=DARK_BROWN)
    return img


def bg_laboratory(W=1920, H=1080):
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    # Floor
    draw.rectangle([0, H * 0.72, W, H], fill=MEDIUM_GRAY)
    # Table
    draw.rounded_rectangle([200, H * 0.5, W - 200, H * 0.58], radius=6, fill=BROWN)
    draw.rectangle([240, H * 0.58, 270, H * 0.78], fill=DARK_BROWN)
    draw.rectangle([W - 270, H * 0.58, W - 240, H * 0.78], fill=DARK_BROWN)
    # Flask outlines on table
    # Erlenmeyer flask shape
    flask_x, flask_y = 600, int(H * 0.5)
    draw.polygon([(flask_x, flask_y - 120), (flask_x + 20, flask_y - 120),
                   (flask_x + 50, flask_y - 20), (flask_x - 30, flask_y - 20)], fill=PALE_BLUE)
    draw.rectangle([flask_x - 2, flask_y - 160, flask_x + 22, flask_y - 120], fill=PALE_BLUE)
    # Beaker
    bk_x = 900
    draw.rectangle([bk_x, flask_y - 100, bk_x + 60, flask_y - 20], fill=PALE_BLUE)
    # Round flask
    draw.ellipse([1150, flask_y - 130, 1230, flask_y - 50], fill=PALE_BLUE)
    draw.rectangle([1180, flask_y - 170, 1200, flask_y - 130], fill=PALE_BLUE)
    # Shelf with bottles on wall
    draw.rectangle([100, 80, 600, 90], fill=BROWN)
    bottle_colors = [CORAL_RED, SAGE_GREEN, GOLD, LAVENDER, SKY_BLUE]
    for i, c in enumerate(bottle_colors):
        bx = 120 + i * 90
        draw.rectangle([bx, 30, bx + 30, 80], fill=c)
        draw.rectangle([bx + 8, 15, bx + 22, 30], fill=c)
    # Shelf on right
    draw.rectangle([W - 500, 80, W - 100, 90], fill=BROWN)
    for i, c in enumerate(reversed(bottle_colors)):
        bx = W - 480 + i * 80
        draw.rectangle([bx, 35, bx + 28, 80], fill=c)
        draw.rectangle([bx + 8, 18, bx + 20, 35], fill=c)
    return img


def bg_chalkboard(W=1920, H=1080):
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    # Floor
    draw.rectangle([0, H * 0.85, W, H], fill=LIGHT_WOOD)
    # Chalkboard frame
    margin_x, margin_y = 120, 60
    draw.rectangle([margin_x - 12, margin_y - 12, W - margin_x + 12, H * 0.82 + 12], fill=BROWN)
    # Chalkboard
    draw.rectangle([margin_x, margin_y, W - margin_x, H * 0.82], fill=DARK_GREEN)
    # Chalk tray
    draw.rectangle([margin_x, H * 0.82, W - margin_x, H * 0.85], fill=DARK_BROWN)
    # Small chalk pieces on tray
    draw.rectangle([300, int(H * 0.82) + 4, 340, int(H * 0.82) + 12], fill=WHITE)
    draw.rectangle([360, int(H * 0.82) + 4, 390, int(H * 0.82) + 12], fill=GOLD)
    draw.rectangle([410, int(H * 0.82) + 4, 445, int(H * 0.82) + 12], fill=CORAL_RED)
    return img


def bg_electromagnetic(W=1920, H=1080):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    # Field lines — curved arcs in yellow and cyan
    cx, cy = W // 2, H // 2
    for i in range(6):
        r = 100 + i * 80
        draw.arc([cx - r, cy - r, cx + r, cy + r], 200, 340, fill=GOLD, width=3)
        draw.arc([cx - r, cy - r, cx + r, cy + r], 20, 160, fill=CYAN, width=3)
    # More field lines offset
    for i in range(4):
        r = 120 + i * 90
        draw.arc([cx - r - 300, cy - r, cx - 300 + r, cy + r], 210, 330, fill=GOLD, width=2)
        draw.arc([cx + 300 - r, cy - r, cx + 300 + r, cy + r], 210, 330, fill=CYAN, width=2)
    # Positive charge (red circle)
    draw.ellipse([cx - 25, cy - 25, cx + 25, cy + 25], fill=CORAL_RED)
    # Negative charges
    draw.ellipse([200, 300, 230, 330], fill=SKY_BLUE)
    draw.ellipse([W - 230, 400, W - 200, 430], fill=SKY_BLUE)
    draw.ellipse([400, 700, 430, 730], fill=CORAL_RED)
    draw.ellipse([W - 400, 200, W - 370, 230], fill=CORAL_RED)
    # Small scattered dots
    import random
    rng = random.Random(42)
    for _ in range(30):
        x = rng.randint(50, W - 50)
        y = rng.randint(50, H - 50)
        s = rng.randint(2, 5)
        c = rng.choice([GOLD, CYAN, CORAL_RED, SKY_BLUE])
        draw.ellipse([x - s, y - s, x + s, y + s], fill=c)
    return img


def bg_thermal(W=1920, H=1080):
    img = Image.new("RGB", (W, H), "#F5C518")
    draw = ImageDraw.Draw(img)
    # 4 horizontal flat bands from warm to hot
    bands = ["#F5C518", "#E8914A", "#E85D5D", "#C0392B"]
    band_h = H // len(bands)
    for i, color in enumerate(bands):
        draw.rectangle([0, i * band_h, W, (i + 1) * band_h], fill=color)
    # Scattered dots (heat particles)
    import random
    rng = random.Random(7)
    for _ in range(60):
        x = rng.randint(30, W - 30)
        y = rng.randint(30, H - 30)
        s = rng.randint(4, 10)
        c = rng.choice([WHITE, CREAM, GOLD, ORANGE])
        draw.ellipse([x - s, y - s, x + s, y + s], fill=c)
    return img


def bg_quantum(W=1920, H=1080):
    img = Image.new("RGB", (W, H), DEEP_PURPLE)
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    # Concentric orbital circles
    for i in range(8):
        r = 60 + i * 65
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=LAVENDER, width=2)
    # Bright dots on orbitals
    import random
    rng = random.Random(99)
    for i in range(8):
        r = 60 + i * 65
        angle = rng.uniform(0, 2 * math.pi)
        dx = int(r * math.cos(angle))
        dy = int(r * math.sin(angle))
        s = 6
        draw.ellipse([cx + dx - s, cy + dy - s, cx + dx + s, cy + dy + s], fill=GOLD)
    # Wave lines in pink across bottom
    for wave_y in [H * 0.75, H * 0.85]:
        points = []
        for x in range(0, W + 10, 10):
            y = int(wave_y + 20 * math.sin(x * 0.02))
            points.append((x, y))
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=SOFT_PINK, width=3)
    # Small bright scattered dots
    for _ in range(40):
        x = rng.randint(20, W - 20)
        y = rng.randint(20, H - 20)
        s = rng.randint(1, 4)
        draw.ellipse([x - s, y - s, x + s, y + s], fill=WHITE)
    return img


def bg_spacetime(W=1920, H=1080):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    # Grid lines curving downward in center
    grid_color = "#445577"
    # Horizontal lines
    for gy in range(0, H + 1, 60):
        points = []
        for gx in range(0, W + 10, 10):
            dist = math.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
            sag = max(0, 120 - dist * 0.15) if dist < 500 else 0
            points.append((gx, gy + sag))
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=grid_color, width=1)
    # Vertical lines
    for gx in range(0, W + 1, 60):
        points = []
        for gy in range(0, H + 10, 10):
            dist = math.sqrt((gx - cx) ** 2 + (gy - cy) ** 2)
            sag_x = 0
            sag_y = max(0, 120 - dist * 0.15) if dist < 500 else 0
            if dist < 500 and dist > 0:
                sag_x = (gx - cx) * 0.08 * max(0, 1 - dist / 500)
            points.append((gx - sag_x, gy + sag_y))
        for i in range(len(points) - 1):
            draw.line([points[i], points[i + 1]], fill=grid_color, width=1)
    # Orange mass at center
    draw.ellipse([cx - 35, cy - 35, cx + 35, cy + 35], fill=ORANGE)
    # Star dots
    import random
    rng = random.Random(55)
    for _ in range(50):
        x = rng.randint(20, W - 20)
        y = rng.randint(20, H - 20)
        if abs(x - cx) > 100 or abs(y - cy) > 100:
            s = rng.randint(1, 3)
            draw.ellipse([x - s, y - s, x + s, y + s], fill=GOLD)
    return img


def bg_workshop(W=1920, H=1080):
    img = Image.new("RGB", (W, H), WARM_BROWN)
    draw = ImageDraw.Draw(img)
    # Floor
    draw.rectangle([0, H * 0.72, W, H], fill=DARK_BROWN)
    # Workbench
    draw.rounded_rectangle([150, H * 0.55, W - 150, H * 0.63], radius=6, fill=WOOD_BROWN)
    draw.rectangle([180, H * 0.63, 210, H * 0.78], fill=DARK_BROWN)
    draw.rectangle([W - 210, H * 0.63, W - 180, H * 0.78], fill=DARK_BROWN)
    # Gears on wall
    for gx, gy, gr in [(300, 200, 50), (450, 150, 35), (1500, 180, 45), (1650, 230, 30)]:
        draw.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=MEDIUM_GRAY)
        draw.ellipse([gx - gr * 0.4, gy - gr * 0.4, gx + gr * 0.4, gy + gr * 0.4], fill=WARM_BROWN)
        # Gear teeth
        for a in range(0, 360, 30):
            tx = int(gx + gr * 0.9 * math.cos(math.radians(a)))
            ty = int(gy + gr * 0.9 * math.sin(math.radians(a)))
            draw.rectangle([tx - 5, ty - 5, tx + 5, ty + 5], fill=MEDIUM_GRAY)
    # Tool silhouettes on wall (hammer, wrench shapes)
    # Hammer
    draw.rectangle([800, 120, 810, 280], fill=DARK_BROWN)
    draw.rectangle([780, 100, 830, 135], fill=DARK_GRAY)
    # Wrench
    draw.rectangle([1000, 120, 1010, 300], fill=DARK_GRAY)
    draw.ellipse([985, 95, 1025, 135], fill=DARK_GRAY)
    # Saw
    draw.rectangle([1150, 130, 1250, 140], fill=DARK_GRAY)
    draw.polygon([(1150, 140), (1250, 140), (1250, 180), (1150, 160)], fill=MEDIUM_GRAY)
    return img


def bg_ocean(W=1920, H=1080):
    img = Image.new("RGB", (W, H), PALE_BLUE)
    draw = ImageDraw.Draw(img)
    # Sky top
    draw.rectangle([0, 0, W, H * 0.35], fill=SKY_BLUE)
    # Sun
    draw_sun(draw, W - 200, 150, 70, GOLD)
    # Clouds
    draw_cloud(draw, 300, 100, 60)
    draw_cloud(draw, 800, 140, 45)
    draw_cloud(draw, 1400, 80, 55)
    # Waves — overlapping rounded shapes in 3 blue shades
    wave_colors = ["#5BA3D9", "#3D8EC9", "#2C6FAA"]
    for i, color in enumerate(wave_colors):
        base_y = H * 0.35 + i * H * 0.18
        points = []
        for x in range(0, W + 30, 30):
            y = base_y + 30 * math.sin(x * 0.008 + i * 2) + 15 * math.sin(x * 0.015 + i)
            points.append((x, int(y)))
        points.append((W, H))
        points.append((0, H))
        draw.polygon(points, fill=color)
    # Deepest water at bottom
    draw.rectangle([0, H * 0.85, W, H], fill="#1A4A7A")
    return img


def bg_mountain(W=1920, H=1080):
    img = Image.new("RGB", (W, H), SKY_BLUE)
    draw = ImageDraw.Draw(img)
    # Clouds
    draw_cloud(draw, 250, 100, 50)
    draw_cloud(draw, 900, 70, 65)
    draw_cloud(draw, 1500, 120, 45)
    # Snow-capped mountain peaks (triangles)
    mountains = [(400, 200, 600), (960, 180, 700), (1500, 220, 550)]
    for mx, mtop, mw in mountains:
        # Mountain body
        draw.polygon([(mx - mw // 2, H * 0.65), (mx, mtop), (mx + mw // 2, H * 0.65)], fill=MEDIUM_GRAY)
        # Snow cap
        cap_h = 80
        cap_w = int(mw * 0.25)
        draw.polygon([(mx - cap_w, mtop + cap_h), (mx, mtop), (mx + cap_w, mtop + cap_h)], fill=WHITE)
    # Green rolling hills in foreground
    hill_colors = ["#6BA36E", SAGE_GREEN, "#8FC693"]
    for i, color in enumerate(hill_colors):
        base_y = H * 0.6 + i * H * 0.1
        points = []
        for x in range(0, W + 20, 20):
            y = base_y + 40 * math.sin(x * 0.004 + i * 2.5) + 20 * math.sin(x * 0.009 + i * 1.3)
            points.append((x, int(y)))
        points.append((W, H))
        points.append((0, H))
        draw.polygon(points, fill=color)
    return img


def bg_royal_society(W=1920, H=1080):
    img = Image.new("RGB", (W, H), DARK_BROWN)
    draw = ImageDraw.Draw(img)
    # Wood paneling — vertical rectangular panels
    panel_w = 160
    for i in range(W // panel_w + 1):
        x = i * panel_w
        col = DARK_BROWN if i % 2 == 0 else "#5A3F28"
        draw.rectangle([x, 0, x + panel_w, H], fill=col)
        # Panel border inset
        draw.rectangle([x + 6, 20, x + panel_w - 6, H - 20], outline="#6B4D35", width=2)
    # Floor
    draw.rectangle([0, H * 0.82, W, H], fill=DARK_WOOD)
    # Tall arched windows
    for wx in [300, 960, 1600]:
        draw_arched_window(draw, wx - 60, 80, 120, 400, DARK_WOOD, "#C5A040")
    # Warm golden tone overlay — horizontal band at top
    draw.rectangle([0, 0, W, 30], fill="#8B6914")
    draw.rectangle([0, H * 0.82, W, H * 0.84], fill="#8B6914")
    return img


def bg_university_lecture(W=1920, H=1080):
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    # Chalkboard on wall
    draw.rectangle([300, 40, W - 300, 380], fill=DARK_BROWN)
    draw.rectangle([310, 50, W - 310, 370], fill=DARK_GREEN)
    # Arched windows on sides
    draw_arched_window(draw, 50, 50, 120, 300, BROWN, SKY_BLUE)
    draw_arched_window(draw, W - 170, 50, 120, 300, BROWN, SKY_BLUE)
    # Tiered bench rows
    bench_colors = [BROWN, WOOD_BROWN, LIGHT_WOOD]
    for i in range(5):
        y = 420 + i * 130
        depth = 50 + i * 15
        shade = BROWN if i % 2 == 0 else WOOD_BROWN
        # Bench surface
        draw.rectangle([80 + i * 30, y, W - 80 - i * 30, y + 20], fill=shade)
        # Bench front
        draw.rectangle([80 + i * 30, y + 20, W - 80 - i * 30, y + 20 + depth], fill=DARK_BROWN)
    return img


def bg_particle_accelerator(W=1920, H=1080):
    img = Image.new("RGB", (W, H), DARK_GRAY)
    draw = ImageDraw.Draw(img)
    cx, cy = W // 2, H // 2
    # Circular tunnel shape
    outer_r = 420
    inner_r = 340
    draw.ellipse([cx - outer_r, cy - outer_r, cx + outer_r, cy + outer_r], fill=MEDIUM_GRAY)
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r], fill=DARK_GRAY)
    # Equipment along the ring
    import random
    rng = random.Random(33)
    for a in range(0, 360, 20):
        r = (outer_r + inner_r) // 2
        ex = int(cx + r * math.cos(math.radians(a)))
        ey = int(cy + r * math.sin(math.radians(a)))
        color = rng.choice([SKY_BLUE, GOLD, CORAL_RED, MEDIUM_GRAY])
        s = rng.randint(12, 20)
        draw.rectangle([ex - s, ey - s // 2, ex + s, ey + s // 2], fill=color)
    # Beam path highlight
    draw.ellipse([cx - (outer_r + inner_r) // 2, cy - (outer_r + inner_r) // 2,
                   cx + (outer_r + inner_r) // 2, cy + (outer_r + inner_r) // 2],
                  outline=CYAN, width=3)
    return img


def bg_patent_office(W=1920, H=1080):
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    # Floor
    draw.rectangle([0, H * 0.75, W, H], fill=LIGHT_WOOD)
    # Window
    draw_window(draw, W - 380, 80, 220, 320, BROWN, SKY_BLUE)
    # Desk
    draw.rounded_rectangle([400, H * 0.52, W - 350, H * 0.6], radius=8, fill=BROWN)
    draw.rectangle([430, H * 0.6, 460, H * 0.8], fill=DARK_BROWN)
    draw.rectangle([W - 400, H * 0.6, W - 370, H * 0.8], fill=DARK_BROWN)
    # Papers on desk
    paper_positions = [(500, int(H * 0.44)), (620, int(H * 0.46)), (750, int(H * 0.43)),
                       (900, int(H * 0.45)), (1050, int(H * 0.44))]
    for px, py in paper_positions:
        draw.rectangle([px, py, px + 60, py + 80], fill=WHITE)
        # Lines on paper
        for ly in range(py + 10, py + 70, 8):
            draw.line([(px + 8, ly), (px + 52, ly)], fill=LIGHT_GRAY, width=1)
    # Warm lamp glow (yellow circle)
    draw.ellipse([680, 120, 760, 200], fill=GOLD)
    draw.rectangle([710, 200, 730, 350], fill=DARK_BROWN)
    # Filing cabinet on left
    draw.rectangle([60, 200, 200, H * 0.75], fill=MEDIUM_GRAY)
    for fy in range(220, int(H * 0.73), 80):
        draw.rectangle([70, fy, 190, fy + 70], outline=DARK_GRAY, width=2)
        draw.ellipse([120, fy + 30, 140, fy + 40], fill=DARK_GRAY)
    return img


def bg_pisa_tower(W=1920, H=1080):
    img = Image.new("RGB", (W, H), SKY_BLUE)
    draw = ImageDraw.Draw(img)
    # Clouds
    draw_cloud(draw, 200, 100, 50)
    draw_cloud(draw, 1600, 80, 55)
    # Green hill
    points = []
    for x in range(0, W + 20, 20):
        y = H * 0.65 + 30 * math.sin(x * 0.003) + 20 * math.sin(x * 0.007)
        points.append((x, int(y)))
    points.append((W, H))
    points.append((0, H))
    draw.polygon(points, fill=SAGE_GREEN)
    # Tower — stacked white rectangles tilted slightly
    tower_x = W // 2 - 40
    tower_base = int(H * 0.62)
    tilt = 4  # pixels of tilt per level
    levels = 7
    level_h = 55
    level_w = 100
    for i in range(levels):
        x_offset = i * tilt
        y = tower_base - (i + 1) * level_h
        draw.rectangle([tower_x + x_offset, y, tower_x + x_offset + level_w, y + level_h - 4], fill=WHITE)
        # Small columns
        for col in range(0, level_w, 20):
            draw.rectangle([tower_x + x_offset + col + 4, y + 5,
                           tower_x + x_offset + col + 8, y + level_h - 8], fill=LIGHT_GRAY)
    # Top dome
    top_y = tower_base - (levels + 1) * level_h + 10
    top_x_off = levels * tilt
    draw.ellipse([tower_x + top_x_off + 20, top_y, tower_x + top_x_off + 80, top_y + 40], fill=WHITE)
    return img


def bg_observatory(W=1920, H=1080):
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    # Stars
    import random
    rng = random.Random(88)
    for _ in range(80):
        x = rng.randint(10, W - 10)
        y = rng.randint(10, int(H * 0.6))
        s = rng.randint(1, 3)
        draw.ellipse([x - s, y - s, x + s, y + s], fill=WHITE)
    # Ground
    draw.rectangle([0, H * 0.7, W, H], fill=DARK_GREEN)
    # Dome
    dome_cx = W // 2
    dome_base_y = int(H * 0.7)
    dome_r = 280
    draw.pieslice([dome_cx - dome_r, dome_base_y - dome_r, dome_cx + dome_r, dome_base_y + dome_r],
                   180, 360, fill=DARK_GRAY)
    # Dome slit/opening
    draw.rectangle([dome_cx - 20, dome_base_y - dome_r + 20, dome_cx + 20, dome_base_y], fill=NAVY)
    # Telescope silhouette poking out
    draw.polygon([(dome_cx, dome_base_y - dome_r + 30),
                   (dome_cx + 120, dome_base_y - dome_r - 60),
                   (dome_cx + 130, dome_base_y - dome_r - 50),
                   (dome_cx + 10, dome_base_y - dome_r + 40)], fill=DARK_GRAY)
    # Building base
    draw.rectangle([dome_cx - dome_r - 40, dome_base_y, dome_cx + dome_r + 40, H], fill="#3A3A3A")
    return img


def bg_library(W=1920, H=1080):
    img = Image.new("RGB", (W, H), WARM_BROWN)
    draw = ImageDraw.Draw(img)
    # Floor
    draw.rectangle([0, H * 0.88, W, H], fill=DARK_WOOD)
    # Tall bookshelves on both sides
    shelf_w = 350
    # Left bookshelf
    draw_bookshelf(draw, 30, 30, shelf_w, H * 0.85 - 30, BROWN)
    # Right bookshelf
    draw_bookshelf(draw, W - shelf_w - 30, 30, shelf_w, H * 0.85 - 30, BROWN)
    # Center aisle — slightly lighter
    draw.rectangle([shelf_w + 50, 0, W - shelf_w - 50, H * 0.88], fill="#B8956A")
    # Arched top (decorative arch in center)
    arch_cx = W // 2
    draw.pieslice([arch_cx - 250, -100, arch_cx + 250, 300], 0, 180, fill=WARM_BROWN)
    draw.pieslice([arch_cx - 220, -80, arch_cx + 220, 280], 0, 180, fill="#B8956A")
    # Center back shelf
    draw_bookshelf(draw, arch_cx - 180, 200, 360, H * 0.6, BROWN)
    return img


def bg_road_highway(W=1920, H=1080):
    img = Image.new("RGB", (W, H), SKY_BLUE)
    draw = ImageDraw.Draw(img)
    # Sky
    draw_cloud(draw, 400, 100, 55)
    draw_cloud(draw, 1200, 80, 50)
    # Green fields
    draw.rectangle([0, H * 0.45, W, H], fill=SAGE_GREEN)
    # Road
    road_top = int(H * 0.45)
    road_w = 300
    draw.rectangle([W // 2 - road_w // 2, road_top, W // 2 + road_w // 2, H], fill=DARK_GRAY)
    # White dashed center line
    for dy in range(road_top, H, 50):
        draw.rectangle([W // 2 - 4, dy, W // 2 + 4, dy + 25], fill=WHITE)
    # Road edges
    draw.rectangle([W // 2 - road_w // 2, road_top, W // 2 - road_w // 2 + 6, H], fill=WHITE)
    draw.rectangle([W // 2 + road_w // 2 - 6, road_top, W // 2 + road_w // 2, H], fill=WHITE)
    return img


def bg_desert(W=1920, H=1080):
    img = Image.new("RGB", (W, H), SKY_BLUE)
    draw = ImageDraw.Draw(img)
    # Sun
    draw_sun(draw, W - 250, 180, 80, GOLD)
    # Dune shapes — overlapping rounded forms
    dune_colors = ["#D4B896", "#C4A882", "#B89870", "#A8885E"]
    for i, color in enumerate(dune_colors):
        base_y = H * 0.4 + i * H * 0.13
        points = []
        for x in range(0, W + 30, 30):
            y = base_y + 60 * math.sin(x * 0.003 + i * 1.8) + 30 * math.sin(x * 0.008 + i * 0.7)
            points.append((x, int(y)))
        points.append((W, H))
        points.append((0, H))
        draw.polygon(points, fill=color)
    return img


def bg_sunset(W=1920, H=1080):
    img = Image.new("RGB", (W, H), "#FFD700")
    draw = ImageDraw.Draw(img)
    # Horizontal flat bands
    bands = [("#FFD700", 0, 0.2), ("#FFA500", 0.2, 0.4), ("#FF6B4A", 0.4, 0.55),
             ("#E85D5D", 0.55, 0.7), (SOFT_PINK, 0.7, 0.75)]
    for color, start, end in bands:
        draw.rectangle([0, int(H * start), W, int(H * end)], fill=color)
    # Large sun
    draw_sun(draw, W // 2, int(H * 0.45), 100, "#FFE066")
    # Dark hill silhouette
    points = []
    for x in range(0, W + 20, 20):
        y = H * 0.72 + 40 * math.sin(x * 0.005) + 25 * math.sin(x * 0.012)
        points.append((x, int(y)))
    points.append((W, H))
    points.append((0, H))
    draw.polygon(points, fill="#2A1A0A")
    # Ground
    draw.rectangle([0, int(H * 0.85), W, H], fill="#1A1008")
    return img


def bg_city_skyline(W=1920, H=1080):
    img = Image.new("RGB", (W, H), "#F5C5A0")
    draw = ImageDraw.Draw(img)
    # Pale orange sky with slight color variation
    draw.rectangle([0, 0, W, int(H * 0.3)], fill="#F5D5B0")
    # Building silhouettes
    import random
    rng = random.Random(21)
    buildings = []
    x = 0
    while x < W:
        bw = rng.randint(60, 160)
        bh = rng.randint(200, 600)
        buildings.append((x, bh, bw))
        x += bw + rng.randint(0, 20)
    for bx, bh, bw in buildings:
        by = H - bh
        shade = rng.choice([DARK_GRAY, "#3A3A3A", "#505050", "#2A2A2A"])
        draw.rectangle([bx, by, bx + bw, H], fill=shade)
        # Window dots
        for wy in range(by + 15, H - 15, 25):
            for wx in range(bx + 10, bx + bw - 10, 18):
                if rng.random() > 0.3:
                    draw.rectangle([wx, wy, wx + 8, wy + 10], fill=GOLD)
    return img


def bg_underwater(W=1920, H=1080):
    img = Image.new("RGB", (W, H), "#0A2A4A")
    draw = ImageDraw.Draw(img)
    # Color bands from dark bottom to lighter top
    bands = [("#2A7AB5", 0, 0.15), ("#1E6A9E", 0.15, 0.35),
             ("#155A88", 0.35, 0.6), ("#0E4A72", 0.6, 0.8), ("#0A2A4A", 0.8, 1.0)]
    for color, start, end in bands:
        draw.rectangle([0, int(H * start), W, int(H * end)], fill=color)
    # Seaweed from bottom
    import random
    rng = random.Random(66)
    seaweed_colors = [SAGE_GREEN, DARK_GREEN, "#4A8B55"]
    for _ in range(12):
        sx = rng.randint(50, W - 50)
        color = rng.choice(seaweed_colors)
        # Draw wavy seaweed
        sw_h = rng.randint(150, 350)
        for sy in range(H, H - sw_h, -8):
            offset = 15 * math.sin((H - sy) * 0.03 + sx * 0.01)
            draw.ellipse([sx + offset - 6, sy - 4, sx + offset + 6, sy + 4], fill=color)
    # Bubble circles
    for _ in range(25):
        bx = rng.randint(30, W - 30)
        by = rng.randint(50, H - 100)
        br = rng.randint(5, 18)
        draw.ellipse([bx - br, by - br, bx + br, by + br], outline=WHITE, width=2)
    # Sandy bottom
    draw.rectangle([0, H - 40, W, H], fill=TAN)
    return img


def bg_factory(W=1920, H=1080):
    img = Image.new("RGB", (W, H), LIGHT_GRAY)
    draw = ImageDraw.Draw(img)
    # Walls
    draw.rectangle([0, 0, W, H * 0.85], fill=MEDIUM_GRAY)
    # Floor
    draw.rectangle([0, H * 0.85, W, H], fill=DARK_GRAY)
    # High windows
    for wx in range(100, W - 100, 300):
        draw.rectangle([wx, 40, wx + 150, 180], fill=PALE_BLUE)
        draw.rectangle([wx + 72, 40, wx + 78, 180], fill=MEDIUM_GRAY)
        draw.rectangle([wx, 107, wx + 150, 113], fill=MEDIUM_GRAY)
    # Pipes along walls
    pipe_y_positions = [250, 300, 350]
    for py in pipe_y_positions:
        draw.rectangle([0, py, W, py + 20], fill="#6A6A6A")
        # Joints
        for jx in range(0, W, 200):
            draw.ellipse([jx - 5, py - 5, jx + 25, py + 25], fill="#5A5A5A")
    # Gears
    for gx, gy, gr in [(400, 550, 60), (550, 520, 40), (1400, 560, 55), (1520, 530, 35)]:
        draw.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill="#7A7A7A")
        draw.ellipse([gx - gr * 0.35, gy - gr * 0.35, gx + gr * 0.35, gy + gr * 0.35], fill=MEDIUM_GRAY)
        for a in range(0, 360, 30):
            tx = int(gx + gr * 0.85 * math.cos(math.radians(a)))
            ty = int(gy + gr * 0.85 * math.sin(math.radians(a)))
            draw.rectangle([tx - 6, ty - 6, tx + 6, ty + 6], fill="#7A7A7A")
    return img


def bg_train_station(W=1920, H=1080):
    img = Image.new("RGB", (W, H), PALE_BLUE)
    draw = ImageDraw.Draw(img)
    # Arched roof structure
    draw.pieslice([-200, -400, W + 200, 800], 0, 180, fill=LIGHT_GRAY)
    draw.pieslice([-150, -350, W + 150, 750], 0, 180, fill=PALE_BLUE)
    # Roof beams
    for bx in range(100, W, 200):
        draw.line([(bx, 0), (W // 2, -100)], fill=MEDIUM_GRAY, width=4)
    # Platform
    draw.rectangle([0, H * 0.65, W, H * 0.7], fill=MEDIUM_GRAY)
    draw.rectangle([0, H * 0.7, W, H], fill=DARK_GRAY)
    # Track lines
    for ty in [H * 0.72, H * 0.74]:
        draw.rectangle([0, int(ty), W, int(ty) + 4], fill="#5A5A5A")
    # Sleepers
    for sx in range(0, W, 40):
        draw.rectangle([sx, int(H * 0.71), sx + 20, int(H * 0.75)], fill=DARK_BROWN)
    # Second set of tracks
    for ty in [H * 0.85, H * 0.87]:
        draw.rectangle([0, int(ty), W, int(ty) + 4], fill="#5A5A5A")
    for sx in range(0, W, 40):
        draw.rectangle([sx, int(H * 0.84), sx + 20, int(H * 0.88)], fill=DARK_BROWN)
    # Clock on wall
    clock_cx, clock_cy = W // 2, 200
    draw.ellipse([clock_cx - 50, clock_cy - 50, clock_cx + 50, clock_cy + 50], fill=WHITE)
    draw.ellipse([clock_cx - 45, clock_cy - 45, clock_cx + 45, clock_cy + 45], outline=DARK_GRAY, width=3)
    # Clock hands
    draw.line([(clock_cx, clock_cy), (clock_cx, clock_cy - 30)], fill=DARK_GRAY, width=3)
    draw.line([(clock_cx, clock_cy), (clock_cx + 20, clock_cy + 5)], fill=DARK_GRAY, width=2)
    return img


def bg_garden(W=1920, H=1080):
    img = Image.new("RGB", (W, H), SKY_BLUE)
    draw = ImageDraw.Draw(img)
    # Sky
    draw_cloud(draw, 350, 90, 50)
    draw_cloud(draw, 1400, 70, 60)
    # Ground
    draw.rectangle([0, H * 0.4, W, H], fill=SAGE_GREEN)
    # Gravel paths (cross pattern)
    path_color = "#D4C8A8"
    draw.rectangle([W // 2 - 40, int(H * 0.4), W // 2 + 40, H], fill=path_color)
    draw.rectangle([0, int(H * 0.6), W, int(H * 0.6) + 60], fill=path_color)
    # Hedge rectangles
    hedge_color = "#4A8B55"
    # Left garden bed
    draw.rounded_rectangle([80, int(H * 0.45), W // 2 - 60, int(H * 0.58)], radius=10, fill=hedge_color)
    # Right garden bed
    draw.rounded_rectangle([W // 2 + 60, int(H * 0.45), W - 80, int(H * 0.58)], radius=10, fill=hedge_color)
    # Lower beds
    draw.rounded_rectangle([80, int(H * 0.66), W // 2 - 60, int(H * 0.85)], radius=10, fill=hedge_color)
    draw.rounded_rectangle([W // 2 + 60, int(H * 0.66), W - 80, int(H * 0.85)], radius=10, fill=hedge_color)
    # Simple flower circles
    import random
    rng = random.Random(12)
    flower_colors = [CORAL_RED, GOLD, SOFT_PINK, LAVENDER, WHITE]
    for bed in [(100, int(H * 0.47), W // 2 - 80, int(H * 0.56)),
                (W // 2 + 80, int(H * 0.47), W - 100, int(H * 0.56)),
                (100, int(H * 0.68), W // 2 - 80, int(H * 0.83)),
                (W // 2 + 80, int(H * 0.68), W - 100, int(H * 0.83))]:
        for _ in range(15):
            fx = rng.randint(bed[0], bed[2])
            fy = rng.randint(bed[1], bed[3])
            fr = rng.randint(6, 12)
            fc = rng.choice(flower_colors)
            draw.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=fc)
            # Center dot
            draw.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=GOLD)
    return img


def bg_cave(W=1920, H=1080):
    img = Image.new("RGB", (W, H), "#2A1F1A")
    draw = ImageDraw.Draw(img)
    # Cave walls — dark rounded shapes
    draw.rectangle([0, 0, W, H], fill="#3A2F25")
    # Lighter interior
    draw.ellipse([-200, -100, W + 200, H + 200], fill="#4A3F30")
    draw.ellipse([100, 50, W - 100, H + 100], fill="#5A4F3A")
    # Stalactites from top
    import random
    rng = random.Random(44)
    for _ in range(15):
        sx = rng.randint(100, W - 100)
        sw = rng.randint(15, 35)
        sh = rng.randint(60, 200)
        draw.polygon([(sx - sw, 0), (sx + sw, 0), (sx, sh)], fill="#3A2F25")
    # Stalagmites from bottom
    for _ in range(10):
        sx = rng.randint(100, W - 100)
        sw = rng.randint(15, 30)
        sh = rng.randint(40, 120)
        draw.polygon([(sx - sw, H), (sx + sw, H), (sx, H - sh)], fill="#3A2F25")
    # Blue water pool at bottom
    draw.ellipse([W // 2 - 350, H - 200, W // 2 + 350, H + 60], fill="#2A5A8A")
    draw.ellipse([W // 2 - 300, H - 170, W // 2 + 300, H + 40], fill="#3A7AAA")
    # Orange torch glow on left wall
    draw.ellipse([100, 250, 300, 450], fill="#8B5A2A")
    draw.ellipse([140, 290, 260, 410], fill=ORANGE)
    draw.ellipse([170, 310, 230, 380], fill=GOLD)
    # Torch stick
    draw.rectangle([192, 380, 208, 500], fill=DARK_BROWN)
    return img


def bg_pantheon(W=1920, H=1080):
    img = Image.new("RGB", (W, H), CREAM)
    draw = ImageDraw.Draw(img)
    # Circular room feel — darker edges
    draw.rectangle([0, 0, W, H], fill="#D4C8B0")
    # Floor
    draw.rectangle([0, H * 0.75, W, H], fill="#B0A08A")
    # Floor pattern
    draw.ellipse([W // 2 - 400, int(H * 0.75), W // 2 + 400, H + 200], fill="#C4B89A")
    # Domed ceiling arc
    draw.pieslice([-200, -500, W + 200, 700], 0, 180, fill="#C8BCA6")
    draw.pieslice([-100, -450, W + 100, 650], 0, 180, fill="#D4C8B0")
    # Oculus (circle at top) with light beam
    oculus_cx = W // 2
    oculus_cy = 80
    oculus_r = 80
    draw.ellipse([oculus_cx - oculus_r, oculus_cy - oculus_r,
                   oculus_cx + oculus_r, oculus_cy + oculus_r], fill=SKY_BLUE)
    # Light beam from oculus
    draw.polygon([(oculus_cx - 60, oculus_cy + oculus_r),
                   (oculus_cx + 60, oculus_cy + oculus_r),
                   (oculus_cx + 200, H * 0.75),
                   (oculus_cx - 200, H * 0.75)], fill="#E8E0C8")
    # Column rectangles along walls
    for cx_pos in [150, 380, 610, W - 150, W - 380, W - 610]:
        draw.rectangle([cx_pos - 25, 200, cx_pos + 25, int(H * 0.75)], fill="#B8AC96")
        # Column cap
        draw.rectangle([cx_pos - 35, 190, cx_pos + 35, 210], fill="#A89C86")
        # Column base
        draw.rectangle([cx_pos - 35, int(H * 0.73), cx_pos + 35, int(H * 0.75)], fill="#A89C86")
    return img


def bg_billiard_hall(W=1920, H=1080):
    img = Image.new("RGB", (W, H), DARK_BROWN)
    draw = ImageDraw.Draw(img)
    # Warm brown walls
    draw.rectangle([0, 0, W, H * 0.3], fill="#5A3F28")
    # Floor
    draw.rectangle([0, H * 0.3, W, H], fill=BROWN)
    # Green billiard table centered
    table_margin_x = 350
    table_margin_y_top = int(H * 0.35)
    table_margin_y_bot = int(H * 0.85)
    # Table frame (brown border)
    draw.rounded_rectangle([table_margin_x - 20, table_margin_y_top - 20,
                             W - table_margin_x + 20, table_margin_y_bot + 20],
                            radius=12, fill=DARK_BROWN)
    # Green felt
    draw.rounded_rectangle([table_margin_x, table_margin_y_top,
                             W - table_margin_x, table_margin_y_bot],
                            radius=8, fill="#2D7A3D")
    # Pockets (dark circles at corners and sides)
    pockets = [(table_margin_x + 10, table_margin_y_top + 10),
               (W - table_margin_x - 10, table_margin_y_top + 10),
               (table_margin_x + 10, table_margin_y_bot - 10),
               (W - table_margin_x - 10, table_margin_y_bot - 10),
               (W // 2, table_margin_y_top + 5),
               (W // 2, table_margin_y_bot - 5)]
    for px, py in pockets:
        draw.ellipse([px - 18, py - 18, px + 18, py + 18], fill="#1A1A1A")
    # Table legs
    for lx in [table_margin_x + 30, W - table_margin_x - 30]:
        for ly in [table_margin_y_bot + 20]:
            draw.rectangle([lx - 10, ly, lx + 10, ly + 80], fill=DARK_WOOD)
    # Hanging lamp above table
    lamp_cx = W // 2
    lamp_y = 80
    draw.rectangle([lamp_cx - 3, 0, lamp_cx + 3, lamp_y], fill=DARK_GRAY)
    draw.polygon([(lamp_cx - 80, lamp_y), (lamp_cx + 80, lamp_y),
                   (lamp_cx + 50, lamp_y + 40), (lamp_cx - 50, lamp_y + 40)], fill=GOLD)
    # Light cone (subtle)
    draw.polygon([(lamp_cx - 60, lamp_y + 40), (lamp_cx + 60, lamp_y + 40),
                   (lamp_cx + 200, table_margin_y_top), (lamp_cx - 200, table_margin_y_top)],
                  fill="#3D8A4D")
    return img


# ── Vertical variants (1080x1920) ──

def bg_grass_field_vertical():
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), SKY_BLUE)
    draw = ImageDraw.Draw(img)
    # Clouds
    draw_cloud(draw, 250, 150, 55)
    draw_cloud(draw, 750, 100, 45)
    draw_cloud(draw, 500, 250, 50)
    # Sun
    draw_sun(draw, W - 150, 120, 60, GOLD)
    # Rolling green hills
    hill_data = [(SAGE_GREEN, H * 0.45, 50), ("#6BA36E", H * 0.5, 40), ("#8FC693", H * 0.55, 35)]
    for color, base_y, amp in hill_data:
        points = []
        for x in range(0, W + 20, 20):
            y = base_y + amp * math.sin(x * 0.006) + amp * 0.5 * math.sin(x * 0.014)
            points.append((x, int(y)))
        points.append((W, H))
        points.append((0, H))
        draw.polygon(points, fill=color)
    # Simple flowers
    import random
    rng = random.Random(77)
    for _ in range(20):
        fx = rng.randint(30, W - 30)
        fy = rng.randint(int(H * 0.6), H - 50)
        fr = rng.randint(6, 12)
        fc = rng.choice([CORAL_RED, GOLD, SOFT_PINK, LAVENDER, WHITE])
        draw.ellipse([fx - fr, fy - fr, fx + fr, fy + fr], fill=fc)
        draw.ellipse([fx - 3, fy - 3, fx + 3, fy + 3], fill=GOLD)
    return img


def bg_outer_space_vertical():
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), NAVY)
    draw = ImageDraw.Draw(img)
    # Star dots
    import random
    rng = random.Random(42)
    for _ in range(120):
        x = rng.randint(5, W - 5)
        y = rng.randint(5, H - 5)
        s = rng.randint(1, 3)
        draw.ellipse([x - s, y - s, x + s, y + s], fill=rng.choice([WHITE, GOLD, PALE_BLUE]))
    # Crescent moon
    moon_cx, moon_cy = 300, 400
    moon_r = 80
    draw.ellipse([moon_cx - moon_r, moon_cy - moon_r, moon_cx + moon_r, moon_cy + moon_r], fill=CREAM)
    draw.ellipse([moon_cx - moon_r + 30, moon_cy - moon_r - 10,
                   moon_cx + moon_r + 30, moon_cy + moon_r - 10], fill=NAVY)
    # A planet
    draw.ellipse([700, 1200, 820, 1320], fill=CORAL_RED)
    draw.ellipse([710, 1210, 810, 1310], fill="#C04040")
    # Another small planet
    draw.ellipse([150, 1500, 210, 1560], fill=SAGE_GREEN)
    return img


def bg_ice_rink_vertical():
    W, H = 1080, 1920
    img = Image.new("RGB", (W, H), PALE_BLUE)
    draw = ImageDraw.Draw(img)
    # Sky at top
    draw.rectangle([0, 0, W, int(H * 0.3)], fill=SKY_BLUE)
    # White/blue hills
    hill_data = [(WHITE, H * 0.25, 50), (PALE_BLUE, H * 0.3, 40), ("#B0D8E8", H * 0.35, 30)]
    for color, base_y, amp in hill_data:
        points = []
        for x in range(0, W + 20, 20):
            y = base_y + amp * math.sin(x * 0.007 + 1) + amp * 0.4 * math.sin(x * 0.015)
            points.append((x, int(y)))
        points.append((W, H))
        points.append((0, H))
        draw.polygon(points, fill=color)
    # Ice surface
    draw.rectangle([0, int(H * 0.4), W, H], fill="#D8EEF8")
    # Ice surface lines
    for ly in range(int(H * 0.4), H, 80):
        draw.line([(0, ly), (W, ly)], fill="#C8DEE8", width=1)
    # Snowflakes
    import random
    rng = random.Random(55)
    for _ in range(30):
        sx = rng.randint(20, W - 20)
        sy = rng.randint(20, int(H * 0.5))
        ss = rng.randint(3, 8)
        # Simple snowflake = small cross
        draw.line([(sx - ss, sy), (sx + ss, sy)], fill=WHITE, width=2)
        draw.line([(sx, sy - ss), (sx, sy + ss)], fill=WHITE, width=2)
        draw.line([(sx - ss + 2, sy - ss + 2), (sx + ss - 2, sy + ss - 2)], fill=WHITE, width=1)
        draw.line([(sx + ss - 2, sy - ss + 2), (sx - ss + 2, sy + ss - 2)], fill=WHITE, width=1)
    return img


# ── Main ──

BACKGROUNDS = {
    "bg_study": bg_study,
    "bg_laboratory": bg_laboratory,
    "bg_chalkboard": bg_chalkboard,
    "bg_electromagnetic": bg_electromagnetic,
    "bg_thermal": bg_thermal,
    "bg_quantum": bg_quantum,
    "bg_spacetime": bg_spacetime,
    "bg_workshop": bg_workshop,
    "bg_ocean": bg_ocean,
    "bg_mountain": bg_mountain,
    "bg_royal_society": bg_royal_society,
    "bg_university_lecture": bg_university_lecture,
    "bg_particle_accelerator": bg_particle_accelerator,
    "bg_patent_office": bg_patent_office,
    "bg_pisa_tower": bg_pisa_tower,
    "bg_observatory": bg_observatory,
    "bg_library": bg_library,
    "bg_road_highway": bg_road_highway,
    "bg_desert": bg_desert,
    "bg_sunset": bg_sunset,
    "bg_city_skyline": bg_city_skyline,
    "bg_underwater": bg_underwater,
    "bg_factory": bg_factory,
    "bg_train_station": bg_train_station,
    "bg_garden": bg_garden,
    "bg_cave": bg_cave,
    "bg_pantheon": bg_pantheon,
    "bg_billiard_hall": bg_billiard_hall,
    "bg_grass_field_vertical": bg_grass_field_vertical,
    "bg_outer_space_vertical": bg_outer_space_vertical,
    "bg_ice_rink_vertical": bg_ice_rink_vertical,
}


def main():
    ensure_output_dir()
    print(f"Generating {len(BACKGROUNDS)} backgrounds to {OUTPUT_DIR}/")
    for name, func in BACKGROUNDS.items():
        path = os.path.join(OUTPUT_DIR, f"{name}.png")
        img = func()
        img.save(path, "PNG")
        print(f"  [{img.size[0]}x{img.size[1]}] {name}.png")
    print(f"\nDone! {len(BACKGROUNDS)} backgrounds generated.")


if __name__ == "__main__":
    main()
