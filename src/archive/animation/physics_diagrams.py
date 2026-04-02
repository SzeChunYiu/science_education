"""
physics_diagrams.py — Programmatic physics diagram renderer using Pillow.

Generates clean, educational physics diagrams as PIL Images that can be
composited into scene timelines. All drawing is algorithmic — no external
assets required.

Diagram types
-------------
force_diagram(forces, object_label)
    Free-body diagram with labeled force vectors from object centre.

motion_diagram(positions, labels)
    Sequence of object positions with velocity/acceleration arrows.

energy_diagram(before, after, labels)
    Before/after energy bar chart (KE + PE).

spring_diagram(compressed, labels)
    Mass-spring system.

inclined_plane(angle_deg, forces)
    Object on inclined plane with force components.

Usage
-----
    from src.animation.physics_diagrams import PhysicsDiagramRenderer
    r = PhysicsDiagramRenderer(width=1600, height=900)
    img = r.force_diagram(
        forces=[("F", "right", 280, "#E8734A"),
                ("f", "left",  120, "#4A90D9"),
                ("N", "up",    200, "#50BFA5"),
                ("W", "down",  200, "#9B59B6")],
        object_label="m",
    )
    img.save("force_diagram.png")
"""

from __future__ import annotations

import math
from typing import Optional
from PIL import Image, ImageDraw, ImageFont
import os


# ---------------------------------------------------------------------------
# Colour palette (flat, bold, educational)
# ---------------------------------------------------------------------------
_P = {
    "bg":       "#FFFDF7",   # warm off-white
    "ink":      "#1C1C1E",   # near-black
    "ground":   "#3D2B1F",   # dark brown ground line
    "object":   "#F5C97A",   # warm amber — the mass/object
    "object_outline": "#1C1C1E",
    "red":      "#E8503A",
    "blue":     "#3A7BD5",
    "green":    "#27AE60",
    "purple":   "#8E44AD",
    "orange":   "#E67E22",
    "teal":     "#16A085",
    "gray":     "#7F8C8D",
    "panel":    "#FFFFFF",
    "panel_border": "#D0CCC4",
}

_DIR_ANGLES = {
    "right":      0,
    "left":     180,
    "up":       -90,   # PIL y increases downward
    "down":      90,
    "up-right":  -45,
    "up-left":  -135,
    "down-right": 45,
    "down-left": 135,
}

_FORCE_COLORS = ["#E8503A", "#3A7BD5", "#27AE60", "#8E44AD", "#E67E22", "#16A085"]


def _hex(c: str) -> tuple[int, int, int]:
    c = c.lstrip("#")
    return int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Supplemental/Verdana Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    ]
    for c in candidates:
        if os.path.isfile(c):
            try:
                return ImageFont.truetype(c, size)
            except Exception:
                continue
    return ImageFont.load_default()


class PhysicsDiagramRenderer:
    """
    Renders physics diagrams as PIL RGBA images.

    Parameters
    ----------
    width, height : int
        Canvas size in pixels. Default 1600×900 (16:9).
    bg_color : str
        Hex background color.
    """

    def __init__(
        self,
        width: int = 1600,
        height: int = 900,
        bg_color: str = _P["bg"],
    ) -> None:
        self.w = width
        self.h = height
        self.bg_color = bg_color

    # ------------------------------------------------------------------
    # Public diagram factories
    # ------------------------------------------------------------------

    def force_diagram(
        self,
        forces: list[tuple[str, str, float, str]],
        object_label: str = "m",
        title: str = "Free-Body Diagram",
        subtitle: str = "",
        show_ground: bool = True,
    ) -> Image.Image:
        """
        Draw a free-body diagram with labeled force vectors.

        Parameters
        ----------
        forces : list of (label, direction, magnitude, color)
            direction is one of: "right","left","up","down",
                                  "up-right","up-left","down-right","down-left"
            magnitude is the arrow length in pixels (scaled internally).
            color is a hex string like "#E8503A".
        object_label : str
            Label drawn inside the central object (e.g. "m" or "box").
        title : str
            Diagram title shown at the top.
        subtitle : str
            Optional subtitle/caption below title.
        show_ground : bool
            Whether to draw a ground line below the object.
        """
        img = Image.new("RGBA", (self.w, self.h), _hex(self.bg_color) + (255,))
        draw = ImageDraw.Draw(img)

        # Fonts
        font_title    = _load_font(52)
        font_subtitle = _load_font(34)
        font_label    = _load_font(44)  # arrow labels
        font_obj      = _load_font(56)  # object centre label

        # Title
        draw.text((80, 60), title, font=font_title, fill=_hex(_P["ink"]))
        if subtitle:
            draw.text((80, 125), subtitle, font=font_subtitle, fill=_hex(_P["gray"]))

        # Object position — centred slightly above mid-height
        cx = self.w // 2
        cy = int(self.h * 0.55)
        obj_r = int(min(self.w, self.h) * 0.09)   # radius

        # Ground line
        if show_ground:
            ground_y = cy + obj_r + 20
            draw.line(
                [(cx - self.w // 3, ground_y), (cx + self.w // 3, ground_y)],
                fill=_hex(_P["ground"]), width=8,
            )
            # Hatching below ground
            hatch_gap = 28
            for x in range(cx - self.w // 3, cx + self.w // 3, hatch_gap):
                draw.line(
                    [(x, ground_y), (x - 18, ground_y + 22)],
                    fill=_hex(_P["ground"]), width=3,
                )

        # Force arrows (drawn before object so object sits on top)
        for i, (label, direction, magnitude, color) in enumerate(forces):
            angle_deg = _DIR_ANGLES.get(direction, 0)
            self._draw_force_arrow(
                draw, cx, cy, angle_deg, magnitude, label, color,
                font_label, obj_r,
            )

        # Object circle
        draw.ellipse(
            [cx - obj_r, cy - obj_r, cx + obj_r, cy + obj_r],
            fill=_hex(_P["object"]),
            outline=_hex(_P["object_outline"]),
            width=5,
        )
        # Object label centred inside
        bbox = draw.textbbox((0, 0), object_label, font=font_obj)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text(
            (cx - tw // 2, cy - th // 2 - 4),
            object_label, font=font_obj, fill=_hex(_P["ink"]),
        )

        return img

    def motion_diagram(
        self,
        n_positions: int = 5,
        accelerating: bool = True,
        title: str = "Motion Diagram",
    ) -> Image.Image:
        """Draw equally spaced (constant v) or unevenly spaced (accelerating) dots."""
        img = Image.new("RGBA", (self.w, self.h), _hex(self.bg_color) + (255,))
        draw = ImageDraw.Draw(img)
        font_title = _load_font(52)
        font_label = _load_font(36)

        draw.text((80, 60), title, font=font_title, fill=_hex(_P["ink"]))

        y = self.h // 2
        margin = self.w // 6
        usable = self.w - 2 * margin

        # Positions: uniform or quadratically spaced
        if accelerating:
            xs = [margin + int(usable * (i / (n_positions - 1)) ** 1.7)
                  for i in range(n_positions)]
        else:
            xs = [margin + int(usable * i / (n_positions - 1))
                  for i in range(n_positions)]

        r = 22
        for i, x in enumerate(xs):
            draw.ellipse([x - r, y - r, x + r, y + r],
                         fill=_hex(_P["blue"]), outline=_hex(_P["ink"]), width=3)

        # Velocity arrows between dots
        for i in range(len(xs) - 1):
            x1, x2 = xs[i] + r, xs[i + 1] - r
            mid_x = (x1 + x2) // 2
            if x2 > x1 + 10:
                self._draw_arrow_h(draw, x1 + 5, x2 - 5, y - 55, _P["red"], 4)
                v_label = f"v{i+1}"
                draw.text((mid_x - 15, y - 100), v_label,
                          font=font_label, fill=_hex(_P["red"]))

        # Direction label
        draw.text((margin, y + 60), "→ direction of motion",
                  font=font_label, fill=_hex(_P["gray"]))

        return img

    def energy_bar_diagram(
        self,
        ke_before: float,
        pe_before: float,
        ke_after: float,
        pe_after: float,
        title: str = "Energy Conservation",
    ) -> Image.Image:
        """Side-by-side KE/PE bar charts for before and after."""
        img = Image.new("RGBA", (self.w, self.h), _hex(self.bg_color) + (255,))
        draw = ImageDraw.Draw(img)
        font_title = _load_font(52)
        font_label = _load_font(38)
        font_val   = _load_font(32)

        draw.text((80, 60), title, font=font_title, fill=_hex(_P["ink"]))

        total = max(ke_before + pe_before, ke_after + pe_after, 1)
        max_h = int(self.h * 0.55)
        bar_w = 110
        base_y = int(self.h * 0.82)

        for col_i, (label, ke, pe) in enumerate([
            ("Before", ke_before, pe_before),
            ("After",  ke_after,  pe_after),
        ]):
            base_x = self.w // 4 + col_i * self.w // 2 - bar_w

            # KE bar (red)
            ke_h = int(max_h * ke / total)
            draw.rectangle(
                [base_x, base_y - ke_h, base_x + bar_w, base_y],
                fill=_hex(_P["red"]), outline=_hex(_P["ink"]), width=3,
            )
            draw.text((base_x + 10, base_y - ke_h - 44),
                      f"KE={ke:.0f}J", font=font_val, fill=_hex(_P["red"]))

            # PE bar (blue) stacked
            pe_h = int(max_h * pe / total)
            draw.rectangle(
                [base_x + bar_w + 16, base_y - pe_h, base_x + 2 * bar_w + 16, base_y],
                fill=_hex(_P["blue"]), outline=_hex(_P["ink"]), width=3,
            )
            draw.text((base_x + bar_w + 20, base_y - pe_h - 44),
                      f"PE={pe:.0f}J", font=font_val, fill=_hex(_P["blue"]))

            # Column label
            draw.text((base_x + 10, base_y + 18), label,
                      font=font_label, fill=_hex(_P["ink"]))

        # Baseline
        draw.line([(self.w // 8, base_y), (self.w * 7 // 8, base_y)],
                  fill=_hex(_P["ink"]), width=4)

        return img

    def energy_diagram(
        self,
        before: tuple[float, float],
        after: tuple[float, float],
        title: str = "Energy Conservation",
    ) -> Image.Image:
        """
        Backward-compatible wrapper for the energy bar diagram API.
        """
        return self.energy_bar_diagram(
            ke_before=before[0],
            pe_before=before[1],
            ke_after=after[0],
            pe_after=after[1],
            title=title,
        )

    def inclined_plane_diagram(
        self,
        angle_deg: float = 30.0,
        show_components: bool = True,
        title: str = "",
    ) -> Image.Image:
        """Object on inclined plane with weight components."""
        img = Image.new("RGBA", (self.w, self.h), _hex(self.bg_color) + (255,))
        draw = ImageDraw.Draw(img)
        font_title = _load_font(52)
        font_label = _load_font(42)

        if title:
            draw.text((80, 60), title, font=font_title, fill=_hex(_P["ink"]))

        # Plane geometry
        base_x, base_y = int(self.w * 0.15), int(self.h * 0.82)
        top_x = int(self.w * 0.75)
        angle_rad = math.radians(angle_deg)
        plane_len = top_x - base_x
        top_y = base_y - int(plane_len * math.tan(angle_rad))

        # Ground and plane
        draw.line([(base_x - 40, base_y), (top_x + 40, base_y)],
                  fill=_hex(_P["ground"]), width=8)
        draw.polygon(
            [(base_x, base_y), (top_x, top_y), (top_x, base_y)],
            fill=_hex("#DDD5C8"), outline=_hex(_P["ink"]), width=4,
        )

        # Object on slope (midpoint)
        mx = (base_x + top_x) // 2
        my = (base_y + top_y) // 2
        obj_r = 38
        draw.ellipse([mx - obj_r, my - obj_r, mx + obj_r, my + obj_r],
                     fill=_hex(_P["object"]), outline=_hex(_P["ink"]), width=4)
        draw.text((mx - 14, my - 20), "m", font=font_label, fill=_hex(_P["ink"]))

        if show_components:
            scale = 160
            # Weight (down)
            self._draw_named_arrow(draw, mx, my, mx, my + scale, "W=mg",
                                   _P["red"], font_label, offset=(12, 0))
            # Normal (perpendicular to plane)
            nx = -math.sin(angle_rad) * scale
            ny = -math.cos(angle_rad) * scale
            self._draw_named_arrow(draw, mx, my, mx + int(nx), my + int(ny),
                                   "N", _P["blue"], font_label, offset=(-50, -15))
            # Parallel component (down-slope)
            px = math.cos(angle_rad) * scale * 0.6
            py = math.sin(angle_rad) * scale * 0.6
            self._draw_named_arrow(draw, mx, my, mx - int(px), my + int(py),
                                   "mg sinθ", _P["orange"], font_label, offset=(-120, 10))

        # Angle arc and label
        arc_r = 60
        draw.arc(
            [top_x - arc_r, base_y - arc_r, top_x + arc_r, base_y + arc_r],
            start=180, end=180 + angle_deg,
            fill=_hex(_P["ink"]), width=3,
        )
        draw.text((top_x - arc_r - 60, base_y - 30),
                  f"θ={angle_deg:.0f}°", font=font_label, fill=_hex(_P["ink"]))

        return img

    def inclined_plane(
        self,
        angle_deg: float = 30.0,
        show_components: bool = True,
        title: str = "",
    ) -> Image.Image:
        """
        Backward-compatible wrapper for inclined plane diagrams.
        """
        return self.inclined_plane_diagram(
            angle_deg=angle_deg,
            show_components=show_components,
            title=title,
        )

    def spring_diagram(
        self,
        extension: float = 0.35,
        title: str = "Mass-Spring Diagram",
        show_force_arrow: bool = True,
        displacement_label: str = "x",
    ) -> Image.Image:
        """
        Draw a simple horizontal spring attached to a wall and mass.

        Parameters
        ----------
        extension : float
            Approximate stretch amount in [0, 1]. 0 = relaxed, 1 = strongly stretched.
        title : str
            Title shown at the top.
        show_force_arrow : bool
            Whether to draw a restoring-force arrow.
        displacement_label : str
            Label used for the displacement marker.
        """
        extension = max(0.0, min(1.0, extension))
        img = Image.new("RGBA", (self.w, self.h), _hex(self.bg_color) + (255,))
        draw = ImageDraw.Draw(img)
        font_title = _load_font(52)
        font_label = _load_font(38)

        draw.text((80, 60), title, font=font_title, fill=_hex(_P["ink"]))

        center_y = int(self.h * 0.55)
        wall_x = int(self.w * 0.18)
        wall_w = 28
        wall_h = int(self.h * 0.28)
        draw.rectangle(
            [wall_x - wall_w, center_y - wall_h // 2, wall_x, center_y + wall_h // 2],
            fill=_hex("#E7E1D6"),
            outline=_hex(_P["ink"]),
            width=4,
        )
        for y in range(center_y - wall_h // 2 + 8, center_y + wall_h // 2, 22):
            draw.line([(wall_x - wall_w, y), (wall_x, y + 18)], fill=_hex(_P["panel_border"]), width=2)

        spring_start = wall_x + 10
        spring_end = int(self.w * (0.48 + 0.16 * extension))
        coils = 7
        amp = 42
        pts: list[tuple[int, int]] = [(spring_start, center_y)]
        usable = max(40, spring_end - spring_start - 60)
        for idx in range(1, coils * 2 + 1):
            x = spring_start + int(usable * idx / (coils * 2 + 1))
            y = center_y + (amp if idx % 2 else -amp)
            pts.append((x, y))
        pts.append((spring_end, center_y))
        draw.line(pts, fill=_hex(_P["blue"]), width=10, joint="curve")

        mass_w = 120
        mass_h = 120
        mass_x0 = spring_end
        mass_y0 = center_y - mass_h // 2
        draw.rounded_rectangle(
            [mass_x0, mass_y0, mass_x0 + mass_w, mass_y0 + mass_h],
            radius=18,
            fill=_hex(_P["object"]),
            outline=_hex(_P["ink"]),
            width=4,
        )
        draw.text((mass_x0 + 42, mass_y0 + 30), "m", font=_load_font(48), fill=_hex(_P["ink"]))

        rest_x = int(self.w * 0.52)
        marker_y = center_y + 130
        draw.line([(rest_x, marker_y - 18), (rest_x, marker_y + 18)], fill=_hex(_P["gray"]), width=4)
        draw.line([(mass_x0 + mass_w // 2, marker_y), (rest_x, marker_y)], fill=_hex(_P["gray"]), width=3)
        draw.text((min(rest_x, mass_x0 + mass_w // 2) + 8, marker_y - 42), displacement_label, font=font_label, fill=_hex(_P["gray"]))

        if show_force_arrow:
            self._draw_named_arrow(
                draw,
                mass_x0 + mass_w // 2,
                center_y,
                mass_x0 - 110,
                center_y,
                "F_s",
                _P["red"],
                font_label,
                offset=(-10, -54),
            )

        return img

    # ------------------------------------------------------------------
    # Internal drawing helpers
    # ------------------------------------------------------------------

    def _draw_force_arrow(
        self,
        draw: ImageDraw.ImageDraw,
        cx: int, cy: int,
        angle_deg: float,
        length: float,
        label: str,
        color: str,
        font: ImageFont.FreeTypeFont,
        obj_r: int,
    ) -> None:
        """Draw one force arrow from the surface of the object outward."""
        angle_rad = math.radians(angle_deg)
        # Start from object surface
        x0 = cx + obj_r * math.cos(angle_rad)
        y0 = cy + obj_r * math.sin(angle_rad)
        # End point
        x1 = cx + (obj_r + length) * math.cos(angle_rad)
        y1 = cy + (obj_r + length) * math.sin(angle_rad)

        rgb = _hex(color)
        line_w = 8
        draw.line([(x0, y0), (x1, y1)], fill=rgb, width=line_w)

        # Arrowhead — filled triangle
        head_len = 32
        head_w = 18
        # Perpendicular direction
        perp_rad = angle_rad + math.pi / 2
        tip = (x1, y1)
        base_mid = (x1 - head_len * math.cos(angle_rad),
                    y1 - head_len * math.sin(angle_rad))
        left  = (base_mid[0] + head_w * math.cos(perp_rad),
                 base_mid[1] + head_w * math.sin(perp_rad))
        right = (base_mid[0] - head_w * math.cos(perp_rad),
                 base_mid[1] - head_w * math.sin(perp_rad))
        draw.polygon([tip, left, right], fill=rgb)

        # Label — placed beyond arrowhead with padding
        pad = 18
        lx = x1 + pad * math.cos(angle_rad)
        ly = y1 + pad * math.sin(angle_rad)
        bbox = draw.textbbox((0, 0), label, font=font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        # Anchor label so it doesn't overlap the arrow
        if angle_deg > 135 or angle_deg < -135:   # pointing left
            lx -= tw + 4
        elif -45 < angle_deg < 45:                 # pointing right
            pass
        else:
            lx -= tw // 2
        if angle_deg < -45:                        # pointing up
            ly -= th + 4
        draw.text((lx, ly), label, font=font, fill=rgb)

    def _draw_named_arrow(
        self,
        draw: ImageDraw.ImageDraw,
        x0: int, y0: int,
        x1: int, y1: int,
        label: str,
        color: str,
        font: ImageFont.FreeTypeFont,
        offset: tuple[int, int] = (10, -30),
    ) -> None:
        """Draw an arrow from (x0,y0) to (x1,y1) with a label."""
        rgb = _hex(color)
        draw.line([(x0, y0), (x1, y1)], fill=rgb, width=7)
        # Arrowhead
        dx, dy = x1 - x0, y1 - y0
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        head_len, head_w = 28, 15
        perp_x, perp_y = -uy, ux
        tip = (x1, y1)
        base_mid = (x1 - head_len * ux, y1 - head_len * uy)
        left  = (base_mid[0] + head_w * perp_x, base_mid[1] + head_w * perp_y)
        right = (base_mid[0] - head_w * perp_x, base_mid[1] - head_w * perp_y)
        draw.polygon([tip, left, right], fill=rgb)
        draw.text((x1 + offset[0], y1 + offset[1]), label,
                  font=font, fill=rgb)

    def _draw_arrow_h(
        self,
        draw: ImageDraw.ImageDraw,
        x0: int, x1: int, y: int,
        color: str, width: int = 5,
    ) -> None:
        """Simple horizontal arrow."""
        rgb = _hex(color)
        draw.line([(x0, y), (x1, y)], fill=rgb, width=width)
        head = 20
        draw.polygon([(x1, y), (x1 - head, y - head // 2), (x1 - head, y + head // 2)],
                     fill=rgb)
