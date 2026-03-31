"""
Scene timeline — defines when elements enter, hold, and exit the screen.

Architecture
------------
SceneTimeline owns a list of ElementTimeline records.  Each record binds a
LayoutElement to a window [enter_frame, exit_frame] and a set of animations
for enter, exit, and hold phases.

Rendering
---------
render_frame() consults the timeline to determine which elements are *active*
at a given frame number, applies the appropriate animation(s), and delegates
compositing to a simple PIL-based compositor.  It does NOT require a full
LayoutEngine implementation — a minimal stub is sufficient (see the
``_FallbackLayoutEngine`` at the bottom of this module).

The compositor contract used here:

    compositor.composite(canvas, element, alpha) -> PIL.Image

where `canvas` is the current PIL Image being built and `element` is the
(possibly transformed) LayoutElement with resolved x, y, w, h.

If a real compositor is not provided, an internal fallback is used that can
render coloured rectangles (for testing) and PIL-loaded PNGs.
"""

from __future__ import annotations

import copy
import os
import re
from collections import deque
from io import BytesIO
from dataclasses import dataclass, field
from typing import List, Optional

from PIL import Image, ImageDraw, ImageFont

from src.layout.element import LayoutElement
from src.animation.primitives import (
    Animation,
    FadeIn,
    FadeOut,
    animation_from_name,
    _clamp01,
    _copy_element,
)


# ---------------------------------------------------------------------------
# ElementTimeline
# ---------------------------------------------------------------------------

@dataclass
class ElementTimeline:
    """
    Binds a LayoutElement to its temporal window and animations within a scene.

    Parameters
    ----------
    element : LayoutElement
        The resolved element (x, y, w, h already set by the layout engine).
    enter_frame : int
        Frame number on which the element first appears.
    exit_frame : int
        Frame number on which the element is removed.  -1 means "stay to the
        end of the scene" (resolved to ``total_frames`` by SceneTimeline).
    enter_anim : Animation or None
        Animation played during the entering phase.  None → instant appear.
    exit_anim : Animation or None
        Animation played during the exit phase.  None → instant disappear.
    hold_anims : list[Animation]
        Animations played once at the start of the hold phase (e.g. pulse).
        Each runs for its own ``duration_frames`` beginning at the first hold
        frame, without looping.
    """
    element: LayoutElement
    enter_frame: int = 0
    exit_frame: int = -1          # -1 → resolved to scene total_frames
    enter_anim: Optional[Animation] = None
    exit_anim: Optional[Animation] = None
    hold_anims: List[Animation] = field(default_factory=list)

    @property
    def enter_duration(self) -> int:
        """Frames consumed by the enter animation (0 if no enter_anim)."""
        if self.enter_anim is None:
            return 0
        return getattr(self.enter_anim, "duration_frames", 0)

    @property
    def exit_duration(self) -> int:
        """Frames consumed by the exit animation (0 if no exit_anim)."""
        if self.exit_anim is None:
            return 0
        return getattr(self.exit_anim, "duration_frames", 0)


# ---------------------------------------------------------------------------
# SceneTimeline
# ---------------------------------------------------------------------------

class SceneTimeline:
    """
    Owns the full temporal description of one scene.

    Parameters
    ----------
    fps : int
        Frames per second (default 30).
    total_frames : int
        Total frame count for the scene.  Use ``from_scene_dict`` to build
        this from a seconds-based description.
    elements : list[ElementTimeline]
        All elements that appear in this scene.
    canvas_size : tuple[int, int]
        (width, height) of the output canvas.  Defaults to 16:9 1920×1080.
    background_color : tuple[int, int, int]
        RGB fallback background colour if no background element is present.
    """

    def __init__(
        self,
        fps: int = 30,
        total_frames: int = 150,
        elements: Optional[List[ElementTimeline]] = None,
        canvas_size: tuple = (1920, 1080),
        background_color: tuple = (240, 240, 240),
    ) -> None:
        self.fps = fps
        self.total_frames = total_frames
        self.elements: List[ElementTimeline] = elements or []
        self.canvas_size = canvas_size
        self.background_color = background_color
        self._default_compositor = _FallbackCompositor()
        self._resolve_exit_frames()

    # ------------------------------------------------------------------
    # Construction helpers
    # ------------------------------------------------------------------

    def add(self, et: ElementTimeline) -> "SceneTimeline":
        """Add an ElementTimeline and return self for chaining."""
        self.elements.append(et)
        self._resolve_exit_frames()
        return self

    def _resolve_exit_frames(self) -> None:
        """Replace sentinel -1 exit frames with total_frames."""
        for et in self.elements:
            if et.exit_frame == -1:
                et.exit_frame = self.total_frames

    # ------------------------------------------------------------------
    # from_scene_dict  (classmethod factory)
    # ------------------------------------------------------------------

    @classmethod
    def from_scene_dict(
        cls,
        scene: dict,
        layout_engine=None,
        fps: int = 30,
    ) -> "SceneTimeline":
        """
        Parse a scene description dict and build a SceneTimeline.

        The dict schema:

        .. code-block:: python

            {
              "duration": 4.5,          # seconds (required)
              "canvas_size": [1920, 1080],  # optional, default 16:9
              "background_color": [240, 240, 240],  # optional
              "elements": [
                {
                  "role": "character_left",
                  "asset": "char_newton.png",  # asset_path
                  "text": None,                # or text string
                  "font_size": 48,             # optional
                  "color": [26, 26, 26],       # optional RGB
                  "scale": 1.0,                # optional
                  # Layout overrides (if layout_engine is None):
                  "x": 100, "y": 100, "w": 400, "h": 600,
                  # Timing:
                  "enter_at": 0.0,   # seconds
                  "exit_at": -1,     # -1 = stay to end, else seconds
                  # Animations (string names):
                  "enter_anim": "slide_right",
                  "exit_anim": "fade_out",
                  "hold_anims": ["pulse_once"],
                  # Per-animation overrides:
                  "enter_anim_kwargs": {"duration_frames": 20},
                  "exit_anim_kwargs": {},
                }
              ]
            }

        Parameters
        ----------
        scene : dict
            Scene description following the schema above.
        layout_engine : optional
            Layout engine instance whose ``place(element)`` method resolves
            x, y, w, h.  If None, raw x/y/w/h from the dict are used.
        fps : int
            Frames per second.
        """
        duration_sec: float = float(scene["duration"])
        total_frames: int = max(1, int(round(duration_sec * fps)))

        canvas_raw = scene.get("canvas_size", [1920, 1080])
        canvas_size = tuple(canvas_raw)

        bg_raw = scene.get("background_color", [240, 240, 240])
        background_color = tuple(bg_raw)

        element_timelines: List[ElementTimeline] = []

        for edict in scene.get("elements", []):
            # Build LayoutElement
            role = edict.get("role", "caption")
            asset_path = edict.get("asset") or edict.get("asset_path")
            text = edict.get("text")
            font_size = int(edict.get("font_size", 36))
            color_raw = edict.get("color", [26, 26, 26])
            color = tuple(color_raw)
            scale = float(edict.get("scale", 1.0))
            padding = int(edict.get("padding", 8))

            el = LayoutElement(
                role=role,
                asset_path=asset_path,
                text=text if text is not None else (None if asset_path else ""),
                font_size=font_size,
                color=color,
                scale=scale,
                padding=padding,
            )
            if role in {"body_text", "caption"} and text:
                el.roll_overflow = True
                if re.search(r"[,;:]\s+", text):
                    el.roll_by_clause = True

            # Resolve layout (engine or manual override)
            if layout_engine is not None:
                # Real LayoutEngine.place() takes a list and returns a sorted list
                placed = layout_engine.place([el])
                el = placed[0]
            else:
                el.x = int(edict.get("x", 0))
                el.y = int(edict.get("y", 0))
                el.w = int(edict.get("w", 200))
                el.h = int(edict.get("h", 200))
                el.z = int(edict.get("z", 0))
                el.update_bbox()

            # Timing
            enter_at_sec = float(edict.get("enter_at", 0.0))
            raw_exit = edict.get("exit_at", -1)
            if raw_exit == -1 or raw_exit is None:
                exit_frame = -1
            else:
                exit_frame = max(0, int(round(float(raw_exit) * fps)))
                # Clamp: exit cannot exceed total_frames
                exit_frame = min(exit_frame, total_frames)

            enter_frame = max(0, int(round(enter_at_sec * fps)))
            # Clamp: enter cannot exceed total_frames
            enter_frame = min(enter_frame, total_frames)

            # Build animations
            enter_anim_name = edict.get("enter_anim")
            exit_anim_name = edict.get("exit_anim")
            hold_anim_names: list = edict.get("hold_anims") or []
            enter_anim_kwargs = edict.get("enter_anim_kwargs") or {}
            exit_anim_kwargs = edict.get("exit_anim_kwargs") or {}

            enter_anim = (
                animation_from_name(enter_anim_name, **enter_anim_kwargs)
                if enter_anim_name else None
            )
            exit_anim = (
                animation_from_name(exit_anim_name, **exit_anim_kwargs)
                if exit_anim_name else None
            )
            hold_anims = [
                animation_from_name(name) for name in hold_anim_names
            ]

            element_timelines.append(
                ElementTimeline(
                    element=el,
                    enter_frame=enter_frame,
                    exit_frame=exit_frame,
                    enter_anim=enter_anim,
                    exit_anim=exit_anim,
                    hold_anims=hold_anims,
                )
            )

        timeline = cls(
            fps=fps,
            total_frames=total_frames,
            elements=element_timelines,
            canvas_size=canvas_size,
            background_color=background_color,
        )
        return timeline

    # ------------------------------------------------------------------
    # Core rendering
    # ------------------------------------------------------------------

    def render_frame(
        self,
        frame_number: int,
        layout_engine=None,
        compositor=None,
    ) -> Image.Image:
        """
        Render one frame of the scene to a PIL Image.

        Parameters
        ----------
        frame_number : int
            Which frame to render (0-indexed).
        layout_engine : optional
            Unused in current implementation; reserved for future integration.
        compositor : optional
            Object implementing ``composite(canvas, element, alpha) → Image``.
            Defaults to the internal ``_FallbackCompositor``.

        Returns
        -------
        PIL.Image.Image
            The rendered frame as an RGB(A) PIL image.
        """
        frame_number = max(0, min(frame_number, self.total_frames - 1))
        comp = compositor or self._default_compositor

        canvas = Image.new("RGBA", self.canvas_size, (*self.background_color, 255))

        # Sort elements by z-order so higher z renders on top
        active = self._active_at(frame_number)
        active.sort(key=lambda pair: pair[0].element.z)

        for et, animated_el in active:
            alpha = int(getattr(animated_el, "alpha", 255.0))
            alpha = max(0, min(255, alpha))
            canvas = comp.composite(canvas, animated_el, alpha)

        return canvas.convert("RGBA")

    def render_all(
        self,
        output_dir: str,
        layout_engine=None,
        compositor=None,
        verbose: bool = True,
    ) -> List[str]:
        """
        Render every frame to numbered PNG files.

        Parameters
        ----------
        output_dir : str
            Directory to write frames into (created if it does not exist).
        layout_engine : optional
            Passed through to render_frame.
        compositor : optional
            Passed through to render_frame.
        verbose : bool
            Print a progress dot every 30 frames.

        Returns
        -------
        list[str]
            Absolute paths to all written PNG files in frame order.
        """
        os.makedirs(output_dir, exist_ok=True)
        paths: List[str] = []
        digits = len(str(self.total_frames - 1))
        for f in range(self.total_frames):
            img = self.render_frame(f, layout_engine=layout_engine, compositor=compositor)
            filename = f"frame_{str(f).zfill(digits)}.png"
            path = os.path.join(output_dir, filename)
            img.save(path, "PNG")
            paths.append(path)
            if verbose and f % 30 == 0:
                print(f"  rendered frame {f}/{self.total_frames - 1}")
        return paths

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _active_at(
        self, frame_number: int
    ) -> List[tuple]:
        """
        Return ``[(ElementTimeline, animated_LayoutElement), ...]`` for every
        element that is visible at ``frame_number``.

        Animation phase logic:

        - **enter phase**: ``enter_frame <= frame < enter_frame + enter_duration``
        - **hold phase**: ``enter_frame + enter_duration <= frame < exit_frame - exit_duration``
        - **exit phase**: ``exit_frame - exit_duration <= frame < exit_frame``
        - outside these bounds: element is not active.

        For hold-phase animations, each hold_anim runs once starting at the
        first hold frame for its own ``duration_frames``.
        """
        result = []
        for et in self.elements:
            resolved_exit = et.exit_frame  # already resolved from -1
            if frame_number < et.enter_frame or frame_number >= resolved_exit:
                continue

            el = _copy_element(et.element)
            if not hasattr(el, "alpha"):
                el.alpha = 255.0

            enter_end = et.enter_frame + et.enter_duration
            exit_start = max(enter_end, resolved_exit - et.exit_duration)

            if frame_number < enter_end and et.enter_anim is not None:
                # Enter phase
                anim_frame = frame_number - et.enter_frame
                t = anim_frame / max(et.enter_duration, 1)
                el = et.enter_anim.apply(el, t)

            elif frame_number >= exit_start and et.exit_anim is not None:
                # Exit phase
                anim_frame = frame_number - exit_start
                t = anim_frame / max(et.exit_duration, 1)
                el = et.exit_anim.apply(el, t)

            else:
                # Hold phase: apply any one-shot hold animations
                hold_start_frame = enter_end
                hold_duration = max(1, exit_start - hold_start_frame)
                for hold_anim in et.hold_anims:
                    hold_dur = getattr(hold_anim, "duration_frames", 0)
                    if hold_dur <= 0:
                        continue
                    frames_into_hold = frame_number - hold_start_frame
                    if 0 <= frames_into_hold < hold_dur:
                        t = frames_into_hold / hold_dur
                        el = hold_anim.apply(el, t)
                    elif (
                        frames_into_hold >= hold_dur
                        and getattr(hold_anim, "persist_final_state", False)
                    ):
                        el = hold_anim.apply(el, 1.0)
                if (
                    getattr(el, "roll_overflow", False)
                    or getattr(el, "roll_by_clause", False)
                ) and hold_duration > 0:
                    frames_into_hold = max(0, frame_number - hold_start_frame)
                    el.roll_progress = _clamp01(frames_into_hold / hold_duration)
                # Ensure full opacity during hold (unless exit fade already changed it)
                if not hasattr(el, "alpha") or el.alpha is None:
                    el.alpha = 255.0

            result.append((et, el))
        return result


# ---------------------------------------------------------------------------
# Fallback compositor (used when no real compositor is injected)
# ---------------------------------------------------------------------------

class _FallbackCompositor:
    """
    Minimal compositor sufficient for testing and development.

    Supports:
    - PNG images via PIL (element.asset_path set)
    - Coloured rectangles when element.asset_path is None (uses element.color)
    - Text rendering via PIL default font
    - Alpha blending
    """

    def __init__(self) -> None:
        self._asset_cache: dict[tuple[str, str], Image.Image] = {}
        self._fitted_asset_cache: dict[tuple[str, str, int, int], Image.Image] = {}
        self._equation_cache: dict[tuple[str, int, tuple[int, int, int], int, int], Image.Image] = {}

    def composite(
        self,
        canvas: Image.Image,
        element: LayoutElement,
        alpha: int,
    ) -> Image.Image:
        """Composite ``element`` onto ``canvas`` and return the result."""
        x, y, w, h = element.x, element.y, element.w, element.h
        if w <= 0 or h <= 0:
            return canvas

        layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))

        if element.asset_path and os.path.exists(element.asset_path):
            try:
                fitted = self._fit_asset_to_element(element)
                fitted_layer, paste_x, paste_y = self._prepare_asset_layer(element, fitted)
                layer.paste(fitted_layer, (paste_x, paste_y), fitted_layer)
            except Exception:
                self._draw_placeholder(layer, element, alpha)
        elif element.asset_path:
            # Path given but file missing → coloured placeholder
            self._draw_placeholder(layer, element, alpha)
        else:
            # Text-only element
            if element.role.startswith("equation"):
                self._draw_equation(layer, element, alpha)
            else:
                self._draw_text(layer, element, alpha)

        # Apply alpha
        if alpha < 255:
            r, g, b, a = layer.split()
            a = a.point(lambda v: int(v * alpha / 255))
            layer = Image.merge("RGBA", (r, g, b, a))

        result = Image.alpha_composite(canvas, layer)
        return result

    def _fit_asset_to_element(self, element: LayoutElement) -> Image.Image:
        key = (element.asset_path, element.role, max(1, element.w), max(1, element.h))
        cached = self._fitted_asset_cache.get(key)
        if cached is not None:
            return cached

        src = self._load_asset_rgba(element.asset_path, element.role)
        if element.role == "background":
            fitted = src.resize((max(1, element.w), max(1, element.h)), Image.LANCZOS)
        else:
            fitted = self._resize_preserving_aspect(src, max(1, element.w), max(1, element.h))

        self._fitted_asset_cache[key] = fitted
        return fitted

    def _prepare_asset_layer(
        self,
        element: LayoutElement,
        fitted: Image.Image,
    ) -> tuple[Image.Image, int, int]:
        rotation = float(getattr(element, "rotation_deg", 0.0) or 0.0)
        anchor_mode = getattr(element, "asset_anchor_mode", "auto") or "auto"
        if element.role == "background" or (abs(rotation) < 0.01 and anchor_mode == "auto"):
            paste_x, paste_y = self._asset_anchor(element, fitted.size)
            return fitted, paste_x, paste_y

        local = Image.new("RGBA", (max(1, element.w), max(1, element.h)), (0, 0, 0, 0))
        inner_x, inner_y = self._asset_local_anchor(element, fitted.size)
        local.paste(fitted, (inner_x, inner_y), fitted)

        if abs(rotation) >= 0.01:
            pivot_rel = getattr(element, "rotation_pivot_rel", (0.5, 0.5))
            pivot = (
                int(local.width * pivot_rel[0]),
                int(local.height * pivot_rel[1]),
            )
            try:
                local = local.rotate(
                    -rotation,
                    resample=Image.BICUBIC,
                    center=pivot,
                    expand=False,
                )
            except TypeError:
                local = local.rotate(-rotation, resample=Image.BICUBIC, expand=False)

        return local, element.x, element.y

    def _load_asset_rgba(self, asset_path: str, role: str) -> Image.Image:
        key = (asset_path, role)
        cached = self._asset_cache.get(key)
        if cached is not None:
            return cached

        src = Image.open(asset_path)
        if src.mode == "RGB" and role != "background" and self._should_remove_white_bg(src):
            rgba = self._remove_white_bg(src)
        else:
            rgba = src.convert("RGBA")

        self._asset_cache[key] = rgba
        return rgba

    @staticmethod
    def _resize_preserving_aspect(
        src: Image.Image,
        max_w: int,
        max_h: int,
        *,
        allow_upscale: bool = True,
    ) -> Image.Image:
        src_w, src_h = src.size
        if src_w <= 0 or src_h <= 0:
            return src.resize((max_w, max_h), Image.LANCZOS)
        scale = min(max_w / src_w, max_h / src_h)
        if not allow_upscale:
            scale = min(scale, 1.0)
        out_w = max(1, int(round(src_w * scale)))
        out_h = max(1, int(round(src_h * scale)))
        return src.resize((out_w, out_h), Image.LANCZOS)

    @staticmethod
    def _asset_anchor(element: LayoutElement, fitted_size: tuple[int, int]) -> tuple[int, int]:
        inner_x, inner_y = _FallbackCompositor._asset_local_anchor(element, fitted_size)
        return element.x + inner_x, element.y + inner_y

    @staticmethod
    def _asset_local_anchor(element: LayoutElement, fitted_size: tuple[int, int]) -> tuple[int, int]:
        fitted_w, fitted_h = fitted_size
        if element.role == "background":
            return 0, 0

        mode = getattr(element, "asset_anchor_mode", "auto") or "auto"
        if mode == "auto":
            mode = (
                "bottom_center"
                if element.role in {"character_left", "character_right", "character_center"}
                else "center"
            )

        if mode == "top_center":
            return max(0, (element.w - fitted_w) // 2), 0
        if mode == "bottom_center":
            return max(0, (element.w - fitted_w) // 2), max(0, element.h - fitted_h)
        if mode == "left_center":
            return 0, max(0, (element.h - fitted_h) // 2)
        if mode == "right_center":
            return max(0, element.w - fitted_w), max(0, (element.h - fitted_h) // 2)
        return max(0, (element.w - fitted_w) // 2), max(0, (element.h - fitted_h) // 2)

    @staticmethod
    def _should_remove_white_bg(img: Image.Image, threshold: int = 245, min_ratio: float = 0.55) -> bool:
        import numpy as np

        rgb = np.array(img.convert("RGB"), dtype=np.uint8)
        if rgb.size == 0:
            return False
        top = rgb[0, :, :]
        bottom = rgb[-1, :, :]
        left = rgb[:, 0, :]
        right = rgb[:, -1, :]
        edge = np.concatenate((top, bottom, left, right), axis=0)
        white = ((edge[:, 0] >= threshold) &
                 (edge[:, 1] >= threshold) &
                 (edge[:, 2] >= threshold))
        return bool(white.mean() >= min_ratio)

    @staticmethod
    def _remove_white_bg(img: Image.Image, threshold: int = 245) -> Image.Image:
        """
        Convert an RGB image to RGBA and remove only border-connected white
        background regions. This preserves interior light details so character
        hair, highlights, and chalk-like props do not become translucent.
        """
        import numpy as np

        rgba = img.convert("RGBA")
        data = np.array(rgba, dtype=np.uint8)
        r, g, b, a = data[:, :, 0], data[:, :, 1], data[:, :, 2], data[:, :, 3]
        white_mask = (r >= threshold) & (g >= threshold) & (b >= threshold)
        h, w = white_mask.shape
        keep = np.zeros((h, w), dtype=bool)
        queue: deque[tuple[int, int]] = deque()

        def push(px: int, py: int) -> None:
            if 0 <= px < w and 0 <= py < h and white_mask[py, px] and not keep[py, px]:
                keep[py, px] = True
                queue.append((px, py))

        for x in range(w):
            push(x, 0)
            push(x, h - 1)
        for y in range(h):
            push(0, y)
            push(w - 1, y)

        while queue:
            px, py = queue.popleft()
            push(px - 1, py)
            push(px + 1, py)
            push(px, py - 1)
            push(px, py + 1)

        a[keep] = 0
        data[:, :, 3] = a
        return Image.fromarray(data, "RGBA")

    # ------------------------------------------------------------------
    # Font loading helper (cached by size)
    # ------------------------------------------------------------------

    _font_cache: dict = {}

    @classmethod
    def _load_font(cls, size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
        if size in cls._font_cache:
            return cls._font_cache[size]
        candidates = [
            # macOS — prefer Unicode fonts for math symbols (∝, ∞, ≈, etc.)
            "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
            "/System/Library/Fonts/Supplemental/STIXGeneral.otf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
            "/System/Library/Fonts/Helvetica.ttc",
            # Linux (Ubuntu/Debian)
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
            # Linux (Red Hat / LUNARC)
            "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
            "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        ]
        font = None
        for path in candidates:
            if os.path.isfile(path):
                try:
                    font = ImageFont.truetype(path, size)
                    break
                except Exception:
                    continue
        if font is None:
            font = ImageFont.load_default()
        cls._font_cache[size] = font
        return font

    def _draw_placeholder(
        self,
        layer: Image.Image,
        element: LayoutElement,
        alpha: int,
    ) -> None:
        if element.asset_path and str(element.asset_path).startswith("storybook://"):
            # Draw a soft filled rounded card as stand-in — gives scenes the
            # coloured panel structure they were designed with.
            draw = ImageDraw.Draw(layer)
            card_alpha = max(0, min(255, int(alpha * 0.90)))
            color = (*element.color, card_alpha)
            radius = max(6, min(18, element.w // 24, element.h // 6))
            try:
                draw.rounded_rectangle(
                    [element.x, element.y,
                     element.x + element.w, element.y + element.h],
                    radius=radius,
                    fill=color,
                )
            except AttributeError:
                # Pillow < 8.2 fallback
                draw.rectangle(
                    [element.x, element.y,
                     element.x + element.w, element.y + element.h],
                    fill=color,
                )
            return
        if element.asset_path and str(element.asset_path).startswith("PLACEHOLDER:"):
            return
        draw = ImageDraw.Draw(layer)
        color = (*element.color, alpha)
        draw.rectangle(
            [element.x, element.y, element.x + element.w, element.y + element.h],
            fill=color,
        )
        if element.text:
            font_size = max(20, getattr(element, "font_size", 36))
            font = self._load_font(font_size)
            draw.text(
                (element.x + 8, element.y + 8),
                element.text,
                fill=(255, 255, 255, alpha),
                font=font,
            )

    def _draw_text(
        self,
        layer: Image.Image,
        element: LayoutElement,
        alpha: int,
    ) -> None:
        if not element.text or element.text.strip() == "":
            return
        measure = ImageDraw.Draw(layer)
        r, g, b = element.color
        pad_x = max(8, int(getattr(element, "padding", 8)))
        pad_y = max(4, pad_x // 2)
        max_w = max(1, element.w - 2 * pad_x)
        available_h = max(1, element.h - 2 * pad_y)
        align = self._text_align_for_role(element.role)

        def wrap_lines(text: str, font_obj: ImageFont.FreeTypeFont | ImageFont.ImageFont, font_px: int) -> list[str]:
            words = text.split()
            if not words:
                return []
            wrapped: list[str] = []
            current = ""
            for word in words:
                test = (current + " " + word).strip()
                try:
                    width = measure.textlength(test, font=font_obj)
                except Exception:
                    width = len(test) * font_px * 0.6
                if width <= max_w:
                    current = test
                else:
                    if current:
                        wrapped.append(current)
                    current = word
            if current:
                wrapped.append(current)
            return wrapped

        base_font_size = max(20, getattr(element, "font_size", 36))
        min_font_size = max(18, int(base_font_size * 0.72))
        font_size = base_font_size
        font = self._load_font(font_size)
        line_height = int(font_size * 1.35)
        max_visible_lines = max(1, available_h // max(1, line_height))
        lines = wrap_lines(element.text, font, font_size)
        while len(lines) > max_visible_lines and font_size > min_font_size:
            font_size = max(min_font_size, font_size - (2 if font_size > 28 else 1))
            font = self._load_font(font_size)
            line_height = int(font_size * 1.35)
            max_visible_lines = max(1, available_h // max(1, line_height))
            lines = wrap_lines(element.text, font, font_size)
        shadow_off = max(2, font_size // 22)
        stroke_w = max(1, font_size // 20)

        def visible_lines(lines: list[str]) -> tuple[list[str], float]:
            if len(lines) <= max_visible_lines:
                return lines, 0.0
            overflow = len(lines) - max_visible_lines
            progress = _clamp01(float(getattr(element, "roll_progress", 0.0)))
            if getattr(element, "roll_overflow", False):
                line_offset = overflow * progress
                start_idx = int(line_offset)
                frac = line_offset - start_idx
                start_idx = max(0, min(start_idx, overflow))
                return lines[start_idx:start_idx + max_visible_lines + 1], frac
            return lines[:max_visible_lines], 0.0

        def base_y_for_block(block_line_count: int) -> int:
            core_count = min(block_line_count, max_visible_lines)
            text_block_h = max(1, line_height * core_count)
            if element.role in {"headline", "caption", "timeline", "equation_center", "equation_right"}:
                return max(0, int((element.h - text_block_h) // 2))
            return pad_y

        def draw_block(
            box_draw: ImageDraw.ImageDraw,
            lines: list[str],
            *,
            local_alpha: int,
            y_offset_lines: float = 0.0,
        ) -> None:
            block_lines, frac = visible_lines(lines)
            y = base_y_for_block(len(block_lines)) - int((frac + y_offset_lines) * line_height)
            shadow_color = (0, 0, 0, int(120 * local_alpha / 255))
            for line in block_lines:
                try:
                    line_w = box_draw.textlength(line, font=font)
                except Exception:
                    line_w = len(line) * font_size * 0.6
                if align == "center":
                    x = max(0, int((element.w - line_w) / 2))
                elif align == "right":
                    x = max(0, int(element.w - line_w - pad_x))
                else:
                    x = pad_x
                box_draw.text(
                    (x + shadow_off, y + shadow_off),
                    line,
                    fill=shadow_color,
                    font=font,
                )
                box_draw.text(
                    (x, y),
                    line,
                    fill=(r, g, b, local_alpha),
                    font=font,
                    stroke_width=stroke_w,
                    stroke_fill=(0, 0, 0, int(90 * local_alpha / 255)),
                )
                y += line_height

        box_layer = Image.new("RGBA", (max(1, element.w), max(1, element.h)), (0, 0, 0, 0))
        box_draw = ImageDraw.Draw(box_layer)
        progress = _clamp01(float(getattr(element, "roll_progress", 0.0)))
        if getattr(element, "roll_by_clause", False):
            segments = self._split_roll_segments(element.text)
            if len(segments) > 1:
                segment_pos = progress * (len(segments) - 1)
                idx = int(segment_pos)
                frac = segment_pos - idx
                current_lines = wrap_lines(segments[idx], font, font_size)
                draw_block(box_draw, current_lines, local_alpha=alpha, y_offset_lines=frac)
                if idx + 1 < len(segments) and frac > 0.01:
                    next_lines = wrap_lines(segments[idx + 1], font, font_size)
                    draw_block(
                        box_draw,
                        next_lines,
                        local_alpha=max(0, int(alpha * frac)),
                        y_offset_lines=frac - 1.0,
                    )
            else:
                draw_block(box_draw, lines, local_alpha=alpha)
        else:
            draw_block(box_draw, lines, local_alpha=alpha)
        layer.paste(box_layer, (element.x, element.y), box_layer)

    @staticmethod
    def _split_roll_segments(text: str) -> list[str]:
        raw = (text or "").strip()
        if not raw:
            return []
        parts = [part.strip() for part in re.split(r"\s*[,;:]\s*", raw) if part.strip()]
        return parts or [raw]

    @staticmethod
    def _text_align_for_role(role: str) -> str:
        if role in {"headline", "caption", "timeline", "equation_center", "equation_right"}:
            return "center"
        if role in {"character_right"}:
            return "right"
        return "left"

    def _draw_equation(
        self,
        layer: Image.Image,
        element: LayoutElement,
        alpha: int,
    ) -> None:
        if not element.text or element.text.strip() == "":
            return

        equation = self._render_equation_image(
            text=element.text,
            font_size=max(28, getattr(element, "font_size", 72)),
            color=element.color,
            max_w=max(1, element.w),
            max_h=max(1, element.h),
        )
        if equation is None:
            self._draw_text(layer, element, alpha)
            return

        x = element.x + max(0, (element.w - equation.width) // 2)
        y = element.y + max(0, (element.h - equation.height) // 2)
        if alpha < 255:
            eq = equation.copy()
            r, g, b, a = eq.split()
            a = a.point(lambda v: int(v * alpha / 255))
            equation = Image.merge("RGBA", (r, g, b, a))
        layer.paste(equation, (x, y), equation)

    def _render_equation_image(
        self,
        text: str,
        font_size: int,
        color: tuple[int, int, int],
        max_w: int,
        max_h: int,
    ) -> Image.Image | None:
        cache_key = (text, font_size, color, max_w, max_h)
        cached = self._equation_cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            import matplotlib
            matplotlib.use("Agg")
            import matplotlib.pyplot as plt
            from matplotlib.font_manager import FontProperties

            expr = self._normalise_mathtext(text)
            color_hex = "#{:02x}{:02x}{:02x}".format(*color)
            render_dpi = max(200, int(font_size * 4))
            pt_size = max(32, int(font_size * 1.3))
            prop = FontProperties(size=pt_size)

            # Render on a transparent figure — no white-background removal needed.
            fig = plt.figure(figsize=(max_w / render_dpi, max_h / render_dpi))
            fig.patch.set_alpha(0.0)
            ax = fig.add_axes([0, 0, 1, 1], facecolor="none")
            ax.set_axis_off()
            ax.text(
                0.5, 0.5,
                f"${expr}$",
                fontsize=pt_size,
                color=color_hex,
                ha="center", va="center",
                transform=ax.transAxes,
                fontproperties=prop,
            )

            buf = BytesIO()
            fig.savefig(
                buf,
                dpi=render_dpi,
                format="png",
                transparent=True,
                bbox_inches="tight",
                pad_inches=0.08,
            )
            plt.close(fig)
            buf.seek(0)

            img = Image.open(buf).convert("RGBA")
            img = self._trim_transparent_bounds(img)
            img = self._resize_preserving_aspect(img, max_w, max_h, allow_upscale=True)
            self._equation_cache[cache_key] = img
            return img
        except Exception:
            return None

    @staticmethod
    def _normalise_mathtext(text: str) -> str:
        expr = text.strip().strip("$")
        expr = expr.replace("\\\\", "\\")
        replacements = {
            "×": r" \times ",
            "·": r" \cdot ",
            "∝": r" \propto ",
            "∞": r" \infty ",
            "≈": r" \approx ",
            "≠": r" \neq ",
            "≤": r" \leq ",
            "≥": r" \geq ",
            "→": r" \to ",
            "←": r" \leftarrow ",
            "∫": r" \int ",
            "∑": r" \sum ",
            "π": r" \pi ",
            "θ": r" \theta ",
            "α": r" \alpha ",
            "β": r" \beta ",
            "γ": r" \gamma ",
            "Δ": r" \Delta ",
            "δ": r" \delta ",
            "λ": r" \lambda ",
            "μ": r" \mu ",
            "σ": r" \sigma ",
            "ω": r" \omega ",
        }
        for raw, latex in replacements.items():
            expr = expr.replace(raw, latex)

        superscripts = str.maketrans({
            "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4",
            "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9",
            "⁺": "+", "⁻": "-", "⁽": "(", "⁾": ")",
        })
        subscripts = str.maketrans({
            "₀": "0", "₁": "1", "₂": "2", "₃": "3", "₄": "4",
            "₅": "5", "₆": "6", "₇": "7", "₈": "8", "₉": "9",
            "₊": "+", "₋": "-", "₍": "(", "₎": ")",
        })
        expr = re.sub(r"([A-Za-z0-9)])([⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁽⁾]+)", lambda m: f"{m.group(1)}^{{{m.group(2).translate(superscripts)}}}", expr)
        expr = re.sub(r"([A-Za-z0-9)])([₀₁₂₃₄₅₆₇₈₉₊₋₍₎]+)", lambda m: f"{m.group(1)}_{{{m.group(2).translate(subscripts)}}}", expr)
        return expr

    @staticmethod
    def _trim_transparent_bounds(img: Image.Image, min_alpha: int = 4) -> Image.Image:
        alpha = img.getchannel("A")
        bbox = alpha.point(lambda v: 255 if v >= min_alpha else 0).getbbox()
        if bbox is None:
            return img
        return img.crop(bbox)
