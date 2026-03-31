"""
manim_renderer.py — Manim CE equation animation renderer.

Generates short animated equation clips for equation_reveal and derivation_step
scenes. Clips are cached at output/assets/equation_clips/{hash}.mp4.

If Manim CE is not installed this module degrades silently: all functions
return empty strings so the caller falls back to PIL-based rendering.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger("manim_renderer")

# ---------------------------------------------------------------------------
# Availability check — cached at module level so we only shell out once
# ---------------------------------------------------------------------------

_MANIM_AVAILABLE: Optional[bool] = None


def is_manim_available() -> bool:
    """Return True if Manim CE is installed and reachable on PATH.

    The result is cached after the first call so subsequent calls are free.
    """
    global _MANIM_AVAILABLE
    if _MANIM_AVAILABLE is not None:
        return _MANIM_AVAILABLE
    try:
        result = subprocess.run(
            ["manim", "--version"],
            capture_output=True,
            timeout=10,
        )
        _MANIM_AVAILABLE = result.returncode == 0
    except FileNotFoundError:
        _MANIM_AVAILABLE = False
    except subprocess.TimeoutExpired:
        _MANIM_AVAILABLE = False
    return _MANIM_AVAILABLE


# ---------------------------------------------------------------------------
# Plain-text → LaTeX conversion
# ---------------------------------------------------------------------------

def _equation_to_latex(text: str) -> str:
    """Convert a plain-text math string to a LaTeX-safe string.

    Replaces common Unicode math symbols with their LaTeX equivalents.
    Existing backslashes in the *original* input are escaped first so they
    don't collide with the backslashes we introduce.
    """
    # Escape pre-existing backslashes before we add our own
    result = text.replace("\\", "\\\\")

    # Unicode → LaTeX substitutions
    replacements = [
        ("²", "^{2}"),
        ("³", "^{3}"),
        ("×", r"\times"),
        ("·", r"\cdot"),
        ("√", r"\sqrt"),
        ("Δ", r"\Delta"),
        ("δ", r"\delta"),
        ("Ω", r"\Omega"),
        ("ω", r"\omega"),
    ]
    for char, latex in replacements:
        result = result.replace(char, latex)

    return result


# ---------------------------------------------------------------------------
# Manim script builder — single equation
# ---------------------------------------------------------------------------

def _build_manim_script(
    equation_text: str,
    caption_text: str,
    duration: float,
    background_hex: str,
    canvas_w: int,
    canvas_h: int,
) -> str:
    """Return a complete Manim CE Python script for an EquationReveal scene.

    The script is returned as a string; the caller writes it to a temp file
    before invoking the manim CLI.
    """
    latex_eq = _equation_to_latex(equation_text)

    # Clamp caption to 80 chars
    safe_caption = caption_text[:80] if caption_text else ""
    has_caption = bool(safe_caption)

    write_time = min(1.5, duration * 0.35)
    fade_time = min(0.8, duration * 0.2) if has_caption else 0.0
    hold_time = max(0.1, duration - write_time - fade_time)

    caption_block = ""
    caption_anim = ""
    caption_add = ""
    if has_caption:
        # Escape backslashes and quotes for embedding in the generated script
        escaped_caption = safe_caption.replace("\\", "\\\\").replace('"', '\\"')
        caption_block = f'''
    caption = Text("{escaped_caption}", font_size=28, color=LIGHT_GRAY)
    caption.next_to(eq, DOWN, buff=0.4)'''
        caption_add = "\n    self.add(caption)"
        caption_anim = f"\n    self.play(FadeIn(caption), run_time={fade_time!r})"

    script = f'''\
from manim import *

config.pixel_width = {canvas_w}
config.pixel_height = {canvas_h}
config.frame_rate = 30


class EquationReveal(Scene):
    def construct(self):
        self.camera.background_color = "{background_hex}"

        eq = MathTex(r"{latex_eq}").scale(2.2)
        eq.set_color(WHITE){caption_block}

        self.play(Write(eq), run_time={write_time!r}){caption_anim}
        self.wait({hold_time!r})
'''
    return script


# ---------------------------------------------------------------------------
# Manim script builder — derivation (multiple lines)
# ---------------------------------------------------------------------------

def _build_derivation_script(
    lines: list[str],
    caption_text: str,
    duration: float,
    background_hex: str,
    canvas_w: int,
    canvas_h: int,
) -> str:
    """Return a Manim CE script that reveals each derivation line in turn."""
    n = max(len(lines), 1)
    time_per_line = duration / n

    # Clamp caption to 80 chars
    safe_caption = caption_text[:80] if caption_text else ""
    has_caption = bool(safe_caption)

    # Build MathTex lines
    latex_lines = [_equation_to_latex(line) for line in lines]
    mathtex_defs = "\n        ".join(
        f'line{i} = MathTex(r"{lat}").set_color(WHITE)'
        for i, lat in enumerate(latex_lines)
    )
    vgroup_items = ", ".join(f"line{i}" for i in range(n))

    caption_block = ""
    caption_anim = ""
    if has_caption:
        escaped_caption = safe_caption.replace("\\", "\\\\").replace('"', '\\"')
        caption_block = f'''
        caption = Text("{escaped_caption}", font_size=28, color=LIGHT_GRAY)
        caption.next_to(group, DOWN, buff=0.5)'''
        fade_time = min(0.8, duration * 0.2)
        caption_anim = f"\n        self.play(FadeIn(caption), run_time={fade_time!r})"

    # Build sequential Write animations — each line gets time_per_line
    write_time = min(1.5, time_per_line * 0.6)
    wait_time = max(0.05, time_per_line - write_time)
    anim_lines = "\n        ".join(
        f"self.play(Write(line{i}), run_time={write_time!r})\n"
        f"        self.wait({wait_time!r})"
        for i in range(n)
    )

    script = f'''\
from manim import *

config.pixel_width = {canvas_w}
config.pixel_height = {canvas_h}
config.frame_rate = 30


class EquationReveal(Scene):
    def construct(self):
        self.camera.background_color = "{background_hex}"

        {mathtex_defs}

        group = VGroup({vgroup_items}).arrange(DOWN, buff=0.4)
        group.move_to(ORIGIN){caption_block}

        {anim_lines}{caption_anim}
'''
    return script


# ---------------------------------------------------------------------------
# Shared render helper
# ---------------------------------------------------------------------------

def _run_render(
    script_src: str,
    cache_key: str,
    project_root: Path,
) -> str:
    """Write *script_src* to a temp dir, invoke manim, copy result to cache.

    Returns the absolute path string of the cached MP4, or ``""`` on failure.
    """
    cache_dir = project_root / "output" / "assets" / "equation_clips"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"eq_{cache_key}.mp4"

    # Return early if a warm cached file exists and is non-trivially sized
    if cache_file.exists() and cache_file.stat().st_size > 10 * 1024:
        return str(cache_file)

    work_dir = tempfile.mkdtemp(prefix="manim_eq_")
    try:
        script_path = Path(work_dir) / "eq_scene.py"
        script_path.write_text(script_src, encoding="utf-8")

        media_dir = Path(work_dir) / "media"
        media_dir.mkdir()

        cmd = [
            "manim",
            "-ql",
            "--format=mp4",
            "--media_dir", str(media_dir),
            str(script_path),
            "EquationReveal",
        ]
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            logger.warning(
                "manim exited with code %d.\nstdout: %s\nstderr: %s",
                result.returncode,
                result.stdout[-2000:],
                result.stderr[-2000:],
            )
            return ""

        # Locate the output MP4 — prefer exact name match
        found_mp4: Optional[Path] = None
        for candidate in media_dir.rglob("EquationReveal.mp4"):
            found_mp4 = candidate
            break
        if found_mp4 is None:
            for candidate in media_dir.rglob("*.mp4"):
                found_mp4 = candidate
                break

        if found_mp4 is None:
            logger.warning("manim succeeded but no MP4 found under %s", media_dir)
            return ""

        shutil.copy2(found_mp4, cache_file)
        return str(cache_file)

    except Exception as exc:  # noqa: BLE001
        logger.warning("manim render failed: %s", exc)
        return ""
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def render_equation_clip(
    equation_text: str,
    caption_text: str = "",
    duration: float = 5.0,
    aspect_ratio: str = "16:9",
    background_color: tuple[int, int, int] = (38, 38, 38),
    project_root: Optional[Path] = None,
) -> str:
    """Render an animated equation reveal clip via Manim CE.

    Parameters
    ----------
    equation_text:
        Plain-text math expression (Unicode symbols supported).
    caption_text:
        Optional subtitle line shown below the equation (max 80 chars).
    duration:
        Total clip duration in seconds.
    aspect_ratio:
        ``"16:9"`` for YouTube Long (1920×1080) or ``"9:16"`` for Shorts
        (1080×1920).
    background_color:
        RGB tuple for the scene background; defaults to near-black (38,38,38).
    project_root:
        Repository root used to resolve the cache directory.  Defaults to two
        levels above this file (i.e. the repo root).

    Returns
    -------
    str
        Absolute path to the cached MP4, or ``""`` if rendering failed or
        Manim CE is not available.
    """
    if not is_manim_available():
        return ""

    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]

    bg_hex = "#{:02x}{:02x}{:02x}".format(*background_color)
    canvas = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)

    cache_key = hashlib.sha256(
        json.dumps(
            [equation_text, caption_text, round(duration, 2), bg_hex, list(canvas)]
        ).encode()
    ).hexdigest()[:16]

    # Fast path — check cache before building script
    cache_dir = project_root / "output" / "assets" / "equation_clips"
    cache_file = cache_dir / f"eq_{cache_key}.mp4"
    if cache_file.exists() and cache_file.stat().st_size > 10 * 1024:
        return str(cache_file)

    script = _build_manim_script(
        equation_text=equation_text,
        caption_text=caption_text,
        duration=duration,
        background_hex=bg_hex,
        canvas_w=canvas[0],
        canvas_h=canvas[1],
    )

    return _run_render(script, cache_key, project_root)


def render_derivation_clip(
    lines: list[str],
    caption_text: str = "",
    duration: float = 5.0,
    aspect_ratio: str = "16:9",
    background_color: tuple[int, int, int] = (38, 38, 38),
    project_root: Optional[Path] = None,
) -> str:
    """Render an animated multi-line derivation clip via Manim CE.

    Each line in *lines* is revealed sequentially with a ``Write`` animation,
    stacked vertically in a ``VGroup``.

    Parameters
    ----------
    lines:
        Ordered list of plain-text math expressions, e.g.
        ``["F = ma", "a = F/m"]``.
    caption_text:
        Optional subtitle line shown below all equations (max 80 chars).
    duration:
        Total clip duration in seconds.
    aspect_ratio:
        ``"16:9"`` or ``"9:16"``.
    background_color:
        RGB tuple for the scene background.
    project_root:
        Repository root; defaults to two levels above this file.

    Returns
    -------
    str
        Absolute path to the cached MP4, or ``""`` on any failure.
    """
    if not is_manim_available():
        return ""

    if project_root is None:
        project_root = Path(__file__).resolve().parents[2]

    bg_hex = "#{:02x}{:02x}{:02x}".format(*background_color)
    canvas = (1920, 1080) if aspect_ratio == "16:9" else (1080, 1920)

    cache_key = hashlib.sha256(
        json.dumps(
            [lines, caption_text, round(duration, 2), bg_hex, list(canvas)]
        ).encode()
    ).hexdigest()[:16]

    # Fast path — check cache before building script
    cache_dir = project_root / "output" / "assets" / "equation_clips"
    cache_file = cache_dir / f"eq_{cache_key}.mp4"
    if cache_file.exists() and cache_file.stat().st_size > 10 * 1024:
        return str(cache_file)

    script = _build_derivation_script(
        lines=lines,
        caption_text=caption_text,
        duration=duration,
        background_hex=bg_hex,
        canvas_w=canvas[0],
        canvas_h=canvas[1],
    )

    return _run_render(script, cache_key, project_root)
