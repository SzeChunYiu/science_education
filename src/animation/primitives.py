"""
Animation primitives for physics education video production.

Provides easing functions and per-element animation classes that transform
a LayoutElement at a given normalised time t ∈ [0, 1].

Design contract
---------------
Every Animation subclass exposes:

    apply(element, frame_t) -> LayoutElement

where `element` is a *copy* of the original LayoutElement with its resolved
x, y, w, h, z, and an extra `alpha` attribute (float 0–255) that the
compositor uses for blending.  `frame_t` is the normalised progress of
this specific animation in [0, 1].

The original LayoutElement is never mutated.
"""

from __future__ import annotations

import copy
import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.layout.element import LayoutElement


# ---------------------------------------------------------------------------
# Easing functions  (t ∈ [0, 1]  →  value ∈ [0, 1])
# ---------------------------------------------------------------------------

def linear(t: float) -> float:
    """Constant speed — no easing."""
    return float(t)


def ease_in(t: float) -> float:
    """Slow start, fast end (cubic)."""
    t = _clamp01(t)
    return t * t * t


def ease_out(t: float) -> float:
    """Fast start, slow end (cubic)."""
    t = _clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def ease_in_out(t: float) -> float:
    """Smooth start and end (cubic Hermite)."""
    t = _clamp01(t)
    return t * t * (3.0 - 2.0 * t)


def bounce_out(t: float) -> float:
    """
    Bounces at the end — great for character entrances.

    Implements the standard four-stage bounce curve.
    """
    t = _clamp01(t)
    n1 = 7.5625
    d1 = 2.75
    if t < 1.0 / d1:
        return n1 * t * t
    elif t < 2.0 / d1:
        t -= 1.5 / d1
        return n1 * t * t + 0.75
    elif t < 2.5 / d1:
        t -= 2.25 / d1
        return n1 * t * t + 0.9375
    else:
        t -= 2.625 / d1
        return n1 * t * t + 0.984375


def spring(t: float, stiffness: float = 10.0, damping: float = 0.7) -> float:
    """
    Damped spring easing — overshoots slightly then settles.

    Parameters
    ----------
    t : float
        Normalised time in [0, 1].
    stiffness : float
        Controls oscillation frequency (default 10.0).
    damping : float
        Controls how quickly oscillations decay (default 0.7).  Values closer
        to 1.0 are more damped (fewer overshoots); values closer to 0 ring
        longer.
    """
    t = _clamp01(t)
    if t == 0.0:
        return 0.0
    if t == 1.0:
        return 1.0
    decay = math.exp(-damping * stiffness * t)
    freq = stiffness * math.sqrt(max(0.0, 1.0 - damping * damping))
    return 1.0 - decay * math.cos(freq * t)


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _clamp01(t: float) -> float:
    return max(0.0, min(1.0, t))


def _copy_element(element: LayoutElement) -> LayoutElement:
    """Return a shallow copy of the element and ensure it has an alpha attr."""
    el = copy.copy(element)
    if not hasattr(el, "alpha"):
        el.alpha = 255.0
    return el


# ---------------------------------------------------------------------------
# Base Animation protocol
# ---------------------------------------------------------------------------

class Animation:
    """
    Abstract base for all per-element animations.

    Subclasses implement `apply(element, frame_t)` and must NOT mutate the
    incoming element.
    """

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        raise NotImplementedError


# ---------------------------------------------------------------------------
# Fade
# ---------------------------------------------------------------------------

@dataclass
class FadeIn(Animation):
    """
    Fade an element from transparent to fully opaque.

    Parameters
    ----------
    duration_frames : int
        Number of frames over which the fade completes.
    easing : callable
        Easing function (default: ease_in_out).
    """
    duration_frames: int = 15
    easing: Callable[[float], float] = field(default_factory=lambda: ease_in_out)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        el.alpha = self.easing(_clamp01(frame_t)) * 255.0
        return el


@dataclass
class FadeOut(Animation):
    """
    Fade an element from fully opaque to transparent.

    Parameters
    ----------
    duration_frames : int
        Number of frames over which the fade completes.
    easing : callable
        Easing function (default: ease_in_out).
    """
    duration_frames: int = 15
    easing: Callable[[float], float] = field(default_factory=lambda: ease_in_out)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        el.alpha = (1.0 - self.easing(_clamp01(frame_t))) * 255.0
        return el


# ---------------------------------------------------------------------------
# Slide
# ---------------------------------------------------------------------------

@dataclass
class SlideIn(Animation):
    """
    Slide an element into its final position from off-screen (or a fixed
    pixel distance).

    Parameters
    ----------
    direction : str
        One of "left", "right", "up", "down".  "left" means the element
        enters from the left edge moving rightward to its resting position.
    distance_px : int or None
        How many pixels the element travels.  None → use the element's own
        dimension (w for horizontal, h for vertical), which puts the start
        position off-canvas.
    duration_frames : int
        Frames to complete the slide.
    easing : callable
        Easing function (default: ease_out).
    """
    direction: str = "left"
    distance_px: Optional[int] = None
    duration_frames: int = 20
    easing: Callable[[float], float] = field(default_factory=lambda: ease_out)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        progress = self.easing(_clamp01(frame_t))
        offset = self._get_offset(el)
        dx = dy = 0
        if self.direction == "left":
            dx = int(offset * (1.0 - progress))
            # Start from the left: negative x offset (element was off-left)
            # "enters from left" → starts at (x - offset) and moves to x
            el.x = el.x - int(offset * (1.0 - progress))
        elif self.direction == "right":
            el.x = el.x + int(offset * (1.0 - progress))
        elif self.direction == "up":
            el.y = el.y - int(offset * (1.0 - progress))
        elif self.direction == "down":
            el.y = el.y + int(offset * (1.0 - progress))
        el.update_bbox()
        return el

    def _get_offset(self, el: LayoutElement) -> int:
        if self.distance_px is not None:
            return self.distance_px
        if self.direction in ("left", "right"):
            return el.x + el.w   # enough to be off-screen left/right
        else:
            return el.y + el.h   # enough to be off-screen top/bottom


@dataclass
class SlideOut(Animation):
    """
    Slide an element out of its current position toward a canvas edge.

    Parameters
    ----------
    direction : str
        One of "left", "right", "up", "down".  Direction of exit travel.
    distance_px : int or None
        Pixels to travel before fully gone.  None → element's own dimension.
    duration_frames : int
        Frames to complete.
    easing : callable
        Easing function (default: ease_in).
    """
    direction: str = "right"
    distance_px: Optional[int] = None
    duration_frames: int = 20
    easing: Callable[[float], float] = field(default_factory=lambda: ease_in)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        progress = self.easing(_clamp01(frame_t))
        distance = self._get_distance(el)
        if self.direction == "left":
            el.x = el.x - int(distance * progress)
        elif self.direction == "right":
            el.x = el.x + int(distance * progress)
        elif self.direction == "up":
            el.y = el.y - int(distance * progress)
        elif self.direction == "down":
            el.y = el.y + int(distance * progress)
        el.alpha = (1.0 - progress) * 255.0
        el.update_bbox()
        return el

    def _get_distance(self, el: LayoutElement) -> int:
        if self.distance_px is not None:
            return self.distance_px
        if self.direction in ("left", "right"):
            return el.x + el.w
        else:
            return el.y + el.h


# ---------------------------------------------------------------------------
# Scale
# ---------------------------------------------------------------------------

@dataclass
class ScaleIn(Animation):
    """
    Scale an element from `from_scale` to `to_scale`.

    The element scales around its center point, so x/y are adjusted to
    keep the center stationary.

    Parameters
    ----------
    from_scale : float
        Starting scale multiplier (default 0.0 → element is invisible).
    to_scale : float
        Ending scale multiplier (default 1.0 → element at its natural size).
    duration_frames : int
        Frames to complete.
    easing : callable
        Easing function (default: ease_out).
    """
    from_scale: float = 0.0
    to_scale: float = 1.0
    duration_frames: int = 15
    easing: Callable[[float], float] = field(default_factory=lambda: ease_out)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        progress = self.easing(_clamp01(frame_t))
        current_scale = self.from_scale + (self.to_scale - self.from_scale) * progress
        if current_scale <= 0.0:
            el.alpha = 0.0
            return el
        # Center of the element in its resting position
        cx = el.x + el.w / 2.0
        cy = el.y + el.h / 2.0
        new_w = int(el.w * current_scale)
        new_h = int(el.h * current_scale)
        el.w = new_w
        el.h = new_h
        el.x = int(cx - new_w / 2.0)
        el.y = int(cy - new_h / 2.0)
        el.alpha = min(255.0, current_scale * 255.0 / max(self.to_scale, 0.001))
        el.update_bbox()
        return el


@dataclass
class ScaleOut(Animation):
    """
    Scale an element from its natural size down to `to_scale` (default 0.0).

    The element scales around its center point, so x/y are adjusted to
    keep the center stationary.

    Parameters
    ----------
    from_scale : float
        Starting scale multiplier (default 1.0 → element at its natural size).
    to_scale : float
        Ending scale multiplier (default 0.0 → element is invisible).
    duration_frames : int
        Frames to complete.
    easing : callable
        Easing function (default: ease_in).
    """
    from_scale: float = 1.0
    to_scale: float = 0.0
    duration_frames: int = 15
    easing: Callable[[float], float] = field(default_factory=lambda: ease_in)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        progress = self.easing(_clamp01(frame_t))
        current_scale = self.from_scale + (self.to_scale - self.from_scale) * progress
        if current_scale <= 0.0:
            el.alpha = 0.0
            return el
        cx = el.x + el.w / 2.0
        cy = el.y + el.h / 2.0
        new_w = int(el.w * current_scale)
        new_h = int(el.h * current_scale)
        el.w = new_w
        el.h = new_h
        el.x = int(cx - new_w / 2.0)
        el.y = int(cy - new_h / 2.0)
        el.alpha = min(255.0, current_scale * 255.0 / max(self.from_scale, 0.001))
        el.update_bbox()
        return el


# ---------------------------------------------------------------------------
# Pop  (scale-up then back to normal)
# ---------------------------------------------------------------------------

@dataclass
class Pop(Animation):
    """
    Scale the element to `peak_scale` then back to 1.0.

    Useful for emphasising an equation the moment it appears.

    Parameters
    ----------
    peak_scale : float
        Maximum scale during the pop (default 1.10).
    duration_frames : int
        Total frames for the pop animation.
    """
    peak_scale: float = 1.10
    duration_frames: int = 12

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        t = _clamp01(frame_t)
        # First half: scale up to peak; second half: scale back to 1.0
        if t < 0.5:
            scale = 1.0 + (self.peak_scale - 1.0) * ease_out(t * 2.0)
        else:
            scale = self.peak_scale + (1.0 - self.peak_scale) * ease_in_out((t - 0.5) * 2.0)
        cx = el.x + el.w / 2.0
        cy = el.y + el.h / 2.0
        new_w = int(el.w * scale)
        new_h = int(el.h * scale)
        el.w = new_w
        el.h = new_h
        el.x = int(cx - new_w / 2.0)
        el.y = int(cy - new_h / 2.0)
        el.update_bbox()
        return el


# ---------------------------------------------------------------------------
# Shake  (horizontal oscillation)
# ---------------------------------------------------------------------------

@dataclass
class Shake(Animation):
    """
    Shake the element horizontally to draw attention (e.g. wrong answer,
    limit exceeded).

    Parameters
    ----------
    amplitude_px : int
        Peak displacement in pixels (default 12).
    duration_frames : int
        Total frames for the shake.
    cycles : int
        Number of full oscillations during the shake (default 3).
    """
    amplitude_px: int = 12
    duration_frames: int = 18
    cycles: int = 3

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        t = _clamp01(frame_t)
        # Envelope: full amplitude at start, decays to 0
        envelope = 1.0 - ease_in_out(t)
        displacement = int(
            self.amplitude_px * envelope * math.sin(2.0 * math.pi * self.cycles * t)
        )
        el.x = el.x + displacement
        el.update_bbox()
        return el


# ---------------------------------------------------------------------------
# Pulse  (brief brightness / scale pulse)
# ---------------------------------------------------------------------------

@dataclass
class PulseOnce(Animation):
    """
    A single brief scale-up-and-back pulse.  Lighter than Pop — used as a
    hold animation to call attention without distracting.

    Parameters
    ----------
    peak_scale : float
        Maximum scale (default 1.05).
    duration_frames : int
        Frames for the full pulse cycle.
    """
    peak_scale: float = 1.05
    duration_frames: int = 10

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        t = _clamp01(frame_t)
        # Smooth bell-curve profile using a sine arch
        scale = 1.0 + (self.peak_scale - 1.0) * math.sin(math.pi * t)
        cx = el.x + el.w / 2.0
        cy = el.y + el.h / 2.0
        new_w = int(el.w * scale)
        new_h = int(el.h * scale)
        el.w = new_w
        el.h = new_h
        el.x = int(cx - new_w / 2.0)
        el.y = int(cy - new_h / 2.0)
        el.update_bbox()
        return el


# ---------------------------------------------------------------------------
# Subject-specific motion
# ---------------------------------------------------------------------------

@dataclass
class RotateSwing(Animation):
    """
    Swing an element around a pivot without changing its layout slot.

    Intended for objects like pendulums that should visibly arc around a
    fixed attachment point.
    """
    amplitude_deg: float = 12.0
    cycles: float = 1.5
    damping: float = 0.18
    duration_frames: int = 48
    pivot_rel: tuple[float, float] = (0.5, 0.06)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        t = _clamp01(frame_t)
        envelope = max(0.0, 1.0 - self.damping * t)
        angle = self.amplitude_deg * envelope * math.sin(2.0 * math.pi * self.cycles * t)
        el.rotation_deg = angle
        el.rotation_pivot_rel = self.pivot_rel
        el.asset_anchor_mode = "top_center"
        return el


@dataclass
class StretchOscillate(Animation):
    """
    Expand and compress an object horizontally around a stable anchor.

    Intended for springs and similar elastic objects that should stretch and
    rebound instead of holding as a still image.
    """
    amplitude: float = 0.18
    cycles: float = 2.0
    damping: float = 0.10
    duration_frames: int = 48
    anchor: str = "left"
    squash: float = 0.05

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        t = _clamp01(frame_t)
        envelope = max(0.0, 1.0 - self.damping * t)
        osc = math.sin(2.0 * math.pi * self.cycles * t)
        scale_x = max(0.75, 1.0 + self.amplitude * envelope * osc)
        scale_y = max(0.88, 1.0 - self.squash * envelope * abs(osc))

        base_x, base_y, base_w, base_h = element.x, element.y, element.w, element.h
        new_w = max(1, int(base_w * scale_x))
        new_h = max(1, int(base_h * scale_y))

        if self.anchor == "left":
            el.x = base_x
        elif self.anchor == "right":
            el.x = base_x + max(0, base_w - new_w)
        else:
            el.x = int(base_x + (base_w - new_w) / 2.0)

        el.y = int(base_y + (base_h - new_h) / 2.0)
        el.w = new_w
        el.h = new_h
        el.asset_anchor_mode = "left_center" if self.anchor == "left" else "center"
        el.update_bbox()
        return el


# ---------------------------------------------------------------------------
# TypeWriter
# ---------------------------------------------------------------------------

@dataclass
class TypeWriter(Animation):
    """
    Reveal the element's text character-by-character.

    The element's `text` attribute is truncated each frame.  Works only for
    text elements; image elements are returned unchanged.

    Parameters
    ----------
    chars_per_frame : float
        How many characters are revealed per frame (default 2.0).
    duration_frames : int
        Total frames to complete the reveal (overrides chars_per_frame if set).
        Set to 0 to use chars_per_frame instead.
    """
    chars_per_frame: float = 2.0
    duration_frames: int = 0  # 0 = derive from chars_per_frame + text length

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = _copy_element(element)
        if not element.text:
            return el
        total_chars = len(element.text)
        t = _clamp01(frame_t)
        if self.duration_frames > 0:
            visible = int(total_chars * t)
        else:
            visible = int(frame_t * self.chars_per_frame)
        visible = max(0, min(total_chars, visible))
        el.text = element.text[:visible]
        return el


# ---------------------------------------------------------------------------
# Composite animation: stack multiple animations on one element
# ---------------------------------------------------------------------------

@dataclass
class CompositeAnimation(Animation):
    """
    Apply multiple animations simultaneously to a single element.

    Each child animation receives the same `frame_t` and the transforms
    are applied in order (each receives the output of the previous).

    Parameters
    ----------
    animations : list[Animation]
        Ordered list of animations to apply.
    """
    animations: list = field(default_factory=list)

    def apply(self, element: LayoutElement, frame_t: float) -> LayoutElement:
        el = element
        for anim in self.animations:
            el = anim.apply(el, frame_t)
        return el


# ---------------------------------------------------------------------------
# Animation factory: build from string names used in scene dicts
# ---------------------------------------------------------------------------

_ANIM_REGISTRY: dict[str, type] = {
    "fade_in":    FadeIn,
    "fade_out":   FadeOut,
    "slide_left":  SlideIn,   # enters from left
    "slide_right": SlideIn,   # enters from right — direction resolved below
    "slide_up":    SlideIn,
    "slide_down":  SlideIn,
    "slide_out_left":  SlideOut,
    "slide_out_right": SlideOut,
    "slide_out_up":    SlideOut,
    "slide_out_down":  SlideOut,
    "scale_in":   ScaleIn,
    "pop":        Pop,
    "shake":      Shake,
    "pulse_once": PulseOnce,
    "rotate_swing": RotateSwing,
    "stretch_oscillate": StretchOscillate,
    "typewriter": TypeWriter,
}

_SLIDE_IN_DIRECTIONS = {
    "slide_left":  "left",
    "slide_right": "right",
    "slide_up":    "up",
    "slide_down":  "down",
}
_SLIDE_OUT_DIRECTIONS = {
    "slide_out_left":  "left",
    "slide_out_right": "right",
    "slide_out_up":    "up",
    "slide_out_down":  "down",
}


def animation_from_name(name: str, **kwargs) -> Animation:
    """
    Construct an Animation instance from a string identifier.

    The ``name`` must be a key in the animation registry.  Extra keyword
    arguments are passed to the constructor (e.g. duration_frames).

    Examples
    --------
    >>> anim = animation_from_name("slide_right", duration_frames=20)
    >>> anim = animation_from_name("fade_in")
    """
    if name not in _ANIM_REGISTRY:
        raise ValueError(
            f"Unknown animation {name!r}.  "
            f"Valid names: {sorted(_ANIM_REGISTRY)}"
        )
    cls = _ANIM_REGISTRY[name]
    if name in _SLIDE_IN_DIRECTIONS:
        kwargs.setdefault("direction", _SLIDE_IN_DIRECTIONS[name])
        return SlideIn(**kwargs)
    if name in _SLIDE_OUT_DIRECTIONS:
        kwargs.setdefault("direction", _SLIDE_OUT_DIRECTIONS[name])
        return SlideOut(**kwargs)
    return cls(**kwargs)
