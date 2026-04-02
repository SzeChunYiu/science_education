"""
Compositor — assembles final video frames from resolved LayoutElement positions.

Takes a scene descriptor dict, runs the layout engine, checks contrast for all
text elements, applies fixes where needed, then composites everything into a
single PIL Image saved to disk.
"""

from __future__ import annotations

import os
from typing import Optional, List

from PIL import Image, ImageDraw, ImageFont

from .constants import (
    ASPECT_TO_CANVAS,
    DEFAULT_FONT_PATH,
    DEFAULT_FONT_SIZE,
    DEFAULT_TEXT_COLOR,
    WCAG_AA_LARGE,
    WCAG_AA_NORMAL,
    Z_ORDER,
    Z_ORDER_DEFAULT,
)
from .contrast import (
    auto_fix_text_contrast,
    sample_background_color_at_element,
    contrast_ratio,
)
from .element import LayoutElement, _hex_to_rgb
from .engine import LayoutEngine


class Compositor:
    """
    Composites a scene dict into a final PIL Image.

    Workflow:
      1. Parse scene dict into LayoutElement objects
      2. Run LayoutEngine.place() to resolve all positions
      3. For each text element, sample the background at its position and
         apply contrast auto-fix if needed
      4. Render layers in z-order: background → images → text
      5. Save and return the composited PIL Image

    Args:
        layout_engine: a configured LayoutEngine instance
    """

    def __init__(self, layout_engine: LayoutEngine) -> None:
        self.engine = layout_engine
        self._canvas_w = layout_engine.canvas_w
        self._canvas_h = layout_engine.canvas_h

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def render_frame(self, scene: dict, output_path: str) -> Image.Image:
        """
        Render a single scene frame to a PNG file.

        Scene dict format::

            {
                "background": "path/to/bg.png",   # or hex color e.g. "#f5e6d3"
                "elements": [
                    {"role": "character_left",  "asset": "char.png",   "scale": 0.8},
                    {"role": "equation_center", "text": "p = mv",
                     "font_size": 72, "color": "#1a1a1a"},
                    {"role": "caption",  "text": "momentum = mass × velocity",
                     "font_size": 36},
                    {"role": "subtitle", "text": "The quantity Newton started with",
                     "font_size": 32},
                ]
            }

        Args:
            scene:       validated scene descriptor dict
            output_path: absolute path where the PNG will be saved

        Returns:
            The composited PIL Image (also saved to output_path)
        """
        # 1. Build the background canvas
        canvas = self._make_background(scene.get("background", "#ffffff"))

        # 2. Parse element dicts into LayoutElement objects
        elements = [
            self._parse_element(e) for e in scene.get("elements", [])
        ]

        if not elements:
            canvas.save(output_path)
            return canvas

        # 3. Layout engine resolves positions (sorted by z ascending)
        elements = self.engine.place(elements)

        # 4. Composite in z-order
        draw = ImageDraw.Draw(canvas, "RGBA")

        for el in elements:
            if el.is_image:
                canvas = self._composite_image(canvas, el)
                draw = ImageDraw.Draw(canvas, "RGBA")  # rebind after paste
            else:
                # Text element: check contrast and apply fix if needed
                el = self._apply_contrast_fix(canvas, el)
                canvas = self._render_text(canvas, draw, el)
                draw = ImageDraw.Draw(canvas, "RGBA")

        # Convert to RGB before saving (PNG supports RGBA but players differ)
        final = canvas.convert("RGBA")
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        final.save(output_path, format="PNG")
        return final

    def render_scene_sequence(
        self,
        scenes: List[dict],
        output_dir: str,
    ) -> List[str]:
        """
        Render a list of scene dicts to sequentially numbered PNG files.

        Files are named ``frame_0000.png``, ``frame_0001.png``, etc.

        Args:
            scenes:     list of scene descriptor dicts
            output_dir: directory to write PNG files into

        Returns:
            List of absolute paths to the written PNG files
        """
        os.makedirs(output_dir, exist_ok=True)
        paths = []
        for idx, scene in enumerate(scenes):
            out_path = os.path.join(output_dir, f"frame_{idx:04d}.png")
            self.render_frame(scene, out_path)
            paths.append(out_path)
        return paths

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _make_background(self, background_spec: str) -> Image.Image:
        """
        Create the base canvas from either a file path or a hex color.

        Args:
            background_spec: path to a PNG/JPEG, or a CSS hex color string

        Returns:
            RGBA PIL Image at the canvas resolution
        """
        canvas = Image.new("RGBA", (self._canvas_w, self._canvas_h), (255, 255, 255, 255))

        if background_spec.startswith("#") or (
            len(background_spec) in (3, 6) and all(c in "0123456789abcdefABCDEF" for c in background_spec.lstrip("#"))
        ):
            # Solid color fill
            rgb = _hex_to_rgb(background_spec)
            canvas.paste(Image.new("RGB", (self._canvas_w, self._canvas_h), rgb))
        elif os.path.isfile(background_spec):
            bg = Image.open(background_spec).convert("RGBA")
            bg = bg.resize((self._canvas_w, self._canvas_h), Image.LANCZOS)
            canvas.paste(bg, (0, 0))
        else:
            # Unknown spec — leave white canvas, log a warning
            import warnings
            warnings.warn(
                f"Background spec {background_spec!r} is neither a valid file path "
                "nor a hex color. Using white background.",
                stacklevel=3,
            )

        return canvas

    def _parse_element(self, spec: dict) -> LayoutElement:
        """
        Convert a scene element dict into a LayoutElement.

        Accepted keys:
            role, asset (path), text, font_size, color (hex or tuple), scale, padding
        """
        role = spec["role"]
        asset_path = spec.get("asset") or spec.get("asset_path")
        text = spec.get("text")
        font_size = int(spec.get("font_size", DEFAULT_FONT_SIZE))
        scale = float(spec.get("scale", 1.0))
        padding = int(spec.get("padding", 8))

        raw_color = spec.get("color", DEFAULT_TEXT_COLOR)
        if isinstance(raw_color, str):
            color = _hex_to_rgb(raw_color)
        else:
            color = tuple(raw_color)

        return LayoutElement(
            role=role,
            asset_path=asset_path,
            text=text,
            font_size=font_size,
            color=color,
            scale=scale,
            padding=padding,
        )

    def _composite_image(
        self, canvas: Image.Image, el: LayoutElement
    ) -> Image.Image:
        """
        Load and paste an image asset onto the canvas at the resolved position.

        Handles transparency (RGBA).
        """
        try:
            img = Image.open(el.asset_path).convert("RGBA")
        except Exception as exc:
            import warnings
            warnings.warn(f"Could not load image {el.asset_path!r}: {exc}")
            return canvas

        # Resize to element's resolved w×h
        if img.size != (el.w, el.h):
            img = img.resize((el.w, el.h), Image.LANCZOS)

        # Paste using alpha channel as mask
        canvas.paste(img, (el.x, el.y), mask=img.split()[3])
        return canvas

    def _apply_contrast_fix(
        self, canvas: Image.Image, el: LayoutElement
    ) -> LayoutElement:
        """
        Check text contrast against the background and apply a fix if needed.

        Modifies el.contrast_fix and el.color in place.

        Returns:
            The (possibly mutated) LayoutElement
        """
        if el.bbox is None:
            return el

        bg_color = sample_background_color_at_element(canvas, el.bbox)
        fix = auto_fix_text_contrast(
            text_color=el.color,
            bg_color=bg_color,
            min_ratio=WCAG_AA_LARGE if el.font_size >= 18 else WCAG_AA_NORMAL,
        )
        if fix is not None:
            el.contrast_fix = fix
            if "new_text_color" in fix:
                el.color = fix["new_text_color"]

        return el

    def _render_text(
        self,
        canvas: Image.Image,
        draw: ImageDraw.ImageDraw,
        el: LayoutElement,
    ) -> Image.Image:
        """
        Render a text element onto the canvas, applying any contrast fix.

        Supports:
          - Drop shadow (offset 2px)
          - Semi-transparent backing box

        Returns:
            Updated canvas (may be a new Image if RGBA compositing was needed)
        """
        font = _load_font(el.font_size)
        text = _fit_text_to_box(el.text or "", font, el.w, el.h)

        # If a backing box fix is needed, draw it first
        fix = el.contrast_fix or {}
        if fix.get("method") == "backing_box":
            backing_rgba = fix.get("backing_color", (0, 0, 0, 153))
            overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            ov_draw = ImageDraw.Draw(overlay)
            margin = 6
            ov_draw.rectangle(
                [
                    el.x - margin,
                    el.y - margin,
                    el.x + el.w + margin,
                    el.y + el.h + margin,
                ],
                fill=backing_rgba,
            )
            canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay)
            draw = ImageDraw.Draw(canvas, "RGBA")

        text_fill = el.color + (255,) if len(el.color) == 3 else el.color

        # Drop shadow
        if fix.get("method") == "shadow":
            shadow_color = fix.get("shadow_color", (0, 0, 0, 180))
            shadow_offset = max(2, el.font_size // 18)
            _draw_multiline_text(
                draw, el.x + shadow_offset, el.y + shadow_offset,
                text, font, shadow_color
            )

        # Main text
        _draw_multiline_text(draw, el.x, el.y, text, font, text_fill)

        return canvas


# ---------------------------------------------------------------------------
# Font loading helper
# ---------------------------------------------------------------------------

_FONT_CACHE: dict = {}


def _load_font(font_size: int, font_path: Optional[str] = None) -> ImageFont.FreeTypeFont:
    """
    Load a PIL font at the given size.

    Falls back to the PIL built-in bitmap font if no TTF is available.
    Caches results to avoid redundant disk reads.
    """
    path = font_path or DEFAULT_FONT_PATH
    cache_key = (path, font_size)
    if cache_key in _FONT_CACHE:
        return _FONT_CACHE[cache_key]

    font = None
    if path and os.path.isfile(path):
        try:
            font = ImageFont.truetype(path, font_size)
        except Exception:
            pass

    if font is None:
        # Try common system fonts as fallback
        for candidate in [
            "/System/Library/Fonts/Supplemental/Verdana.ttf",   # macOS common readable fallback
            "/System/Library/Fonts/Supplemental/Arial.ttf",     # macOS common readable fallback
            "/System/Library/Fonts/Helvetica.ttc",              # macOS
            "/System/Library/Fonts/Arial.ttf",                  # macOS alt
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",  # Linux
            "/usr/share/fonts/TTF/DejaVuSans.ttf",           # Linux alt
        ]:
            if os.path.isfile(candidate):
                try:
                    font = ImageFont.truetype(candidate, font_size)
                    break
                except Exception:
                    continue

    if font is None:
        font = ImageFont.load_default()

    _FONT_CACHE[cache_key] = font
    return font


def _draw_multiline_text(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple,
) -> None:
    """
    Draw potentially multiline text at (x, y) using the given font and fill color.
    """
    lines = text.split("\n")
    try:
        bbox = font.getbbox("A")
        line_h = (bbox[3] - bbox[1]) + 4
    except AttributeError:
        line_h = font.size + 4  # type: ignore

    for i, line in enumerate(lines):
        draw.text((x, y + i * line_h), line, font=font, fill=fill)


def _measure_text_width(font: ImageFont.FreeTypeFont, text: str) -> float:
    """Measure a single line of text for wrapping decisions."""
    if not text:
        return 0.0
    if hasattr(font, "getlength"):
        try:
            return float(font.getlength(text))
        except Exception:
            pass
    try:
        bbox = font.getbbox(text)
        return float(bbox[2] - bbox[0])
    except Exception:
        return float(len(text) * max(6, getattr(font, "size", 12) * 0.6))


def _line_height(font: ImageFont.FreeTypeFont) -> int:
    """Estimate line height for wrapped text."""
    try:
        bbox = font.getbbox("Ag")
        return max(1, (bbox[3] - bbox[1]) + 4)
    except Exception:
        return max(1, getattr(font, "size", 12) + 4)


def _truncate_line_to_width(
    line: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> str:
    """Trim a line to fit a box and add ellipsis if needed."""
    if _measure_text_width(font, line) <= max_width:
        return line
    ellipsis = "..."
    working = line.strip()
    while working and _measure_text_width(font, working + ellipsis) > max_width:
        working = working[:-1].rstrip()
    return (working + ellipsis) if working else ellipsis


def _wrap_text_to_width(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
) -> list[str]:
    """Greedy word-wrap that respects explicit paragraph breaks."""
    if max_width <= 0:
        return [text] if text else [""]

    wrapped: list[str] = []
    paragraphs = text.split("\n") if text else [""]
    for paragraph in paragraphs:
        words = paragraph.split()
        if not words:
            wrapped.append("")
            continue

        current = words[0]
        for word in words[1:]:
            candidate = f"{current} {word}"
            if _measure_text_width(font, candidate) <= max_width:
                current = candidate
            else:
                if _measure_text_width(font, current) > max_width:
                    wrapped.append(_truncate_line_to_width(current, font, max_width))
                else:
                    wrapped.append(current)
                current = word

        if _measure_text_width(font, current) > max_width:
            wrapped.append(_truncate_line_to_width(current, font, max_width))
        else:
            wrapped.append(current)

    return wrapped


def _fit_text_to_box(
    text: str,
    font: ImageFont.FreeTypeFont,
    max_width: int,
    max_height: int,
) -> str:
    """
    Wrap text to the element box and clamp the number of lines to fit height.
    """
    lines = _wrap_text_to_width(text, font, max_width)
    if max_height <= 0:
        return "\n".join(lines[:1])

    line_h = _line_height(font)
    max_lines = max(1, max_height // line_h)
    if len(lines) <= max_lines:
        return "\n".join(lines)

    clipped = lines[:max_lines]
    clipped[-1] = _truncate_line_to_width(clipped[-1], font, max_width)
    return "\n".join(clipped)
