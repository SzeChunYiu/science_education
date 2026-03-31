"""
Pre-built scene type factories for physics education video production.

Each factory function constructs a fully configured SceneTimeline with
sensible defaults for a specific narrative beat.  The caller supplies
content (text, asset paths, duration) and gets back a ready-to-render
SceneTimeline.

Design philosophy
-----------------
- Characters: SlideIn + bounce_out easing — they feel alive, not mechanical.
- Equations: ScaleIn + Pop — they feel significant, like a reveal.
- Text captions: progressive reveal for longer copy, with FadeIn support for short labels.
- Backgrounds: FadeIn with a short duration — smooth context setting.

All timing is in seconds; conversion to frames is handled by SceneTimeline.

Canvas sizes
------------
The factories default to 16:9 (1920×1080).  Pass ``aspect_ratio="9:16"``
to get Shorts (1080×1920) layout — zone x/y values are scaled accordingly.

Layout convention (without a live LayoutEngine)
-----------------------------------------------
These factories manually assign x, y, w, h based on the canvas and the
zone grid defined in src/layout/constants.py.  When a real LayoutEngine
is available the caller can pass it as ``layout_engine`` and the zones
will be resolved properly.  Until then a lightweight ``_ZoneResolver``
derives pixel rects from the constants.
"""

from __future__ import annotations

import re
from typing import Optional, Sequence, Tuple

from src.layout.element import LayoutElement
from src.layout import constants
from src.animation.primitives import (
    FadeIn, FadeOut,
    SlideIn,
    ScaleIn,
    Pop, PulseOnce, RotateSwing, Shake, StretchOscillate,
    CompositeAnimation,
    TypeWriter,
    ease_out, ease_in_out, bounce_out,
)
from src.animation.timeline import SceneTimeline, ElementTimeline


# ---------------------------------------------------------------------------
# Internal zone resolver
# ---------------------------------------------------------------------------

class _ZoneResolver:
    """
    Converts a zone name + canvas size to a pixel rect (x, y, w, h).

    Mirrors the math that a full LayoutEngine would perform:
    1. Compute content-safe area (inside SAFE margins, above subtitle zone).
    2. Divide into GRID_COLS × GRID_ROWS.
    3. Map the zone's (col_start, col_end, row_start, row_end) to pixels.
    """

    def __init__(self, canvas_size: Tuple[int, int] = (1920, 1080)) -> None:
        self.cw, self.ch = canvas_size

        # Safe-area pixel bounds
        self.safe_left = int(self.cw * constants.SAFE_LEFT)
        self.safe_right = int(self.cw * (1.0 - constants.SAFE_RIGHT))
        self.safe_top = int(self.ch * constants.SAFE_TOP)
        # Content bottom: exclude the subtitle reserve
        self.safe_bottom = int(self.ch * (1.0 - constants.SAFE_BOTTOM))

        self.content_w = self.safe_right - self.safe_left
        self.content_h = self.safe_bottom - self.safe_top

        self.cell_w = self.content_w / constants.GRID_COLS
        self.cell_h = self.content_h / constants.GRID_ROWS

    def rect(self, zone: str, padding: int = 0) -> Tuple[int, int, int, int]:
        """Return (x, y, w, h) for the named zone."""
        if zone not in constants.ZONES:
            raise KeyError(f"Unknown zone: {zone!r}")
        c0, c1, r0, r1 = constants.ZONES[zone]
        x = int(self.safe_left + c0 * self.cell_w) + padding
        y = int(self.safe_top + r0 * self.cell_h) + padding
        w = int((c1 - c0) * self.cell_w) - 2 * padding
        h = int((r1 - r0) * self.cell_h) - 2 * padding
        return max(0, x), max(0, y), max(1, w), max(1, h)

    def z(self, zone: str) -> int:
        return constants.Z_ORDER.get(zone, constants.Z_ORDER_DEFAULT)


def _make_element(
    role: str,
    resolver: _ZoneResolver,
    asset_path: Optional[str] = None,
    text: Optional[str] = None,
    font_size: int = 36,
    color: Tuple[int, int, int] = (26, 26, 26),
    scale: float = 1.0,
    padding: int = 8,
) -> LayoutElement:
    """Build and place a LayoutElement using zone coordinates."""
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
    x, y, w, h = resolver.rect(role, padding=padding)
    el.x, el.y, el.w, el.h = x, y, w, h
    el.z = resolver.z(role)
    el.update_bbox()
    return el


def _canvas_for_aspect(aspect_ratio: str) -> Tuple[int, int]:
    return constants.ASPECT_TO_CANVAS.get(aspect_ratio, constants.YOUTUBE_LONG)


# ---------------------------------------------------------------------------
# Storybook scene helpers
# ---------------------------------------------------------------------------

_STORYBOOK_CREAM = (255, 247, 231)
_STORYBOOK_BUTTER = (246, 231, 139)
_STORYBOOK_TEAL = (99, 198, 197)
_STORYBOOK_SKY = (169, 216, 242)
_STORYBOOK_GREEN = (184, 217, 122)
_STORYBOOK_PEACH = (243, 176, 110)
_STORYBOOK_CORAL = (242, 141, 121)
_STORYBOOK_ROSE = (232, 162, 185)
_STORYBOOK_LAVENDER = (185, 174, 220)
_STORYBOOK_INK = (52, 42, 37)


def _mix_rgb(
    color_a: Tuple[int, int, int],
    color_b: Tuple[int, int, int],
    mix: float,
) -> Tuple[int, int, int]:
    """Blend two RGB colours with ``mix`` measured toward ``color_b``."""
    mix = max(0.0, min(1.0, mix))
    return tuple(
        int(round(color_a[idx] * (1.0 - mix) + color_b[idx] * mix))
        for idx in range(3)
    )


def _soft_card_fill(
    base_color: Tuple[int, int, int],
    background_color: Tuple[int, int, int],
    mix: float = 0.18,
) -> Tuple[int, int, int]:
    """
    Return a muted card fill that stays inside the scene palette.

    The base colour is blended toward the scene background so the card reads
    as part of the composition instead of a saturated overlay dropped on top.
    """
    return _mix_rgb(base_color, background_color, mix)


def _text_reveal_anim(
    text: str,
    fps: int,
    *,
    min_seconds: float = 0.75,
    max_seconds: float = 2.4,
    chars_per_second: float = 22.0,
    fade_seconds: float = 0.2,
) -> CompositeAnimation:
    """
    Reveal text progressively in the same box, then fade it in cleanly.

    This keeps the layout stable while the copy rolls on over time.
    """
    clean = (text or "").strip()
    if not clean:
        return CompositeAnimation(animations=[
            FadeIn(duration_frames=max(1, int(round(fade_seconds * fps))), easing=ease_in_out),
        ])
    seconds = len(clean) / max(chars_per_second, 1.0)
    seconds = max(min_seconds, min(max_seconds, seconds))
    reveal_frames = max(1, int(round(seconds * fps)))
    fade_frames = max(1, int(round(fade_seconds * fps)))
    return CompositeAnimation(animations=[
        TypeWriter(duration_frames=reveal_frames),
        FadeIn(duration_frames=fade_frames, easing=ease_in_out),
    ])


def _clip_on_screen(text: str, max_words: int = 10) -> str:
    """
    Slide-rule: on-screen text must be short like a PowerPoint bullet.
    Full narration belongs in audio/subtitles; this just shows the key phrase.
    """
    if not text:
        return text
    words = text.split()
    if len(words) <= max_words:
        return text
    return " ".join(words[:max_words]) + "…"


def _equation_font_size(equation_text: str) -> int:
    """
    Keep equations visually strong without dwarfing the explanatory copy.
    """
    clean = (equation_text or "").strip()
    length = len(clean)
    if length <= 10:
        return 50
    if length <= 28:
        return 52
    if length <= 52:
        return 50
    return 46


def _placeholder_asset_name(role: str) -> str:
    """
    Return a deliberately missing asset path.

    The fallback compositor draws a coloured rectangle when an asset path is
    present but the file does not exist.  That lets the storybook factories use
    placeholder cards and ribbons without requiring new art assets yet.
    """
    return f"storybook://{role}"


def _place_element(
    role: str,
    rect: Tuple[int, int, int, int],
    *,
    asset_path: Optional[str] = None,
    text: Optional[str] = None,
    font_size: int = 36,
    color: Tuple[int, int, int] = _STORYBOOK_INK,
    scale: float = 1.0,
    padding: int = 8,
    z: Optional[int] = None,
) -> LayoutElement:
    """Create a LayoutElement with an explicit frame rectangle."""
    x, y, w, h = rect
    el = LayoutElement(
        role=role,
        asset_path=asset_path,
        text=text,
        font_size=font_size,
        color=color,
        scale=scale,
        padding=padding,
    )
    if role in {"body_text", "caption"} and text:
        el.roll_overflow = True
        if re.search(r"[,;:]\s+", text):
            el.roll_by_clause = True
    el.x, el.y, el.w, el.h = x, y, w, h
    el.z = z if z is not None else constants.Z_ORDER.get(role, constants.Z_ORDER_DEFAULT)
    el.update_bbox()
    return el


def _fractional_rect(
    canvas: Tuple[int, int],
    x: float,
    y: float,
    w: float,
    h: float,
) -> Tuple[int, int, int, int]:
    cw, ch = canvas
    return int(cw * x), int(ch * y), int(cw * w), int(ch * h)


def _set_rect(el: LayoutElement, rect: Tuple[int, int, int, int]) -> LayoutElement:
    x, y, w, h = rect
    el.x, el.y, el.w, el.h = x, y, w, h
    el.update_bbox()
    return el


def _planned_rect(
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]],
    key: str,
    fallback: Tuple[int, int, int, int],
) -> Tuple[int, int, int, int]:
    if not layout_rects:
        return fallback
    return layout_rects.get(key, fallback)


def _timeline_element(
    element: LayoutElement,
    total_frames: int,
    *,
    enter_frame: int = 0,
    enter_anim=None,
    exit_anim=None,
    hold_anims=None,
) -> ElementTimeline:
    """Wrap a LayoutElement into a timed scene element."""
    return ElementTimeline(
        element=element,
        enter_frame=enter_frame,
        exit_frame=total_frames,
        enter_anim=enter_anim,
        exit_anim=exit_anim,
        hold_anims=hold_anims or [],
    )


def _motion_hold_anims(
    motion_profile: str,
    fps: int,
    duration_frames: int,
):
    profile = (motion_profile or "").strip().lower()
    hold_frames = max(int(1.0 * fps), duration_frames)
    if profile == "pendulum_swing":
        cycles = max(1.0, hold_frames / max(int(2.2 * fps), 1))
        return [
            RotateSwing(
                amplitude_deg=12.0,
                cycles=cycles,
                damping=0.10,
                duration_frames=hold_frames,
                pivot_rel=(0.5, 0.06),
            )
        ]
    if profile == "spring_stretch":
        cycles = max(1.5, hold_frames / max(int(1.5 * fps), 1))
        return [
            StretchOscillate(
                amplitude=0.18,
                cycles=cycles,
                damping=0.08,
                duration_frames=hold_frames,
                anchor="left",
                squash=0.05,
            )
        ]
    return []


def _apply_object_motion(
    timeline: ElementTimeline,
    motion_profile: str,
    fps: int,
    active_frames: int,
) -> ElementTimeline:
    profile = (motion_profile or "").strip().lower()
    if not profile:
        return timeline
    if profile == "pendulum_swing":
        timeline.element.asset_anchor_mode = "top_center"
    elif profile == "spring_stretch":
        timeline.element.asset_anchor_mode = "left_center"
    timeline.hold_anims.extend(_motion_hold_anims(profile, fps, active_frames))
    return timeline


def _is_text_element(el: LayoutElement) -> bool:
    return bool(el.text)


def _safe_bounds(canvas: Tuple[int, int], padding: int = 8) -> Tuple[int, int, int, int]:
    cw, ch = canvas
    left = int(cw * constants.SAFE_LEFT) + padding
    top = int(ch * constants.SAFE_TOP) + padding
    right = int(cw * (1.0 - constants.SAFE_RIGHT)) - padding
    bottom = int(ch * (1.0 - constants.SAFE_BOTTOM)) - padding
    return left, top, right, bottom


def _clamp_element_to_bounds(el: LayoutElement, bounds: Tuple[int, int, int, int]) -> None:
    left, top, right, bottom = bounds
    el.x = max(left, min(el.x, right - el.w))
    el.y = max(top, min(el.y, bottom - el.h))
    el.update_bbox()


def _rect_overlap(a: LayoutElement, b: LayoutElement) -> bool:
    return not (
        a.x + a.w <= b.x or
        b.x + b.w <= a.x or
        a.y + a.h <= b.y or
        b.y + b.h <= a.y
    )


def _nudge_text_away(
    text_el: LayoutElement,
    blocker: LayoutElement,
    bounds: Tuple[int, int, int, int],
    gap: int = 18,
) -> None:
    left, top, right, bottom = bounds
    above_y = blocker.y - text_el.h - gap
    below_y = blocker.y + blocker.h + gap

    # Prefer moving up, then down, while staying in safe bounds.
    if above_y >= top:
        text_el.y = above_y
    elif below_y + text_el.h <= bottom:
        text_el.y = below_y
    else:
        # Final fallback: move horizontally toward the nearest free edge.
        if blocker.x > (left + right) // 2:
            text_el.x = left
        else:
            text_el.x = max(left, right - text_el.w)
    _clamp_element_to_bounds(text_el, bounds)


def _apply_storybook_layout_guards(
    timelines: list[ElementTimeline],
    canvas: Tuple[int, int],
) -> list[ElementTimeline]:
    """
    Clamp elements into the safe area and avoid obvious text collisions.

    This is intentionally conservative: it only prevents clear overlaps and
    margin violations, especially important in 9:16 layouts.
    """
    bounds = _safe_bounds(canvas)
    for et in timelines:
        _clamp_element_to_bounds(et.element, bounds)

    text_elements = [et.element for et in timelines if _is_text_element(et.element)]
    blockers = [
        et.element
        for et in timelines
        if (
            not _is_text_element(et.element)
            and et.element.z >= 15
            and et.element.asset_path
            and not str(et.element.asset_path).startswith("storybook://")
        )
    ]

    # Move text away from real visual blockers like characters/objects/diagrams.
    for text_el in text_elements:
        for blocker in blockers:
            if _rect_overlap(text_el, blocker):
                _nudge_text_away(text_el, blocker, bounds)

    # Prevent text-on-text overlaps after repositioning.
    text_elements.sort(key=lambda el: (el.y, el.x))
    for idx in range(1, len(text_elements)):
        prev = text_elements[idx - 1]
        cur = text_elements[idx]
        if _rect_overlap(prev, cur):
            cur.y = prev.y + prev.h + 12
            _clamp_element_to_bounds(cur, bounds)
            if _rect_overlap(prev, cur):
                cur.y = max(bounds[1], prev.y - cur.h - 12)
                _clamp_element_to_bounds(cur, bounds)

    return timelines


# ---------------------------------------------------------------------------
# 1. equation_reveal_scene
# ---------------------------------------------------------------------------

def equation_reveal_scene(
    equation_text: str,
    narrator_text: str,
    background: str = "",
    equation_rect: Optional[Tuple[int, int, int, int]] = None,
    caption_rect: Optional[Tuple[int, int, int, int]] = None,
    duration: float = 5.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (240, 238, 230),
    fps: int = 30,
) -> SceneTimeline:
    """
    Classic equation reveal:
      - Background fades in at t=0.0s
      - Equation scales in from centre at t=0.5s, followed by a pop
      - Caption text fades in below at t=1.5s
      - Everything holds

    Parameters
    ----------
    equation_text : str
        The equation string (e.g. "F = ma").
    narrator_text : str
        Caption / narration text shown below the equation.
    background : str
        Path to background PNG, or empty string for a flat colour background.
    duration : float
        Scene length in seconds.
    aspect_ratio : str
        "16:9" or "9:16".
    background_color : tuple
        RGB fallback / border colour.
    fps : int
        Frames per second.
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    cw, ch = canvas
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))

    elements: list[ElementTimeline] = []

    # Background — full canvas, z=0
    bg_el = LayoutElement(
        role="background",
        asset_path=background if background else None,
        text=None if background else " ",
        color=background_color,
    )
    bg_el.x, bg_el.y = 0, 0
    bg_el.w, bg_el.h = canvas
    bg_el.z = constants.Z_ORDER.get("background", 0)
    bg_el.update_bbox()
    elements.append(ElementTimeline(
        element=bg_el,
        enter_frame=0,
        exit_frame=total_frames,
        enter_anim=FadeIn(duration_frames=int(0.4 * fps), easing=ease_in_out),
    ))

    # Equation and explanation should read as one teaching unit rather than
    # a giant formula plus tiny caption.
    eq_el = _make_element(
        role="equation_center",
        resolver=res,
        text=equation_text,
        font_size=max(40, int(_equation_font_size(equation_text) * 0.72)),
        color=(255, 215, 0),
    )
    _set_rect(
        eq_el,
        equation_rect if equation_rect is not None else (
            _fractional_rect(canvas, 0.18, 0.45, 0.64, 0.15) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.08, 0.43, 0.84, 0.16)
        ),
    )
    enter_frame_eq = int(0.5 * fps)
    enter_anim_eq = CompositeAnimation(animations=[
        ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.5 * fps), easing=ease_out),
    ])
    hold_anim_eq = PulseOnce(peak_scale=1.04, duration_frames=int(0.4 * fps))
    elements.append(ElementTimeline(
        element=eq_el,
        enter_frame=enter_frame_eq,
        exit_frame=total_frames,
        enter_anim=enter_anim_eq,
        exit_anim=FadeOut(duration_frames=int(0.4 * fps), easing=ease_in_out),
        hold_anims=[hold_anim_eq],
    ))

    # Explanation sits close to the equation and remains nearly the same
    # visual scale.
    cap_el = _make_element(
        role="caption",
        resolver=res,
        text=narrator_text,
        font_size=40 if aspect_ratio == "16:9" else 36,
        color=(238, 236, 228),
    )
    _set_rect(
        cap_el,
        caption_rect if caption_rect is not None else (
            _fractional_rect(canvas, 0.18, 0.61, 0.64, 0.10) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.10, 0.62, 0.80, 0.12)
        ),
    )
    elements.append(ElementTimeline(
        element=cap_el,
        enter_frame=int(1.5 * fps),
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(narrator_text, fps, min_seconds=1.0, max_seconds=2.0, chars_per_second=22.0),
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=_apply_storybook_layout_guards(elements, canvas),
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 9. storybook_hook_title_card_scene
# ---------------------------------------------------------------------------

def storybook_hook_title_card_scene(
    title_text: str,
    subtitle_text: str,
    badge_text: str = "",
    hero_asset: str = "",
    background: str = "",
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 5.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = _STORYBOOK_BUTTER,
    fps: int = 30,
) -> SceneTimeline:
    """
    Warm title-card style opener for hooks and episode launches.

    The composition is intentionally simple:
      - a bold top banner for the hook
      - a subtitle block that states the promise of the episode
      - an optional hero illustration or character on one side
      - a small badge for the series tag or chapter label
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    cw, ch = canvas
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    # Background — full canvas, z=0
    bg_el = LayoutElement(
        role="background",
        asset_path=background if background else None,
        text=None if background else " ",
        color=background_color,
    )
    bg_el.x, bg_el.y = 0, 0
    bg_el.w, bg_el.h = cw, ch
    bg_el.z = constants.Z_ORDER.get("background", 0)
    bg_el.update_bbox()
    elements.append(ElementTimeline(
        element=bg_el,
        enter_frame=0,
        exit_frame=total_frames,
    ))

    if aspect_ratio == "9:16":
        title_rect = _fractional_rect(canvas, 0.10, 0.09, 0.80, 0.14)
        subtitle_rect = _fractional_rect(canvas, 0.12, 0.30, 0.76, 0.14)
        hero_rect = _fractional_rect(canvas, 0.18, 0.50, 0.64, 0.26)
        badge_rect = (int(cw * 0.26), int(ch * 0.80), int(cw * 0.48), int(ch * 0.08))
    else:
        title_rect = _fractional_rect(canvas, 0.10, 0.10, 0.80, 0.14)
        subtitle_rect = _fractional_rect(canvas, 0.18, 0.42, 0.52, 0.12)
        hero_rect = _fractional_rect(canvas, 0.70, 0.24, 0.18, 0.46)
        badge_rect = (int(cw * 0.70), int(ch * 0.70), int(cw * 0.16), int(ch * 0.08))
    title_rect = _planned_rect(layout_rects, "title", title_rect)
    subtitle_rect = _planned_rect(layout_rects, "subtitle", subtitle_rect)
    hero_rect = _planned_rect(layout_rects, "hero", hero_rect)
    badge_rect = _planned_rect(layout_rects, "badge", badge_rect)

    title_text_el = _place_element(
        "headline",
        title_rect,
        text=title_text,
        font_size=60 if aspect_ratio == "16:9" else 50,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        title_text_el,
        total_frames,
        enter_frame=0,
        enter_anim=_text_reveal_anim(title_text, fps, min_seconds=0.9, max_seconds=1.8, chars_per_second=18.0),
    ))

    # Clip to slide-rule limit; enter only after title TypeWriter finishes (max 1.8s + 0.2s buffer)
    subtitle_clipped = _clip_on_screen(subtitle_text, max_words=10)
    subtitle_text_el = _place_element(
        "body_text",
        subtitle_rect,
        text=subtitle_clipped,
        font_size=38 if aspect_ratio == "16:9" else 30,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        subtitle_text_el,
        total_frames,
        enter_frame=int(2.0 * fps),
        enter_anim=_text_reveal_anim(subtitle_clipped, fps, min_seconds=1.0, max_seconds=2.0, chars_per_second=20.0),
    ))

    if hero_asset:
        hero = _place_element(
            "character_center" if aspect_ratio == "16:9" else "diagram",
            hero_rect,
            asset_path=hero_asset,
            color=_STORYBOOK_SKY,
            scale=1.0,
            z=20,
        )
        elements.append(_timeline_element(
            hero,
            total_frames,
            enter_frame=int(0.35 * fps),
            enter_anim=ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.55 * fps), easing=ease_out),
            hold_anims=[PulseOnce(peak_scale=1.04, duration_frames=int(0.45 * fps))],
        ))

    if badge_text:
        badge_text_el = _place_element(
            "caption",
            badge_rect,
            text=badge_text,
            font_size=24 if aspect_ratio == "16:9" else 22,
            color=_STORYBOOK_INK,
            z=45,
        )
        elements.append(_timeline_element(
            badge_text_el,
            total_frames,
            enter_frame=int(1.0 * fps),
            enter_anim=_text_reveal_anim(badge_text, fps, min_seconds=0.55, max_seconds=1.2, chars_per_second=26.0),
        ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=_apply_storybook_layout_guards(elements, canvas),
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 10. storybook_object_demo_scene
# ---------------------------------------------------------------------------

def storybook_object_demo_scene(
    object_asset: str,
    title_text: str,
    explanation_text: str,
    callout_text: str = "",
    accent_asset: str = "",
    motion_profile: str = "",
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 5.5,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = _STORYBOOK_CREAM,
    fps: int = 30,
) -> SceneTimeline:
    """
    Object-focused scene for simple experiments, props, or recurring objects.

    The object is the hero.  The title stays short and the supporting text
    explains the one idea the object should teach.
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    cw, ch = canvas
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    if aspect_ratio == "9:16":
        title_rect = _fractional_rect(canvas, 0.10, 0.08, 0.80, 0.10)
        object_rect = _fractional_rect(canvas, 0.12, 0.20, 0.76, 0.32)
        explanation_rect = _fractional_rect(canvas, 0.12, 0.58, 0.76, 0.09)
        callout_rect = (int(cw * 0.28), int(ch * 0.76), int(cw * 0.44), int(ch * 0.05))
    else:
        title_rect = _fractional_rect(canvas, 0.18, 0.10, 0.64, 0.08)
        object_rect = _fractional_rect(canvas, 0.24, 0.22, 0.52, 0.30)
        explanation_rect = _fractional_rect(canvas, 0.18, 0.57, 0.64, 0.08)
        callout_rect = _fractional_rect(canvas, 0.36, 0.70, 0.28, 0.05)
    title_rect = _planned_rect(layout_rects, "title", title_rect)
    object_rect = _planned_rect(layout_rects, "object", object_rect)
    explanation_rect = _planned_rect(layout_rects, "explanation", explanation_rect)
    callout_rect = _planned_rect(layout_rects, "callout", callout_rect)

    title_text_el = _place_element(
        "headline",
        title_rect,
        text=title_text,
        font_size=54 if aspect_ratio == "16:9" else 46,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        title_text_el,
        total_frames,
        enter_anim=_text_reveal_anim(title_text, fps, min_seconds=0.8, max_seconds=1.6, chars_per_second=18.0),
    ))

    object_el = _place_element(
        "diagram",
        object_rect,
        asset_path=object_asset if object_asset else _placeholder_asset_name("object_demo_object"),
        color=_STORYBOOK_SKY,
        scale=1.18 if aspect_ratio == "16:9" else 1.10,
        z=20,
    )
    object_timeline = _timeline_element(
        object_el,
        total_frames,
        enter_frame=int(0.35 * fps),
        enter_anim=ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.6 * fps), easing=ease_out),
        hold_anims=[PulseOnce(peak_scale=1.03, duration_frames=int(0.4 * fps))],
    )
    elements.append(_apply_object_motion(
        object_timeline,
        motion_profile,
        fps,
        total_frames - int(0.95 * fps),
    ))

    # Clip to slide-rule limit before element creation; enter after title TypeWriter (max 1.6s + 0.2s)
    explanation_clipped = _clip_on_screen(explanation_text, max_words=12)
    explanation_text_el = _place_element(
        "caption",
        explanation_rect,
        text=explanation_clipped,
        font_size=32 if aspect_ratio == "16:9" else 28,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        explanation_text_el,
        total_frames,
        enter_frame=int(1.8 * fps),
        enter_anim=_text_reveal_anim(explanation_clipped, fps, min_seconds=1.0, max_seconds=2.0, chars_per_second=20.0),
    ))

    if callout_text:
        callout_text_el = _place_element(
            "lower_third",
            callout_rect,
            text=callout_text,
            font_size=24 if aspect_ratio == "16:9" else 22,
            color=_STORYBOOK_INK,
            z=45,
        )
        # Enter after explanation TypeWriter finishes (starts 1.8s, max 2.0s → 3.8s + 0.2s buffer)
        elements.append(_timeline_element(
            callout_text_el,
            total_frames,
            enter_frame=int(4.0 * fps),
            enter_anim=_text_reveal_anim(callout_text, fps, min_seconds=0.65, max_seconds=1.2, chars_per_second=24.0),
        ))

    if accent_asset:
        accent = _place_element(
            "character_right",
            _planned_rect(layout_rects, "accent", (int(cw * 0.68), int(ch * 0.33), int(cw * 0.14), int(ch * 0.10))),
            asset_path=accent_asset,
            color=_STORYBOOK_ROSE,
            scale=1.08,
            z=18,
        )
        elements.append(_timeline_element(
            accent,
            total_frames,
            enter_frame=int(1.4 * fps),
            enter_anim=FadeIn(duration_frames=int(0.4 * fps)),
        ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=_apply_storybook_layout_guards(elements, canvas),
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 11. storybook_comparison_split_scene
# ---------------------------------------------------------------------------

def storybook_comparison_split_scene(
    left_title: str,
    left_caption: str,
    right_title: str,
    right_caption: str,
    left_asset: str = "",
    right_asset: str = "",
    bridge_text: str = "",
    left_motion_profile: str = "",
    right_motion_profile: str = "",
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 6.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = _STORYBOOK_CREAM,
    fps: int = 30,
) -> SceneTimeline:
    """
    Two-panel comparison scene for contrast, before/after, or competing ideas.
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    cw, ch = canvas
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    if aspect_ratio == "9:16":
        panel_w = int(cw * 0.80)
        panel_h = int(ch * 0.26)
        panel_x = int(cw * 0.10)
        left_rect = (panel_x, int(ch * 0.16), panel_w, panel_h)
        right_rect = (panel_x, int(ch * 0.54), panel_w, panel_h)
        vs_rect = (int(cw * 0.36), int(ch * 0.44), int(cw * 0.28), int(ch * 0.08))
    else:
        panel_w = int(cw * 0.32)
        panel_h = int(ch * 0.46)
        left_rect = (int(cw * 0.09), int(ch * 0.20), panel_w, panel_h)
        right_rect = (int(cw * 0.59), int(ch * 0.20), panel_w, panel_h)
        vs_rect = (int(cw * 0.46), int(ch * 0.39), int(cw * 0.08), int(ch * 0.10))
    left_rect = _planned_rect(layout_rects, "left_panel", left_rect)
    right_rect = _planned_rect(layout_rects, "right_panel", right_rect)
    vs_rect = _planned_rect(layout_rects, "vs", vs_rect)

    vs_text_el = _place_element(
        "timeline",
        vs_rect,
        text="vs",
        font_size=38 if aspect_ratio == "16:9" else 28,
        color=(110, 104, 92),
        z=45,
    )
    elements.append(_timeline_element(
        vs_text_el,
        total_frames,
        enter_frame=int(0.5 * fps),
        enter_anim=FadeIn(duration_frames=int(0.2 * fps)),
    ))

    left_title_rect = _planned_rect(layout_rects, "left_title", (left_rect[0], left_rect[1], left_rect[2], int(left_rect[3] * 0.16)))
    right_title_rect = _planned_rect(layout_rects, "right_title", (right_rect[0], right_rect[1], right_rect[2], int(right_rect[3] * 0.16)))
    left_caption_rect = _planned_rect(layout_rects, "left_caption", (left_rect[0], left_rect[1] + int(left_rect[3] * 0.64), left_rect[2], int(left_rect[3] * 0.12)))
    right_caption_rect = _planned_rect(layout_rects, "right_caption", (right_rect[0], right_rect[1] + int(right_rect[3] * 0.64), right_rect[2], int(right_rect[3] * 0.12)))

    left_title_el = _place_element(
        "headline",
        left_title_rect,
        text=left_title,
        font_size=40 if aspect_ratio == "16:9" else 38,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        left_title_el,
        total_frames,
        enter_frame=int(0.45 * fps),
        enter_anim=_text_reveal_anim(left_title, fps, min_seconds=0.7, max_seconds=1.4, chars_per_second=20.0),
    ))

    right_title_el = _place_element(
        "headline",
        right_title_rect,
        text=right_title,
        font_size=40 if aspect_ratio == "16:9" else 38,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        right_title_el,
        total_frames,
        enter_frame=int(0.65 * fps),
        enter_anim=_text_reveal_anim(right_title, fps, min_seconds=0.7, max_seconds=1.4, chars_per_second=20.0),
    ))

    if left_asset:
        left_asset_rect = _planned_rect(layout_rects, "left_asset", (
            left_rect[0] + int(left_rect[2] * 0.21),
            left_rect[1] + int(left_rect[3] * 0.23),
            int(left_rect[2] * 0.58),
            int(left_rect[3] * 0.30),
        ))
        left_asset_el = _place_element(
            "diagram",
            left_asset_rect,
            asset_path=left_asset,
            color=_STORYBOOK_BUTTER,
            z=18,
        )
        left_asset_timeline = _timeline_element(
            left_asset_el,
            total_frames,
            enter_frame=int(0.35 * fps),
            enter_anim=ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.45 * fps), easing=ease_out),
        )
        elements.append(_apply_object_motion(
            left_asset_timeline,
            left_motion_profile,
            fps,
            total_frames - int(0.80 * fps),
        ))

    if right_asset:
        right_asset_rect = _planned_rect(layout_rects, "right_asset", (
            right_rect[0] + int(right_rect[2] * 0.16),
            right_rect[1] + int(right_rect[3] * 0.27),
            int(right_rect[2] * 0.68),
            int(right_rect[3] * 0.20),
        ))
        right_asset_el = _place_element(
            "diagram",
            right_asset_rect,
            asset_path=right_asset,
            color=_STORYBOOK_GREEN,
            z=18,
        )
        right_asset_timeline = _timeline_element(
            right_asset_el,
            total_frames,
            enter_frame=int(0.55 * fps),
            enter_anim=ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.45 * fps), easing=ease_out),
        )
        elements.append(_apply_object_motion(
            right_asset_timeline,
            right_motion_profile,
            fps,
            total_frames - int(1.00 * fps),
        ))

    left_caption_el = _place_element(
        "caption",
        left_caption_rect,
        text=left_caption,
        font_size=34 if aspect_ratio == "16:9" else 28,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        left_caption_el,
        total_frames,
        enter_frame=int(1.0 * fps),
        enter_anim=_text_reveal_anim(left_caption, fps, min_seconds=0.9, max_seconds=2.0, chars_per_second=20.0),
    ))

    right_caption_el = _place_element(
        "caption",
        right_caption_rect,
        text=right_caption,
        font_size=34 if aspect_ratio == "16:9" else 28,
        color=_STORYBOOK_INK,
        z=40,
    )
    # Right caption enters after left caption's TypeWriter finishes (max 2.0s) + 0.5s buffer
    right_caption_enter = int(1.0 * fps) + int(2.5 * fps)
    elements.append(_timeline_element(
        right_caption_el,
        total_frames,
        enter_frame=right_caption_enter,
        enter_anim=_text_reveal_anim(right_caption, fps, min_seconds=0.9, max_seconds=2.0, chars_per_second=20.0),
    ))

    if bridge_text:
        bridge_rect = _planned_rect(
            layout_rects,
            "bridge",
            (int(cw * 0.28), int(ch * 0.84), int(cw * 0.44), int(ch * 0.08)) if aspect_ratio == "9:16" else (int(cw * 0.31), int(ch * 0.74), int(cw * 0.38), int(ch * 0.08)),
        )
        bridge_text_el = _place_element(
            "caption",
            bridge_rect,
            text=bridge_text,
            font_size=28 if aspect_ratio == "16:9" else 22,
            color=_STORYBOOK_INK,
            z=45,
        )
        # Bridge enters after right caption's TypeWriter finishes
        bridge_enter = right_caption_enter + int(2.5 * fps)
        elements.append(_timeline_element(
            bridge_text_el,
            total_frames,
            enter_frame=bridge_enter,
            enter_anim=_text_reveal_anim(bridge_text, fps, min_seconds=0.8, max_seconds=1.6, chars_per_second=24.0),
        ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=_apply_storybook_layout_guards(elements, canvas),
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 12. storybook_timeline_sequence_scene
# ---------------------------------------------------------------------------

def storybook_timeline_sequence_scene(
    stages: Sequence[tuple[str, str, Optional[str]]],
    intro_text: str = "",
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 8.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = _STORYBOOK_CREAM,
    fps: int = 30,
) -> SceneTimeline:
    """
    Timeline-style scene for historical sequences or progression of ideas.

    Each stage tuple is ``(year_text, label_text, asset_path)``.
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    cw, ch = canvas
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []
    stages = list(stages)
    count = max(1, len(stages))

    if intro_text:
        intro_rect = _planned_rect(layout_rects, "intro", _fractional_rect(canvas, 0.14, 0.07, 0.72, 0.09))
        intro_text_el = _place_element(
            "headline",
            intro_rect,
            text=intro_text,
            font_size=46 if aspect_ratio == "16:9" else 40,
            color=_STORYBOOK_INK,
            z=40,
        )
        elements.append(_timeline_element(
            intro_text_el,
            total_frames,
            enter_anim=_text_reveal_anim(intro_text, fps, min_seconds=0.8, max_seconds=1.6, chars_per_second=20.0),
        ))

    timeline_rect = _planned_rect(
        layout_rects,
        "timeline",
        (int(cw * 0.10), int(ch * 0.50), int(cw * 0.80), int(ch * 0.012)) if aspect_ratio == "16:9" else (int(cw * 0.18), int(ch * 0.50), int(cw * 0.64), int(ch * 0.018)),
    )
    timeline_bar = _place_element(
        "timeline",
        timeline_rect,
        asset_path=_placeholder_asset_name("timeline_bar"),
        color=_STORYBOOK_INK,
        z=8,
    )
    elements.append(_timeline_element(
        timeline_bar,
        total_frames,
        enter_frame=int(0.35 * fps),
        enter_anim=ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.35 * fps), easing=ease_out),
    ))

    if aspect_ratio == "9:16":
        stages_region = _planned_rect(layout_rects, "stages_region", (int(cw * 0.14), int(ch * 0.18), int(cw * 0.72), int(ch * 0.58)))
        available_h = stages_region[3]
        card_h = min(int(available_h / count) - 12, int(ch * 0.13))
        card_w = stages_region[2]
        card_x = stages_region[0]
        start_y = stages_region[1]
        gap_y = max(12, int(ch * 0.018))
        for idx, stage in enumerate(stages):
            year_text, label_text, asset_path = stage
            y = start_y + idx * (card_h + gap_y)
            year_el = _place_element(
                "lower_third",
                (card_x + 12, y, int(card_w * 0.30), int(card_h * 0.24)),
                text=year_text,
                font_size=24,
                color=_STORYBOOK_INK,
                z=40,
            )
            elements.append(_timeline_element(year_el, total_frames, enter_frame=int((0.65 + idx * 0.18) * fps), enter_anim=FadeIn(duration_frames=int(0.2 * fps))))
            label_el = _place_element(
                "caption",
                (card_x + 12, y + int(card_h * 0.28), int(card_w * 0.54), int(card_h * 0.32)),
                text=label_text,
                font_size=28,
                color=_STORYBOOK_INK,
                z=40,
            )
            elements.append(_timeline_element(label_el, total_frames, enter_frame=int((0.75 + idx * 0.18) * fps), enter_anim=FadeIn(duration_frames=int(0.2 * fps))))
            if asset_path:
                asset_el = _place_element(
                    "character_center",
                    (card_x + int(card_w * 0.66), y + int(card_h * 0.08), int(card_w * 0.22), int(card_h * 0.70)),
                    asset_path=asset_path,
                    color=_STORYBOOK_BUTTER,
                    z=18,
                )
                elements.append(_timeline_element(asset_el, total_frames, enter_frame=int((0.75 + idx * 0.18) * fps), enter_anim=ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.25 * fps), easing=ease_out)))
    else:
        stages_region = _planned_rect(layout_rects, "stages_region", (int(cw * 0.11), int(ch * 0.32), int(cw * 0.78), int(ch * 0.35)))
        usable_w = stages_region[2]
        slot_w = int(usable_w / count)
        start_x = stages_region[0]
        year_y = stages_region[1]
        asset_y = stages_region[1] + int(stages_region[3] * 0.23)
        label_y = stages_region[1] + int(stages_region[3] * 0.77)
        for idx, stage in enumerate(stages):
            year_text, label_text, asset_path = stage
            x = start_x + idx * slot_w
            center_x = x + slot_w // 2
            year_el = _place_element(
                "caption",
                (x, year_y, slot_w, int(ch * 0.05)),
                text=year_text,
                font_size=28,
                color=_STORYBOOK_INK,
                z=40,
            )
            elements.append(_timeline_element(
                year_el,
                total_frames,
                enter_frame=int((0.7 + idx * 0.18) * fps),
                enter_anim=FadeIn(duration_frames=int(0.2 * fps)),
            ))
            if asset_path:
                asset_rect = (center_x - int(slot_w * 0.17), asset_y, int(slot_w * 0.34), int(ch * 0.14))
            else:
                asset_rect = None
            if asset_rect:
                asset_el = _place_element(
                    "diagram",
                    asset_rect,
                    asset_path=asset_path,
                    color=_STORYBOOK_BUTTER,
                    z=18,
                )
                elements.append(_timeline_element(
                    asset_el,
                    total_frames,
                    enter_frame=int((0.78 + idx * 0.18) * fps),
                    enter_anim=ScaleIn(from_scale=0.0, to_scale=1.0, duration_frames=int(0.28 * fps), easing=ease_out),
                ))
            label_el = _place_element(
                "caption",
                (x, label_y, slot_w, int(ch * 0.08)),
                text=label_text,
                font_size=26,
                color=_STORYBOOK_INK,
                z=40,
            )
            elements.append(_timeline_element(
                label_el,
                total_frames,
                enter_frame=int((0.88 + idx * 0.18) * fps),
                enter_anim=_text_reveal_anim(label_text, fps, min_seconds=0.7, max_seconds=1.2, chars_per_second=24.0),
            ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=_apply_storybook_layout_guards(elements, canvas),
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 13. storybook_outro_bridge_scene
# ---------------------------------------------------------------------------

def storybook_outro_bridge_scene(
    takeaway_text: str,
    next_episode_text: str,
    series_label: str = "",
    hero_asset: str = "",
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 4.5,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = _STORYBOOK_CREAM,
    fps: int = 30,
) -> SceneTimeline:
    """
    End card that closes the episode and tees up the next one.
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    cw, ch = canvas
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    if aspect_ratio == "9:16":
        takeaway_rect = (int(cw * 0.10), int(ch * 0.18), int(cw * 0.80), int(ch * 0.22))
        next_rect = (int(cw * 0.14), int(ch * 0.50), int(cw * 0.72), int(ch * 0.16))
        hero_rect = (int(cw * 0.26), int(ch * 0.72), int(cw * 0.48), int(ch * 0.12))
        label_rect = (int(cw * 0.22), int(ch * 0.08), int(cw * 0.56), int(ch * 0.08))
    else:
        takeaway_rect = _fractional_rect(canvas, 0.08, 0.22, 0.34, 0.18)
        next_rect = _fractional_rect(canvas, 0.08, 0.50, 0.30, 0.08)
        hero_rect = _fractional_rect(canvas, 0.58, 0.18, 0.30, 0.56)
        label_rect = _fractional_rect(canvas, 0.08, 0.09, 0.28, 0.06)
    takeaway_rect = _planned_rect(layout_rects, "takeaway", takeaway_rect)
    next_rect = _planned_rect(layout_rects, "next", next_rect)
    hero_rect = _planned_rect(layout_rects, "hero", hero_rect)
    label_rect = _planned_rect(layout_rects, "label", label_rect)

    if series_label:
        label_text_el = _place_element(
            "headline",
            label_rect,
            text=series_label,
            font_size=26 if aspect_ratio == "16:9" else 24,
            color=_STORYBOOK_INK,
            z=40,
        )
        elements.append(_timeline_element(
            label_text_el,
            total_frames,
            enter_anim=FadeIn(duration_frames=int(0.2 * fps)),
        ))

    takeaway_text_el = _place_element(
        "body_text",
        takeaway_rect,
        text=takeaway_text,
        font_size=38 if aspect_ratio == "16:9" else 34,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        takeaway_text_el,
        total_frames,
        enter_frame=0,
        enter_anim=_text_reveal_anim(takeaway_text, fps, min_seconds=1.0, max_seconds=2.0, chars_per_second=18.0),
    ))

    next_text_el = _place_element(
        "body_text",
        next_rect,
        text=next_episode_text,
        font_size=28 if aspect_ratio == "16:9" else 24,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(_timeline_element(
        next_text_el,
        total_frames,
        enter_frame=int(0.45 * fps),
        enter_anim=_text_reveal_anim(next_episode_text, fps, min_seconds=0.75, max_seconds=1.5, chars_per_second=22.0),
    ))

    if hero_asset:
        hero = _place_element(
            "character_right" if aspect_ratio == "16:9" else "diagram",
            hero_rect,
            asset_path=hero_asset,
            color=_STORYBOOK_SKY,
            z=18,
        )
        elements.append(_timeline_element(
            hero,
            total_frames,
            enter_frame=int(0.8 * fps),
            enter_anim=Pop(duration_frames=int(0.25 * fps)),
            hold_anims=[PulseOnce(peak_scale=1.04, duration_frames=int(0.35 * fps))],
        ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 2. character_introduction_scene
# ---------------------------------------------------------------------------

def character_introduction_scene(
    character_asset: str,
    character_name: str,
    year: str,
    quote: str,
    background: str = "",
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 4.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (240, 238, 230),
    fps: int = 30,
) -> SceneTimeline:
    """
    Character enters from the side, name locks directly under the figure, and
    supporting quote text fades in as a separate text column.

      - Background fades in at t=0.0s
      - Character slides in from left at t=0.0s (bounce easing)
      - Character name/year fades in beneath the figure at t=0.5s
      - Quote fades in at t=1.5s

    Parameters
    ----------
    character_asset : str
        Path to character PNG.
    character_name : str
        Character's name for the lower-third.
    year : str
        Year or era string (e.g. "1687").
    quote : str
        Short quote or caption.
    background : str
        Path to background PNG.
    duration : float
        Scene length in seconds.
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    # Background
    bg_el = LayoutElement(
        role="background",
        asset_path=background if background else None,
        text=None if background else " ",
        color=background_color,
    )
    bg_el.x, bg_el.y = 0, 0
    bg_el.w, bg_el.h = canvas
    bg_el.z = constants.Z_ORDER.get("background", 0)
    bg_el.update_bbox()
    elements.append(ElementTimeline(
        element=bg_el,
        enter_frame=0,
        exit_frame=total_frames,
        enter_anim=FadeIn(duration_frames=int(0.3 * fps), easing=ease_in_out),
    ))

    # Character — slides in from left with bounce
    char_el = _make_element(
        role="character_left",
        resolver=res,
        asset_path=character_asset,
        text=None,
    )
    _set_rect(
        char_el,
        _planned_rect(
            layout_rects,
            "character",
            _fractional_rect(canvas, 0.06, 0.16, 0.24, 0.60) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.18, 0.28, 0.64, 0.42),
        ),
    )
    char_enter_frames = int(0.7 * fps)
    char_exit_frame = int(total_frames - 0.4 * fps)
    elements.append(ElementTimeline(
        element=char_el,
        enter_frame=0,
        exit_frame=char_exit_frame,
        enter_anim=SlideIn(
            direction="left",
            duration_frames=char_enter_frames,
            easing=bounce_out,
        ),
        exit_anim=FadeOut(duration_frames=int(0.4 * fps), easing=ease_in_out),
    ))

    # Label the subject directly instead of using a detached lower-third card.
    name_el = _make_element(
        role="caption",
        resolver=res,
        text=character_name,
        font_size=38 if aspect_ratio == "16:9" else 34,
        color=_STORYBOOK_INK,
    )
    _set_rect(
        name_el,
        _planned_rect(
            layout_rects,
            "name",
            _fractional_rect(canvas, 0.06, 0.76, 0.24, 0.07) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.18, 0.71, 0.64, 0.07),
        ),
    )
    elements.append(ElementTimeline(
        element=name_el,
        enter_frame=int(0.5 * fps),
        exit_frame=char_exit_frame,
        enter_anim=FadeIn(duration_frames=int(0.25 * fps), easing=ease_in_out),
        exit_anim=FadeOut(duration_frames=int(0.4 * fps), easing=ease_in_out),
    ))

    if year:
        year_el = _make_element(
            role="caption",
            resolver=res,
            text=year,
            font_size=26 if aspect_ratio == "16:9" else 24,
            color=(102, 92, 74),
        )
        _set_rect(
            year_el,
            _planned_rect(
                layout_rects,
                "year",
                _fractional_rect(canvas, 0.06, 0.82, 0.24, 0.04) if aspect_ratio == "16:9"
                else _fractional_rect(canvas, 0.18, 0.77, 0.64, 0.04),
            ),
        )
        elements.append(ElementTimeline(
            element=year_el,
            enter_frame=int(0.65 * fps),
            exit_frame=char_exit_frame,
            enter_anim=FadeIn(duration_frames=int(0.2 * fps), easing=ease_in_out),
            exit_anim=FadeOut(duration_frames=int(0.4 * fps), easing=ease_in_out),
        ))

    # Supporting quote as plain text in its own quieter column.
    quote_el = _make_element(
        role="body_text",
        resolver=res,
        text=quote,
        font_size=40 if aspect_ratio == "16:9" else 34,
        color=_STORYBOOK_INK,
    )
    _set_rect(
        quote_el,
        _planned_rect(
            layout_rects,
            "quote",
            _fractional_rect(canvas, 0.40, 0.36, 0.38, 0.16) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.14, 0.80, 0.72, 0.10),
        ),
    )
    elements.append(ElementTimeline(
        element=quote_el,
        enter_frame=int(1.2 * fps),
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(quote, fps, min_seconds=0.9, max_seconds=1.8, chars_per_second=20.0),
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 3. derivation_step_scene
# ---------------------------------------------------------------------------

def derivation_step_scene(
    previous_line: str,
    new_line: str,
    annotation: str,
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 3.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (248, 246, 240),
    fps: int = 30,
) -> SceneTimeline:
    """
    Previous equation holds at top; new line slides in below; annotation fades in.

      - Previous equation already on-screen (no enter animation)
      - New line slides in from below at t=0.3s
      - Annotation text fades in at t=1.0s

    Parameters
    ----------
    previous_line : str
        Equation text from the previous derivation step.
    new_line : str
        New equation line to introduce.
    annotation : str
        Pedagogical annotation (e.g. "multiply both sides by m").
    duration : float
        Scene length in seconds.
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    # Previous equation — present from frame 0, no enter animation
    prev_el = _make_element(
        role="headline",
        resolver=res,
        text=previous_line,
        font_size=52,
        color=(30, 30, 30),
    )
    _set_rect(prev_el, _planned_rect(layout_rects, "previous", _fractional_rect(canvas, 0.16, 0.14, 0.68, 0.12)))
    elements.append(ElementTimeline(
        element=prev_el,
        enter_frame=0,
        exit_frame=total_frames,
        enter_anim=None,
    ))

    # New equation line — slides in from below
    new_el = _make_element(
        role="equation_center",
        resolver=res,
        text=new_line,
        font_size=52,
        color=(20, 70, 160),
    )
    _set_rect(new_el, _planned_rect(layout_rects, "derivation", _fractional_rect(canvas, 0.18, 0.30, 0.64, 0.18)))
    new_enter = int(0.3 * fps)
    new_enter_dur = int(0.5 * fps)
    elements.append(ElementTimeline(
        element=new_el,
        enter_frame=new_enter,
        exit_frame=total_frames,
        enter_anim=SlideIn(
            direction="down",
            distance_px=new_el.h + 40,
            duration_frames=new_enter_dur,
            easing=ease_out,
        ),
        hold_anims=[PulseOnce(peak_scale=1.05, duration_frames=int(0.3 * fps))],
    ))

    # Annotation — fades in
    ann_el = _make_element(
        role="caption",
        resolver=res,
        text=annotation,
        font_size=32,
        color=(120, 80, 20),
    )
    _set_rect(ann_el, _planned_rect(layout_rects, "annotation", _fractional_rect(canvas, 0.16, 0.68, 0.68, 0.10)))
    elements.append(ElementTimeline(
        element=ann_el,
        enter_frame=int(1.0 * fps),
        exit_frame=total_frames,
        enter_anim=FadeIn(duration_frames=int(0.4 * fps), easing=ease_in_out),
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 4. two_character_debate_scene
# ---------------------------------------------------------------------------

def two_character_debate_scene(
    char_left_asset: str,
    char_left_name: str,
    char_left_says: str,
    char_right_asset: str,
    char_right_name: str,
    char_right_says: str,
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 6.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (230, 240, 255),
    fps: int = 30,
) -> SceneTimeline:
    """
    Two characters face each other. Left speaks first, then right.

      - Left character slides in from left at t=0.0s
      - Right character slides in from right at t=0.3s
      - Left speech bubble fades in at t=0.8s
      - Left speech bubble fades out at t=duration/2
      - Right speech bubble fades in at t=duration/2
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))
    mid_frame = total_frames // 2
    elements: list[ElementTimeline] = []

    char_enter_dur = int(0.6 * fps)

    # Left character
    left_el = _make_element(
        role="character_left",
        resolver=res,
        asset_path=char_left_asset,
        text=None,
    )
    _set_rect(
        left_el,
        _planned_rect(
            layout_rects,
            "left_character",
            _fractional_rect(canvas, 0.08, 0.22, 0.22, 0.54) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.10, 0.38, 0.34, 0.26),
        ),
    )
    elements.append(ElementTimeline(
        element=left_el,
        enter_frame=0,
        exit_frame=total_frames,
        enter_anim=SlideIn(direction="left", duration_frames=char_enter_dur, easing=bounce_out),
    ))

    # Right character
    right_el = _make_element(
        role="character_right",
        resolver=res,
        asset_path=char_right_asset,
        text=None,
    )
    _set_rect(
        right_el,
        _planned_rect(
            layout_rects,
            "right_character",
            _fractional_rect(canvas, 0.70, 0.22, 0.22, 0.54) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.56, 0.38, 0.34, 0.26),
        ),
    )
    elements.append(ElementTimeline(
        element=right_el,
        enter_frame=int(0.3 * fps),
        exit_frame=total_frames,
        enter_anim=SlideIn(direction="right", duration_frames=char_enter_dur, easing=bounce_out),
    ))

    speech_fade_dur = int(0.4 * fps)

    # Left speech text
    left_bubble_rect = (
        _fractional_rect(canvas, 0.22, 0.16, 0.22, 0.14) if aspect_ratio == "16:9"
        else _fractional_rect(canvas, 0.08, 0.16, 0.38, 0.12)
    )
    left_bubble_rect = _planned_rect(layout_rects, "left_speech", left_bubble_rect)
    left_exit_frame = mid_frame
    left_bubble_el = _place_element(
        "caption",
        left_bubble_rect,
        text=f'"{char_left_says}"',
        font_size=32,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(ElementTimeline(
        element=left_bubble_el,
        enter_frame=int(0.8 * fps),
        exit_frame=left_exit_frame,
        enter_anim=_text_reveal_anim(char_left_says, fps, min_seconds=0.6, max_seconds=1.4, chars_per_second=24.0),
        exit_anim=FadeOut(duration_frames=speech_fade_dur, easing=ease_in_out),
    ))

    # Right speech text
    right_bubble_rect = (
        _fractional_rect(canvas, 0.56, 0.16, 0.22, 0.14) if aspect_ratio == "16:9"
        else _fractional_rect(canvas, 0.54, 0.16, 0.38, 0.12)
    )
    right_bubble_rect = _planned_rect(layout_rects, "right_speech", right_bubble_rect)
    right_bubble_el = _place_element(
        "caption",
        right_bubble_rect,
        text=f'"{char_right_says}"',
        font_size=32,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(ElementTimeline(
        element=right_bubble_el,
        enter_frame=mid_frame,
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(char_right_says, fps, min_seconds=0.6, max_seconds=1.4, chars_per_second=24.0),
    ))

    # Name labels — both characters
    left_name_rect = (
        _fractional_rect(canvas, 0.06, 0.76, 0.28, 0.08) if aspect_ratio == "16:9"
        else _fractional_rect(canvas, 0.08, 0.65, 0.36, 0.07)
    )
    left_name_rect = _planned_rect(layout_rects, "left_name", left_name_rect)
    left_name_el = _place_element(
        "lower_third",
        left_name_rect,
        text=char_left_name,
        font_size=30 if aspect_ratio == "16:9" else 28,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(ElementTimeline(
        element=left_name_el,
        enter_frame=int(0.55 * fps),
        exit_frame=total_frames,
        enter_anim=FadeIn(duration_frames=int(0.25 * fps)),
    ))

    right_name_rect = (
        _fractional_rect(canvas, 0.66, 0.76, 0.28, 0.08) if aspect_ratio == "16:9"
        else _fractional_rect(canvas, 0.56, 0.65, 0.36, 0.07)
    )
    right_name_rect = _planned_rect(layout_rects, "right_name", right_name_rect)
    right_name_el = _place_element(
        "lower_third",
        right_name_rect,
        text=char_right_name,
        font_size=30 if aspect_ratio == "16:9" else 28,
        color=_STORYBOOK_INK,
        z=40,
    )
    elements.append(ElementTimeline(
        element=right_name_el,
        enter_frame=int(0.8 * fps),
        exit_frame=total_frames,
        enter_anim=FadeIn(duration_frames=int(0.25 * fps)),
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 5. diagram_explanation_scene
# ---------------------------------------------------------------------------

def diagram_explanation_scene(
    diagram_asset: str,
    headline: str,
    caption: str,
    accent_asset: str = "",
    motion_profile: str = "",
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 5.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (245, 245, 245),
    fps: int = 30,
) -> SceneTimeline:
    """
    Diagram enters on the right; headline at top; caption below.

      - Headline slides down from top at t=0.0s
      - Diagram scales in on the right at t=0.3s
      - Caption fades in below at t=1.5s
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    hl_el = _make_element(
        role="headline",
        resolver=res,
        text=headline,
        font_size=54 if aspect_ratio == "16:9" else 46,
        color=_STORYBOOK_INK,
    )
    _set_rect(
        hl_el,
        _planned_rect(
            layout_rects,
            "headline",
            _fractional_rect(canvas, 0.10, 0.08, 0.80, 0.10) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.10, 0.08, 0.80, 0.10),
        ),
    )
    elements.append(ElementTimeline(
        element=hl_el,
        enter_frame=0,
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(headline, fps, min_seconds=0.8, max_seconds=1.6, chars_per_second=20.0),
    ))

    if accent_asset:
        accent_el = _make_element(
            role="diagram",
            resolver=res,
            asset_path=accent_asset,
            text=None,
        )
        _set_rect(
            accent_el,
            _planned_rect(
                layout_rects,
                "accent",
                _fractional_rect(canvas, 0.18, 0.22, 0.64, 0.42) if aspect_ratio == "16:9"
                else _fractional_rect(canvas, 0.10, 0.24, 0.80, 0.34),
            ),
        )
        accent_el.z = 14
        elements.append(ElementTimeline(
            element=accent_el,
            enter_frame=int(0.2 * fps),
            exit_frame=total_frames,
            enter_anim=FadeIn(duration_frames=int(0.4 * fps), easing=ease_in_out),
        ))

    # Diagram — centred and given generous space so the visual element
    # is the clear hero of the scene, not an afterthought in one corner.
    diag_el = _make_element(
        role="diagram",
        resolver=res,
        asset_path=diagram_asset or _placeholder_asset_name("diagram_placeholder"),
        text=None,
    )
    _set_rect(
        diag_el,
        _planned_rect(
            layout_rects,
            "diagram",
            _fractional_rect(canvas, 0.32, 0.22, 0.36, 0.42) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.16, 0.26, 0.68, 0.32),
        ),
    )
    diag_timeline = ElementTimeline(
        element=diag_el,
        enter_frame=int(0.3 * fps),
        exit_frame=total_frames,
        enter_anim=ScaleIn(
            from_scale=0.0,
            to_scale=1.0,
            duration_frames=int(0.6 * fps),
            easing=ease_out,
        ),
    )
    elements.append(_apply_object_motion(
        diag_timeline,
        motion_profile,
        fps,
        total_frames - int(0.90 * fps),
    ))

    cap_el = _make_element(
        role="caption",
        resolver=res,
        text=caption,
        font_size=34 if aspect_ratio == "16:9" else 30,
        color=_STORYBOOK_INK,
    )
    _set_rect(
        cap_el,
        _planned_rect(
            layout_rects,
            "caption",
            _fractional_rect(canvas, 0.18, 0.70, 0.64, 0.08) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.12, 0.68, 0.76, 0.12),
        ),
    )
    elements.append(ElementTimeline(
        element=cap_el,
        enter_frame=int(1.5 * fps),
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(caption, fps, min_seconds=1.0, max_seconds=2.0, chars_per_second=20.0),
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 6. historical_moment_scene
# ---------------------------------------------------------------------------

def historical_moment_scene(
    character_asset: str,
    setting_background: str,
    year_text: str,
    location_text: str,
    narration: str,
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 5.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (220, 215, 200),
    fps: int = 30,
) -> SceneTimeline:
    """
    Character in period setting; year/location lower-third; narration caption.

      - Background fades in at t=0.0s
      - Character slides in from left at t=0.2s (bounce)
      - Year/location lower-third slides up at t=0.8s
      - Narration caption fades in at t=1.5s
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    # Background
    bg_el = LayoutElement(
        role="background",
        asset_path=setting_background if setting_background else None,
        text=None if setting_background else " ",
        color=background_color,
    )
    bg_el.x, bg_el.y = 0, 0
    bg_el.w, bg_el.h = canvas
    bg_el.z = constants.Z_ORDER.get("background", 0)
    bg_el.update_bbox()
    elements.append(ElementTimeline(
        element=bg_el,
        enter_frame=0,
        exit_frame=total_frames,
        enter_anim=FadeIn(duration_frames=int(0.5 * fps), easing=ease_in_out),
    ))

    # Character
    char_el = _make_element(
        role="character_center",
        resolver=res,
        asset_path=character_asset,
        text=None,
    )
    _set_rect(
        char_el,
        _planned_rect(
            layout_rects,
            "character",
            _fractional_rect(canvas, 0.10, 0.16, 0.26, 0.60) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.18, 0.28, 0.64, 0.38),
        ),
    )
    elements.append(ElementTimeline(
        element=char_el,
        enter_frame=int(0.2 * fps),
        exit_frame=total_frames,
        enter_anim=SlideIn(
            direction="left",
            duration_frames=int(0.7 * fps),
            easing=bounce_out,
        ),
    ))

    # Lower-third: year + location as a compact label, not a large floor panel.
    lower_text = f"{year_text}  ·  {location_text}"
    lower_el = _make_element(
        role="lower_third",
        resolver=res,
        text=lower_text,
        font_size=34 if aspect_ratio == "16:9" else 30,
        color=_STORYBOOK_INK,
    )
    _set_rect(
        lower_el,
        _planned_rect(
            layout_rects,
            "metadata",
            _fractional_rect(canvas, 0.08, 0.78, 0.28, 0.06) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.16, 0.70, 0.68, 0.06),
        ),
    )
    elements.append(ElementTimeline(
        element=lower_el,
        enter_frame=int(0.8 * fps),
        exit_frame=total_frames,
        enter_anim=FadeIn(duration_frames=int(0.25 * fps), easing=ease_in_out),
    ))

    # Narration caption: keep it separate from the floor and from the character.
    narr_el = _make_element(
        role="caption",
        resolver=res,
        text=narration,
        font_size=36 if aspect_ratio == "16:9" else 32,
        color=_STORYBOOK_INK,
    )
    _set_rect(
        narr_el,
        _planned_rect(
            layout_rects,
            "caption",
            _fractional_rect(canvas, 0.42, 0.56, 0.42, 0.12) if aspect_ratio == "16:9"
            else _fractional_rect(canvas, 0.12, 0.80, 0.76, 0.10),
        ),
    )
    elements.append(ElementTimeline(
        element=narr_el,
        enter_frame=int(1.5 * fps),
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(narration, fps, min_seconds=1.2, max_seconds=2.4, chars_per_second=18.0),
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 7. limits_breakdown_scene
# ---------------------------------------------------------------------------

def limits_breakdown_scene(
    equation_text: str,
    limit_text: str,
    warning_text: str,
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 4.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (255, 248, 240),
    fps: int = 30,
) -> SceneTimeline:
    """
    Equation is shown; a red warning indicator appears; limit condition stated.

      - Equation scales in at t=0.0s
      - Warning text fades in at t=1.0s with a shake
      - Limit condition fades in below at t=2.0s
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    # Equation — placed in the vertical centre so warning text has room above.
    eq_el = _make_element(
        role="equation_center",
        resolver=res,
        text=equation_text,
        font_size=52,
        color=(30, 30, 30),
    )
    _set_rect(eq_el, _planned_rect(layout_rects, "equation", _fractional_rect(canvas, 0.10, 0.26, 0.80, 0.28)))
    elements.append(ElementTimeline(
        element=eq_el,
        enter_frame=0,
        exit_frame=total_frames,
        enter_anim=ScaleIn(
            from_scale=0.0,
            to_scale=1.0,
            duration_frames=int(0.5 * fps),
            easing=ease_out,
        ),
    ))

    # Warning text — plain text above the equation.
    warning_rect = _planned_rect(layout_rects, "warning", _fractional_rect(canvas, 0.12, 0.09, 0.76, 0.12))
    warn_el = _place_element(
        "headline",
        warning_rect,
        text=f"! {warning_text}",
        font_size=40,
        color=(200, 30, 30),
        z=40,
    )
    warn_enter = int(1.0 * fps)
    shake_dur = int(0.6 * fps)
    elements.append(ElementTimeline(
        element=warn_el,
        enter_frame=warn_enter,
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(f"⚠  {warning_text}", fps, min_seconds=0.75, max_seconds=1.4, chars_per_second=24.0),
        hold_anims=[Shake(amplitude_px=10, duration_frames=shake_dur, cycles=3)],
    ))

    # Limit condition
    limit_el = _make_element(
        role="equation_center",
        resolver=res,
        text=limit_text,
        font_size=38,
        color=(160, 60, 0),
    )
    _set_rect(limit_el, _planned_rect(layout_rects, "limit", _fractional_rect(canvas, 0.20, 0.66, 0.60, 0.12)))
    elements.append(ElementTimeline(
        element=limit_el,
        enter_frame=int(2.0 * fps),
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(limit_text, fps, min_seconds=0.85, max_seconds=1.8, chars_per_second=20.0),
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )


# ---------------------------------------------------------------------------
# 8. worked_example_scene
# ---------------------------------------------------------------------------

def worked_example_scene(
    setup_text: str,
    equation_text: str,
    numbers_substituted: str,
    result_text: str,
    layout_rects: Optional[dict[str, Tuple[int, int, int, int]]] = None,
    duration: float = 8.0,
    aspect_ratio: str = "16:9",
    background_color: Tuple[int, int, int] = (248, 248, 248),
    fps: int = 30,
) -> SceneTimeline:
    """
    Progressive calculation: setup → equation → substitution → answer.

    Each step appears sequentially:
      - Setup text fades in at t=0.5s
      - Equation scales in at t=2.0s
      - Substitution slides in at t=4.0s
      - Result scales in at t=6.0s with a pop

    Parameters
    ----------
    setup_text : str
        Problem statement (e.g. "A 2 kg ball moves at 3 m/s. Find momentum.").
    equation_text : str
        Base equation (e.g. "p = mv").
    numbers_substituted : str
        Numbers plugged in (e.g. "p = 2 × 3").
    result_text : str
        Final answer (e.g. "p = 6 kg·m/s").
    duration : float
        Scene length in seconds (recommend >= 8.0).
    """
    canvas = _canvas_for_aspect(aspect_ratio)
    res = _ZoneResolver(canvas)
    total_frames = max(1, int(round(duration * fps)))
    elements: list[ElementTimeline] = []

    step_enter_dur = int(0.5 * fps)

    # Step 1: Setup (problem statement)
    setup_el = _make_element(
        role="headline",
        resolver=res,
        text=setup_text,
        font_size=40,
        color=(30, 30, 30),
    )
    _set_rect(setup_el, _planned_rect(layout_rects, "setup", _fractional_rect(canvas, 0.12, 0.10, 0.76, 0.10)))
    elements.append(ElementTimeline(
        element=setup_el,
        enter_frame=int(0.5 * fps),
        exit_frame=total_frames,
        enter_anim=_text_reveal_anim(setup_text, fps, min_seconds=0.9, max_seconds=2.0, chars_per_second=20.0),
    ))

    # Step 2: Base equation
    eq_el = _make_element(
        role="equation_center",
        resolver=res,
        text=equation_text,
        font_size=52,
        color=(20, 60, 140),
    )
    _set_rect(eq_el, _planned_rect(layout_rects, "equation", _fractional_rect(canvas, 0.20, 0.28, 0.60, 0.16)))
    elements.append(ElementTimeline(
        element=eq_el,
        enter_frame=int(2.0 * fps),
        exit_frame=total_frames,
        enter_anim=ScaleIn(
            from_scale=0.0,
            to_scale=1.0,
            duration_frames=step_enter_dur,
            easing=ease_out,
        ),
    ))

    # Step 3: Substitution
    sub_el = _make_element(
        role="equation_center",
        resolver=res,
        text=numbers_substituted,
        font_size=42,
        color=(100, 40, 140),
    )
    _set_rect(sub_el, _planned_rect(layout_rects, "substitution", _fractional_rect(canvas, 0.22, 0.52, 0.56, 0.12)))
    elements.append(ElementTimeline(
        element=sub_el,
        enter_frame=int(4.0 * fps),
        exit_frame=total_frames,
        enter_anim=SlideIn(
            direction="down",
            distance_px=sub_el.h + 30,
            duration_frames=step_enter_dur,
            easing=ease_out,
        ),
    ))

    # Step 4: Result — larger, with pop
    result_el = _make_element(
        role="equation_center",
        resolver=res,
        text=result_text,
        font_size=48,
        color=(10, 120, 40),
    )
    _set_rect(result_el, _planned_rect(layout_rects, "result", _fractional_rect(canvas, 0.22, 0.70, 0.56, 0.12)))
    elements.append(ElementTimeline(
        element=result_el,
        enter_frame=int(6.0 * fps),
        exit_frame=total_frames,
        enter_anim=ScaleIn(
            from_scale=0.0,
            to_scale=1.0,
            duration_frames=step_enter_dur,
            easing=ease_out,
        ),
        hold_anims=[PulseOnce(peak_scale=1.10, duration_frames=int(0.5 * fps))],
    ))

    return SceneTimeline(
        fps=fps,
        total_frames=total_frames,
        elements=elements,
        canvas_size=canvas,
        background_color=background_color,
    )
