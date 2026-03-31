"""
episode_renderer.py — The missing link between scenes.json and rendered MP4.

This module completes the production pipeline:

    script.md
        → parse_script + SceneMapper
        → automatic slide_planner
        → SceneTimeline per scene              (THIS MODULE: build_scene_timeline)
        → PNG frames per scene                 (THIS MODULE: render_episode)
        → per-scene MP4s                       (THIS MODULE: render_episode)
        → concatenated episode MP4             (THIS MODULE: render_episode)

Public API
----------
build_scene_timeline(scene_dict, aspect_ratio, fps) → SceneTimeline
    Dispatch a single scene descriptor dict to the right scene_types factory.

render_episode(script_path, output_mp4, aspect_ratio, fps, work_dir) → str
    Full pipeline: script → scenes → render → MP4.

render_all_episodes(physics_dir, output_base, aspect_ratio, fps) → list[dict]
    Walk the physics output tree and render every *_youtube_long.md script.
"""

from __future__ import annotations

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from src.animation.scene_types import (
    equation_reveal_scene,
    character_introduction_scene,
    derivation_step_scene,
    diagram_explanation_scene,
    historical_moment_scene,
    limits_breakdown_scene,
    storybook_object_demo_scene,
    storybook_comparison_split_scene,
    storybook_hook_title_card_scene,
    storybook_outro_bridge_scene,
    storybook_timeline_sequence_scene,
    two_character_debate_scene,
    worked_example_scene,
)
from src.animation.timeline import SceneTimeline, ElementTimeline
from src.animation.ffmpeg_export import frames_to_video
from src.layout.element import LayoutElement
from src.pipeline.scene_mapper import map_script_to_scenes
from src.pipeline.script_parser import parse_script
from src.pipeline.slide_planner import apply_layout_plan
from src.asset_registry import get_registry

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Storybook palette — warm cream used when no background asset is available
# ---------------------------------------------------------------------------
_BG_CREAM  = (245, 240, 228)
_BG_CHALK  = (38,  38,  38)   # near-black for "chalkboard" templates
_BG_CLEAN  = (248, 248, 248)

_TEMPLATE_BG_COLOR = {
    "equation_reveal":        _BG_CHALK,
    "derivation_step":        _BG_CHALK,
    "character_scene":        _BG_CREAM,
    "historical_moment":      _BG_CREAM,
    "two_character_debate":   _BG_CREAM,
    "two_element_comparison": _BG_CLEAN,
    "diagram_explanation":    _BG_CLEAN,
    "animation_scene":        _BG_CLEAN,
    "object_demo":            _BG_CLEAN,
    "timeline_sequence":      _BG_CREAM,
    "narration_with_caption": _BG_CREAM,
    "limits_breakdown":       _BG_CREAM,
    "worked_example":         _BG_CLEAN,
    "outro_bridge":           _BG_CREAM,
}

_AUDIO_CANDIDATE_NAMES = (
    "narration.mp3",
    "narration.m4a",
    "narration.aac",
    "narration.wav",
)

_ANIMATION_FALLBACK_ASSETS = (
    ("ball", "data/assets/physics/objects/obj_ball_red.png"),
    ("sphere", "data/assets/physics/objects/obj_ball_red.png"),
    ("apple", "data/assets/physics/test_v3/obj_apple_green.png"),   # no production version yet
    ("ramp", "data/assets/physics/objects/obj_ramp_wood.png"),
    ("pendulum", "data/assets/physics/objects/obj_pendulum.png"),
    ("spring", "data/assets/physics/objects/obj_coil_spring.png"),
    ("earth", "data/assets/physics/objects/obj_earth_globe.png"),
    ("globe", "data/assets/physics/objects/obj_earth_globe.png"),
    ("arrow", "data/assets/physics/objects/obj_arrow_right.png"),
    ("cloud", "data/assets/physics/test_v3/obj_cloud.png"),
    ("tree", "data/assets/physics/test_v3/obj_tree_round.png"),
)

_ANIMATION_ACCENT_ASSETS = (
    (("air", "wind", "flow", "rush", "streamline"), "data/assets/physics/objects/obj_airflow_streamlines.png"),
)

_CHARACTER_BACKGROUND_HINTS = {
    "aristotle": "data/assets/physics/backgrounds/bg_ancient_greek_courtyard.png",
    "newton":    "data/assets/physics/backgrounds/bg_grass_field.png",
    "galileo":   "data/assets/physics/backgrounds/bg_grass_field.png",
    "descartes": "data/assets/physics/backgrounds/bg_grass_field.png",
    "leibniz":   "data/assets/physics/backgrounds/bg_grass_field.png",
    "kepler":    "data/assets/physics/backgrounds/bg_grass_field.png",
    "euler":     "data/assets/physics/backgrounds/bg_grass_field.png",
    "lagrange":  "data/assets/physics/backgrounds/bg_grass_field.png",
    "hamilton":  "data/assets/physics/backgrounds/bg_grass_field.png",
    "noether":   "data/assets/physics/backgrounds/bg_grass_field.png",
}

_SUBJECT_BACKGROUND_HINTS = (
    (("space", "orbit", "planet", "star", "moon", "galaxy", "earth", "globe"), "data/assets/physics/backgrounds/bg_deep_space.png"),
    (("ice", "skate", "slip", "frictionless"), "data/assets/physics/backgrounds/bg_ice_surface.png"),
    (("aristotle", "greece", "greek", "athens"), "data/assets/physics/backgrounds/bg_ancient_greek_courtyard.png"),
    (("ball", "apple", "ramp", "field", "throw", "projectile", "air", "wind", "flow"), "data/assets/physics/backgrounds/bg_grass_field.png"),
)

_OBJECT_MOTION_HINTS = (
    (("pendulum", "oscillat", "swing"), "pendulum_swing"),
    (("spring", "coil", "elastic", "hooke"), "spring_stretch"),
)

_DEFAULT_TTS_VOICE = os.environ.get("SCIENCE_EDU_TTS_VOICE", "en-US-GuyNeural")
_DEFAULT_TTS_RATE = os.environ.get("SCIENCE_EDU_TTS_RATE", "-4%")
_DEFAULT_TTS_PITCH = os.environ.get("SCIENCE_EDU_TTS_PITCH", "+0Hz")


# ---------------------------------------------------------------------------
# VTT / subtitle helpers
# ---------------------------------------------------------------------------

def _vtt_timestamp_to_seconds(ts: str) -> float:
    """Convert WebVTT timestamp (HH:MM:SS.mmm or MM:SS.mmm) to float seconds."""
    ts = ts.strip()
    parts = ts.replace(",", ".").split(":")
    try:
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
        elif len(parts) == 2:
            return int(parts[0]) * 60 + float(parts[1])
        return float(parts[0])
    except (ValueError, IndexError):
        return 0.0


def _parse_vtt_cues(vtt_path: str) -> list[tuple[float, float, str]]:
    """
    Parse a WebVTT file and return a list of (start_sec, end_sec, text) tuples.
    Text is stripped of tags and whitespace-normalised.
    """
    cues: list[tuple[float, float, str]] = []
    try:
        with open(vtt_path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return cues

    # Strip WEBVTT header and NOTE blocks
    blocks = re.split(r"\n\n+", content.strip())
    for block in blocks:
        block = block.strip()
        if not block or block.startswith("WEBVTT") or block.startswith("NOTE"):
            continue
        lines = block.splitlines()
        # Find the timestamp line (contains " --> ")
        ts_line = next((l for l in lines if " --> " in l), None)
        if ts_line is None:
            continue
        ts_parts = ts_line.split(" --> ", 1)
        start = _vtt_timestamp_to_seconds(ts_parts[0])
        end   = _vtt_timestamp_to_seconds(ts_parts[1].split()[0])  # ignore position hints
        # Text lines: everything after the timestamp line, strip inline tags
        text_lines = lines[lines.index(ts_line) + 1:]
        text = " ".join(re.sub(r"<[^>]+>", "", l).strip() for l in text_lines if l.strip())
        if text:
            cues.append((start, end, text))
    return cues


def _parse_vtt_duration(vtt_path: str) -> float:
    """Return the end timestamp of the last cue in a VTT file, in seconds."""
    cues = _parse_vtt_cues(vtt_path)
    if not cues:
        return 0.0
    return max(end for _, end, _ in cues)


def _get_media_duration_ffprobe(path: str) -> float:
    """Return duration of any media file in seconds using ffprobe, or 0.0 on failure."""
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", path],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode == 0:
            import json as _json
            data = _json.loads(result.stdout)
            dur = float(data.get("format", {}).get("duration", 0))
            return dur
    except Exception:
        pass
    return 0.0


def _vtt_to_srt(vtt_path: str, srt_path: str) -> bool:
    """
    Convert a WebVTT file to SRT format for use with ffmpeg subtitles filter.
    Returns True on success.
    """
    cues = _parse_vtt_cues(vtt_path)
    if not cues:
        return False

    def _fmt(seconds: float) -> str:
        h = int(seconds // 3600)
        m = int((seconds % 3600) // 60)
        s = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    try:
        with open(srt_path, "w", encoding="utf-8") as fh:
            for i, (start, end, text) in enumerate(cues, 1):
                fh.write(f"{i}\n{_fmt(start)} --> {_fmt(end)}\n{text}\n\n")
        return True
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Asset pre-flight check
# ---------------------------------------------------------------------------

def _preflight_scenes(scenes: list[dict], script_path: str) -> list[str]:
    """
    Check all asset paths referenced in scene descriptors before rendering begins.
    Returns a list of warning strings for any unresolvable non-placeholder assets.
    """
    warnings: list[str] = []
    root = _project_root()
    seen: set[str] = set()

    for scene in scenes:
        bg = scene.get("background", "")
        if bg and not bg.startswith("PLACEHOLDER:") and bg not in seen:
            seen.add(bg)
            p = Path(bg) if Path(bg).is_absolute() else root / bg
            if not p.is_file():
                warnings.append(f"Missing background: {bg}  (scene {scene.get('scene_id')})")

        for el in scene.get("elements", []):
            asset = el.get("asset_path") or ""
            if not asset or asset.startswith("PLACEHOLDER:") or asset in seen:
                continue
            seen.add(asset)
            p = Path(asset) if Path(asset).is_absolute() else root / asset
            if not p.is_file():
                warnings.append(f"Missing asset: {asset}  (scene {scene.get('scene_id')} role={el.get('role')})")

    return warnings


# ---------------------------------------------------------------------------
# Per-shot persistence helpers
# ---------------------------------------------------------------------------

def _scene_dict_hash(scene_dict: dict) -> str:
    """Compute a 16-char hex hash of a scene dict for cache invalidation.
    Layout-computed and debug keys are excluded so re-planning without content
    changes does not bust the cache.
    """
    import hashlib
    EXCLUDE = {"_source_visual_cue", "_source_segment", "layout_plan"}
    clean = {k: v for k, v in scene_dict.items() if k not in EXCLUDE}
    blob = json.dumps(clean, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


def _load_scene_manifest(scenes_dir: Path) -> dict:
    """Load the per-episode scene manifest, returning {} on any failure."""
    path = scenes_dir / "scene_manifest.json"
    if path.is_file():
        try:
            with open(path, encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            pass
    return {}


def _save_scene_manifest(scenes_dir: Path, manifest: dict) -> None:
    """Atomically write the scene manifest."""
    scenes_dir.mkdir(parents=True, exist_ok=True)
    tmp = scenes_dir / "scene_manifest.tmp.json"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(manifest, fh, indent=2)
    os.replace(tmp, scenes_dir / "scene_manifest.json")


def _scenes_dir_for_script(script_path: str) -> Path:
    """Return the persistent per-shot scenes directory next to an episode's media dir."""
    return _media_dir_for_script(script_path) / "scenes"


def _try_manim_equation(scene_dict: dict, aspect_ratio: str, fps: int) -> str:
    """
    Attempt to render an equation/derivation scene with Manim CE.
    Returns the path to a rendered MP4, or "" if Manim is unavailable or fails.
    """
    try:
        from src.animation.manim_renderer import render_equation_clip, render_derivation_clip, is_manim_available
        if not is_manim_available():
            return ""
    except ImportError:
        return ""

    elements  = scene_dict.get("elements", [])
    template  = scene_dict.get("template", "")
    duration  = float(scene_dict.get("duration", 5.0))
    bg_color  = _TEMPLATE_BG_COLOR.get(template, _BG_CHALK)

    cap_el = _get_el(elements, "caption")
    caption_text = _text(cap_el)

    if template == "derivation_step":
        # Gather equation lines from timeline + headline elements
        lines = [_text(el) for el in elements if el.get("role") in ("timeline", "headline") and _text(el)]
        if not lines:
            return ""
        return render_derivation_clip(
            lines=lines,
            caption_text=caption_text,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
        )
    else:
        eq_el = _get_el(elements, "equation_center")
        if not eq_el:
            return ""
        raw_eq = _text(eq_el, "?")
        import re as _re
        clean_eq = _re.sub(r"^(equation appearing|equation)\s*:\s*", "", raw_eq, flags=_re.IGNORECASE).strip()
        return render_equation_clip(
            equation_text=clean_eq or raw_eq,
            caption_text=caption_text,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
        )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_el(elements: list[dict], role: str) -> Optional[dict]:
    """Return the first element with the given role, or None."""
    for el in elements:
        if el.get("role") == role:
            return el
    return None


def _text(el: Optional[dict], fallback: str = "") -> str:
    if el is None:
        return fallback
    return (el.get("text") or fallback).strip()


def _get_els(elements: list[dict], role: str) -> list[dict]:
    return [el for el in elements if el.get("role") == role]


def _asset(el: Optional[dict]) -> str:
    if el is None:
        return ""
    path = el.get("asset_path") or ""
    # Treat PLACEHOLDER: strings as missing
    if path.startswith("PLACEHOLDER:") or not path:
        return ""
    if os.path.isabs(path):
        return path
    candidate = _project_root() / path
    return str(candidate) if candidate.is_file() else path


def _rect_from_el(el: Optional[dict]) -> Optional[tuple[int, int, int, int]]:
    if el is None:
        return None
    if not all(key in el for key in ("x", "y", "w", "h")):
        return None
    rect = tuple(int(el.get(key, 0)) for key in ("x", "y", "w", "h"))
    if rect[2] <= 0 or rect[3] <= 0:
        return None
    return rect


def _name_from_asset(asset_path: str) -> str:
    """Extract a display name from a character asset path like char_newton.png."""
    m = re.search(r"char_([a-z0-9_]+)", asset_path or "")
    if m:
        name = re.sub(r"_v\d+$|_v$", "", m.group(1))
        return name.replace("_", " ").title()
    return "Unknown"


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _media_dir_for_script(script_path: str) -> Path:
    script = Path(script_path).resolve()
    return script.parent.parent / "media"


def _background_for_character(asset_path: str, fallback: str = "") -> str:
    name = _name_from_asset(asset_path).lower()
    # Registry primary lookup
    try:
        registry = get_registry()
        result = registry.find(name, asset_type="background")
        if result:
            return result
    except Exception:
        pass
    # Hardcoded fallback
    rel_path = _CHARACTER_BACKGROUND_HINTS.get(name)
    if not rel_path:
        return fallback
    asset = _project_root() / rel_path
    return str(asset) if asset.is_file() else fallback


def _background_for_subject(*subjects: str, fallback: str = "") -> str:
    combined = " ".join((subject or "") for subject in subjects).lower()
    if not combined.strip():
        return fallback
    # Registry primary lookup — try meaningful words from the combined subject text
    try:
        registry = get_registry()
        for word in combined.split():
            if len(word) >= 4:
                result = registry.find(word, asset_type="background")
                if result:
                    return result
    except Exception:
        pass
    # Hardcoded fallback
    for keywords, rel_path in _SUBJECT_BACKGROUND_HINTS:
        if any(keyword in combined for keyword in keywords):
            asset = _project_root() / rel_path
            if asset.is_file():
                return str(asset)
    return fallback


def _motion_profile_for_subject(*subjects: str) -> str:
    combined_parts: list[str] = []
    for subject in subjects:
        if not subject:
            continue
        combined_parts.append(subject)
        combined_parts.append(os.path.basename(subject))
    combined = " ".join(combined_parts).lower()
    if not combined.strip():
        return ""
    for keywords, profile in _OBJECT_MOTION_HINTS:
        if any(keyword in combined for keyword in keywords):
            return profile
    return ""


def _resolve_sibling_audio(script_path: str) -> str:
    """
    Resolve narration audio next to a script if the production pipeline wrote it.

    Expected location is the episode media directory, e.g.
    ``.../ep01_xxx/scripts/ep01_youtube_long.md`` → ``.../ep01_xxx/media/narration.mp3``.
    """
    script = Path(script_path).resolve()
    media_dir = _media_dir_for_script(script_path)
    if not media_dir.is_dir():
        return ""

    stem = script.stem
    candidates = [media_dir / name for name in _AUDIO_CANDIDATE_NAMES]
    candidates.extend([
        media_dir / f"{stem}.mp3",
        media_dir / f"{stem}.m4a",
        media_dir / f"{stem}.aac",
        media_dir / f"{stem}.wav",
        media_dir / f"{stem.replace('_youtube_long', '')}_narration.mp3",
        media_dir / f"{stem.replace('_youtube_long', '')}_narration.m4a",
    ])

    for candidate in candidates:
        if candidate.is_file():
            return str(candidate)
    return ""


def _build_narration_text(script_path: str) -> str:
    parsed = parse_script(script_path)
    lines: list[str] = []
    for segment in parsed.segments:
        if not segment.narrator_lines:
            continue
        lines.append(" ".join(line.strip() for line in segment.narrator_lines if line.strip()))
    return "\n\n".join(line for line in lines if line).strip()


def _generate_tts_audio(script_path: str, *, voice: str = _DEFAULT_TTS_VOICE, rate: str = _DEFAULT_TTS_RATE, pitch: str = _DEFAULT_TTS_PITCH) -> str:
    if os.environ.get("SCIENCE_EDU_TTS_DISABLE") == "1":
        return ""
    narration_text = _build_narration_text(script_path)
    if not narration_text:
        return ""

    media_dir = _media_dir_for_script(script_path)
    media_dir.mkdir(parents=True, exist_ok=True)
    audio_path = media_dir / "narration.mp3"
    subtitles_path = media_dir / "narration.vtt"

    fd, temp_text_path = tempfile.mkstemp(prefix="tts_", suffix=".txt")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(narration_text)
        cmd = [
            "edge-tts",
            "--file", temp_text_path,
            "--voice", voice,
            "--rate", rate,
            "--pitch", pitch,
            "--write-media", str(audio_path),
            "--write-subtitles", str(subtitles_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0 or not audio_path.is_file():
            log.warning("edge-tts generation failed for %s: %s", script_path, result.stderr[-1000:])
            return ""
        return str(audio_path)
    finally:
        try:
            os.remove(temp_text_path)
        except OSError:
            pass


def _ensure_sibling_audio(script_path: str) -> str:
    existing = _resolve_sibling_audio(script_path)
    if existing:
        return existing
    return _generate_tts_audio(script_path)


def _resolve_sibling_vtt(script_path: str) -> str:
    """Return path to narration.vtt in the episode media dir if it exists."""
    vtt = _media_dir_for_script(script_path) / "narration.vtt"
    return str(vtt) if vtt.is_file() else ""


def _mux_audio_into_video(video_path: str, audio_path: str, vtt_path: str = "") -> None:
    """
    Mux narration audio into an existing MP4 with three improvements over the
    old -shortest approach:

    1. Pad video to audio duration  — if the audio is longer than the video,
       the last frame is frozen rather than content being cut off.
    2. Subtitle burn-in            — if a WebVTT file is supplied it is
       converted to SRT and burned into the video via the subtitles filter.
    3. Never drops content         — audio is always the authoritative duration.
    """
    if not audio_path or not os.path.isfile(audio_path) or not os.path.isfile(video_path):
        return

    video = Path(video_path)
    tmp_output = video.with_suffix(".muxed.mp4")

    # ------------------------------------------------------------------ #
    # Determine duration drift
    # ------------------------------------------------------------------ #
    audio_dur = 0.0
    if vtt_path and os.path.isfile(vtt_path):
        audio_dur = _parse_vtt_duration(vtt_path)
    if audio_dur <= 0.0:
        audio_dur = _get_media_duration_ffprobe(audio_path)
    video_dur = _get_media_duration_ffprobe(video_path)

    pad_secs = max(0.0, audio_dur - video_dur) if audio_dur > 1.0 and video_dur > 1.0 else 0.0
    if pad_secs > 0.5:
        log.info("Audio longer than video by %.1fs — padding last frame", pad_secs)

    # ------------------------------------------------------------------ #
    # Build video filter chain
    # ------------------------------------------------------------------ #
    vf_parts: list[str] = []

    if pad_secs > 0.5:
        vf_parts.append(f"tpad=stop_mode=clone:stop_duration={pad_secs:.3f}")

    srt_path = ""
    if vtt_path and os.path.isfile(vtt_path):
        srt_path = str(video.with_suffix(".tmp_subs.srt"))
        if _vtt_to_srt(vtt_path, srt_path):
            # Escape the path for the ffmpeg filter string
            esc = srt_path.replace("\\", "/").replace("'", "\\'").replace(":", "\\:")
            vf_parts.append(
                f"subtitles='{esc}':force_style='"
                "FontName=Arial,FontSize=26,"
                "PrimaryColour=&H00FFFFFF,"
                "OutlineColour=&H00000000,"
                "BackColour=&H80000000,"
                "BorderStyle=4,Outline=1,Shadow=0,"
                "Alignment=2,MarginV=40'"
            )
        else:
            srt_path = ""

    # ------------------------------------------------------------------ #
    # Build ffmpeg command
    # ------------------------------------------------------------------ #
    cmd = ["ffmpeg", "-y", "-i", str(video), "-i", audio_path]

    if vf_parts:
        cmd += ["-vf", ",".join(vf_parts), "-c:v", "libx264", "-crf", "23", "-preset", "fast"]
    else:
        cmd += ["-c:v", "copy"]

    cmd += ["-c:a", "aac", "-b:a", "192k", "-shortest", "-movflags", "+faststart", str(tmp_output)]

    result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)

    # Clean up temp SRT regardless of outcome
    if srt_path and os.path.isfile(srt_path):
        try:
            os.remove(srt_path)
        except OSError:
            pass

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg audio mux failed (rc={result.returncode}):\n"
            f"{result.stderr[-2000:]}"
        )
    os.replace(tmp_output, video)


def _animation_scene_fallback_asset(cue: str) -> str:
    """
    Choose a concrete prop asset for simple animation cues when no diagram is provided.
    Uses the asset registry as the primary lookup; falls back to hardcoded dict.
    """
    lower = cue.lower()
    # Registry primary lookup — try each word in the cue
    try:
        registry = get_registry()
        for word in lower.split():
            if len(word) >= 3:
                result = registry.find(word, asset_type="object")
                if result:
                    return result
    except Exception:
        pass
    # Hardcoded fallback
    for keyword, rel_path in _ANIMATION_FALLBACK_ASSETS:
        if keyword in lower:
            asset = _project_root() / rel_path
            if asset.is_file():
                return str(asset)
    return ""


def _animation_scene_accent_asset(cue: str) -> str:
    lower = cue.lower()
    for keywords, rel_path in _ANIMATION_ACCENT_ASSETS:
        if any(keyword in lower for keyword in keywords):
            asset = _project_root() / rel_path
            if asset.is_file():
                return str(asset)
    return ""


def _short_text(text: str, limit: int = 40) -> str:
    text = text.strip()
    if len(text) <= limit:
        return text
    shortened = text[:limit].rsplit(" ", 1)[0].strip()
    return shortened or text[:limit].strip()


def _first_clause(text: str, limit: int = 44) -> str:
    text = text.strip()
    if not text:
        return ""
    for separator in (". ", "; ", ": ", ", "):
        if separator in text:
            clause = text.split(separator, 1)[0].strip(" ,.;:")
            if clause:
                return _short_text(clause, limit=limit)
    return _short_text(text, limit=limit)


def _split_title_and_caption(text: str, title_limit: int = 28) -> tuple[str, str]:
    text = text.strip()
    if not text:
        return "", ""
    for separator in (". ", "; ", ": ", ", "):
        if separator in text:
            head, tail = text.split(separator, 1)
            title = _short_text(head.strip(" ,.;:"), limit=title_limit)
            caption = tail.strip()
            return title or _short_text(text, limit=title_limit), caption or text
    title = _first_clause(text, limit=title_limit)
    return title, text


def _split_metadata(text: str) -> tuple[str, str]:
    text = text.strip()
    if not text:
        return "", ""
    for separator in ("·", "|", " - ", ", "):
        if separator in text:
            left, right = text.split(separator, 1)
            return left.strip(), right.strip()
    return text, ""


def _split_stage_text(text: str) -> tuple[str, str]:
    text = text.strip()
    if not text:
        return "", ""
    for separator in ("|", "·", ";"):
        if separator in text:
            year, label = text.split(separator, 1)
            return year.strip(), label.strip()
    return "", text


# ---------------------------------------------------------------------------
# Background injection helper
# ---------------------------------------------------------------------------

def _inject_background(tl: SceneTimeline, bg_asset: str) -> SceneTimeline:
    """
    If bg_asset is a valid image path and the timeline has no background image
    element, insert a full-canvas background element at z=0.
    """
    if not bg_asset or not os.path.isfile(bg_asset):
        return tl
    # Check if a background image element already exists
    for et in tl.elements:
        if et.element.role == "background" and et.element.asset_path:
            return tl  # already has a background image
    # Build a full-canvas background element
    cw, ch = tl.canvas_size
    bg_el = LayoutElement(
        role="background",
        asset_path=bg_asset,
        text=None,
        color=(0, 0, 0),
    )
    bg_el.x, bg_el.y = 0, 0
    bg_el.w, bg_el.h = cw, ch
    bg_el.z = 0
    bg_el.update_bbox()
    tl.elements.insert(0, ElementTimeline(
        element=bg_el,
        enter_frame=0,
        exit_frame=tl.total_frames,
    ))
    # Re-sort by z so background renders first
    tl.elements.sort(key=lambda et: et.element.z)
    return tl


# ---------------------------------------------------------------------------
# Scene dispatcher
# ---------------------------------------------------------------------------

def build_scene_timeline(
    scene_dict: dict,
    aspect_ratio: str = "16:9",
    fps: int = 30,
):
    """
    Convert a scene descriptor dict (as produced by SceneMapper) to a
    SceneTimeline ready for rendering.

    Parameters
    ----------
    scene_dict : dict
        A single scene descriptor with keys: template, duration, background,
        elements (and optional _source_* debug keys).
    aspect_ratio : str
        "16:9" (YouTube long-form) or "9:16" (Shorts / TikTok).
    fps : int
        Frames per second.

    Returns
    -------
    SceneTimeline
    """
    scene_dict = apply_layout_plan(scene_dict, aspect_ratio=aspect_ratio)
    template  = scene_dict.get("template", "narration_with_caption")
    elements  = scene_dict.get("elements", [])
    duration  = float(scene_dict.get("duration", 5.0))
    bg_asset  = scene_dict.get("background", "")
    layout_rects = (scene_dict.get("layout_plan") or {}).get("rects") or {}
    archetype = (scene_dict.get("layout_plan") or {}).get("archetype", "")
    bg_color  = _TEMPLATE_BG_COLOR.get(template, _BG_CREAM)

    # Resolve background: convert relative paths to absolute using project root
    if bg_asset and not os.path.isabs(bg_asset):
        _project_root = Path(__file__).resolve().parents[2]
        bg_asset = str(_project_root / bg_asset)
    if bg_asset and not os.path.isfile(bg_asset):
        bg_asset = ""  # file doesn't exist — fall back to solid color

    def _render_equation_focus() -> SceneTimeline:
        eq_el  = _get_el(elements, "equation_center")
        cap_el = _get_el(elements, "caption")
        raw_eq = _text(eq_el, "?")
        # Strip "equation appearing:" / "equation:" prefix if scene mapper left it in
        clean_eq = re.sub(r"^(equation appearing|equation)\s*:\s*", "", raw_eq, flags=re.IGNORECASE).strip()
        return equation_reveal_scene(
            equation_text=clean_eq or raw_eq,
            narrator_text=_text(cap_el),
            background=bg_asset,
            equation_rect=_rect_from_el(eq_el) or scene_dict.get("equation_rect"),
            caption_rect=_rect_from_el(cap_el) or scene_dict.get("caption_rect"),
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        )

    def _render_derivation_build() -> SceneTimeline:
        prev_el = _get_el(elements, "headline")
        tl_el  = _get_el(elements, "timeline")
        cap_el = _get_el(elements, "caption")
        return _inject_background(derivation_step_scene(
            previous_line=_text(prev_el),
            new_line=_text(tl_el, "?"),
            annotation=_text(cap_el),
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), bg_asset)

    def _render_profile_quote() -> SceneTimeline:
        char_el  = _get_el(elements, "character_center")
        label_el = _get_el(elements, "lower_third")
        asset    = _asset(char_el)
        name     = _name_from_asset(asset) if asset else _name_from_asset(
            _text(char_el)
        )
        # Truncate quote so it doesn't overflow the caption zone
        raw_quote = _text(label_el)
        quote = raw_quote[:80] + "…" if len(raw_quote) > 80 else raw_quote
        return character_introduction_scene(
            character_asset=asset,
            character_name=name,
            year="",
            quote=quote,
            background=bg_asset or _background_for_character(asset),
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        )

    def _render_historical_profile() -> SceneTimeline:
        char_el = _get_el(elements, "character_center")
        meta_el = _get_el(elements, "lower_third")
        cap_el = _get_el(elements, "caption")
        year_text, location_text = _split_metadata(_text(meta_el))
        return historical_moment_scene(
            character_asset=_asset(char_el),
            setting_background=bg_asset or _background_for_character(_asset(char_el)),
            year_text=scene_dict.get("year_text") or year_text,
            location_text=scene_dict.get("location_text") or location_text,
            narration=_text(cap_el),
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        )

    def _render_dual_dialogue() -> SceneTimeline:
        left_el = _get_el(elements, "character_left")
        right_el = _get_el(elements, "character_right")
        name_els = _get_els(elements, "lower_third")
        speech_els = _get_els(elements, "caption")
        return _inject_background(two_character_debate_scene(
            char_left_asset=_asset(left_el),
            char_left_name=_text(name_els[0]) if len(name_els) > 0 else _name_from_asset(_asset(left_el)),
            char_left_says=_text(speech_els[0]) if len(speech_els) > 0 else "",
            char_right_asset=_asset(right_el),
            char_right_name=_text(name_els[1]) if len(name_els) > 1 else _name_from_asset(_asset(right_el)),
            char_right_says=_text(speech_els[1]) if len(speech_els) > 1 else "",
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), bg_asset)

    def _render_split_comparison() -> SceneTimeline:
        left_el  = _get_el(elements, "character_left")
        right_el = _get_el(elements, "character_right")
        left_txt  = _text(left_el,  "A")
        right_txt = _text(right_el, "B")
        left_title, left_caption = _split_title_and_caption(left_txt)
        right_title, right_caption = _split_title_and_caption(right_txt)
        left_motion_profile = _motion_profile_for_subject(left_title, left_caption, _asset(left_el))
        right_motion_profile = _motion_profile_for_subject(right_title, right_caption, _asset(right_el))
        inferred_bg = bg_asset or _background_for_subject(
            left_txt,
            right_txt,
            _asset(left_el),
            _asset(right_el),
        )
        return _inject_background(storybook_comparison_split_scene(
            left_title=left_title,
            left_caption=left_caption,
            right_title=right_title,
            right_caption=right_caption,
            left_asset=_asset(left_el) or _animation_scene_fallback_asset(left_txt),
            right_asset=_asset(right_el) or _animation_scene_fallback_asset(right_txt),
            bridge_text=scene_dict.get("bridge_text") or "",
            left_motion_profile=left_motion_profile,
            right_motion_profile=right_motion_profile,
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), inferred_bg)

    def _render_title_visual_caption() -> SceneTimeline:
        diag_el = _get_el(elements, "diagram")
        cap_el  = _get_el(elements, "caption")
        headline_text = _first_clause(_text(diag_el), limit=60)
        diagram_asset = _asset(diag_el)
        if not diagram_asset:
            diagram_asset = _animation_scene_fallback_asset(" ".join([_text(diag_el), _text(cap_el)]))
        motion_profile = _motion_profile_for_subject(headline_text, _text(cap_el), diagram_asset)
        inferred_bg = bg_asset or _background_for_subject(
            headline_text,
            _text(cap_el),
            diagram_asset,
        )
        return _inject_background(diagram_explanation_scene(
            diagram_asset=diagram_asset,
            headline=headline_text,
            caption=_text(cap_el),
            motion_profile=motion_profile,
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), inferred_bg)

    def _render_motion_annotated_visual() -> SceneTimeline:
        diag_el = _get_el(elements, "diagram")
        cap_el  = _get_el(elements, "caption")
        accent_el = _get_el(elements, "accent")
        headline_text = _first_clause(_text(diag_el), limit=60)
        diagram_text = _text(diag_el)
        caption_text = _text(cap_el)
        diagram_asset = _asset(diag_el) or _animation_scene_fallback_asset(diagram_text or caption_text)
        accent_asset = _asset(accent_el) or _animation_scene_accent_asset(" ".join([headline_text, caption_text]))
        motion_profile = _motion_profile_for_subject(headline_text, caption_text, diagram_asset)
        inferred_bg = bg_asset or _background_for_subject(
            headline_text,
            caption_text,
            diagram_asset,
            accent_asset,
        )
        return _inject_background(diagram_explanation_scene(
            diagram_asset=diagram_asset,
            headline=headline_text,
            caption=caption_text,
            accent_asset=accent_asset,
            motion_profile=motion_profile,
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), inferred_bg)

    def _render_object_focus_callout() -> SceneTimeline:
        title_el = _get_el(elements, "headline")
        object_el = _get_el(elements, "diagram")
        explanation_el = _get_el(elements, "caption")
        callout_el = _get_el(elements, "lower_third")
        accent_el = _get_el(elements, "accent")
        motion_profile = _motion_profile_for_subject(
            _text(title_el),
            _text(explanation_el),
            _text(callout_el),
            _asset(object_el),
        )
        inferred_bg = bg_asset or _background_for_subject(
            _text(title_el),
            _text(explanation_el),
            _text(callout_el),
            _asset(object_el),
        )
        return _inject_background(storybook_object_demo_scene(
            object_asset=_asset(object_el) or _animation_scene_fallback_asset(_text(object_el)),
            title_text=_text(title_el),
            explanation_text=_text(explanation_el),
            callout_text=_text(callout_el),
            accent_asset=_asset(accent_el),
            motion_profile=motion_profile,
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), inferred_bg)

    def _render_timeline_milestones() -> SceneTimeline:
        intro_el = _get_el(elements, "headline")
        stage_els = _get_els(elements, "timeline")
        stages = scene_dict.get("stages") or []
        if not stages:
            parsed_stages: list[tuple[str, str, Optional[str]]] = []
            for stage_el in stage_els:
                year_text, label_text = _split_stage_text(_text(stage_el))
                parsed_stages.append((year_text, label_text, _asset(stage_el) or None))
            stages = parsed_stages
        stage_context = " ".join(" ".join(filter(None, [stage[0], stage[1], stage[2] or ""])) for stage in stages)
        inferred_bg = bg_asset or _background_for_subject(_text(intro_el), stage_context)
        return _inject_background(storybook_timeline_sequence_scene(
            stages=stages,
            intro_text=_text(intro_el),
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), inferred_bg)

    def _render_hook_title_visual() -> SceneTimeline:
        hl_el   = _get_el(elements, "headline")
        body_el = _get_el(elements, "body_text")
        # Fallback also handles "caption" role (some templates produce this)
        cap_el  = _get_el(elements, "caption")
        subtitle = _text(body_el) or _text(cap_el)
        hero_el = _get_el(elements, "diagram")
        hero_asset = _asset(hero_el) or _animation_scene_fallback_asset(" ".join([_text(hl_el), subtitle]))
        return storybook_hook_title_card_scene(
            title_text=_text(hl_el, "..."),
            subtitle_text=subtitle,
            badge_text=scene_dict.get("badge_text") or "",
            hero_asset=hero_asset,
            background=bg_asset,
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        )

    def _render_equation_warning() -> SceneTimeline:
        eq_el = _get_el(elements, "equation_center")
        warn_el = _get_el(elements, "headline")
        limit_el = _get_el(elements, "caption")
        return limits_breakdown_scene(
            equation_text=_text(eq_el, scene_dict.get("equation_text", "?")),
            limit_text=_text(limit_el, scene_dict.get("limit_text", "")),
            warning_text=_text(warn_el, scene_dict.get("warning_text", "")),
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        )

    def _render_worked_example_stack() -> SceneTimeline:
        setup_el = _get_el(elements, "headline")
        eq_el = _get_el(elements, "equation_center")
        sub_el = _get_el(elements, "caption")
        result_el = _get_el(elements, "lower_third")
        return worked_example_scene(
            setup_text=_text(setup_el, scene_dict.get("setup_text", "")),
            equation_text=_text(eq_el, scene_dict.get("equation_text", "?")),
            numbers_substituted=_text(sub_el, scene_dict.get("numbers_substituted", "")),
            result_text=_text(result_el, scene_dict.get("result_text", "")),
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        )

    def _render_outro_takeaway() -> SceneTimeline:
        label_el = _get_el(elements, "headline")
        takeaway_el = _get_el(elements, "body_text")
        next_el = _get_el(elements, "caption")
        hero_el = _get_el(elements, "diagram")
        return _inject_background(storybook_outro_bridge_scene(
            takeaway_text=_text(takeaway_el, scene_dict.get("takeaway_text", "")),
            next_episode_text=_text(next_el, scene_dict.get("next_episode_text", "")),
            series_label=_text(label_el, scene_dict.get("series_label", "")),
            hero_asset=_asset(hero_el),
            layout_rects=layout_rects,
            duration=duration,
            aspect_ratio=aspect_ratio,
            background_color=bg_color,
            fps=fps,
        ), bg_asset)

    planners: dict[str, Callable[[], SceneTimeline]] = {
        "equation_focus": _render_equation_focus,
        "derivation_build": _render_derivation_build,
        "profile_quote": _render_profile_quote,
        "historical_profile": _render_historical_profile,
        "dual_dialogue": _render_dual_dialogue,
        "split_comparison": _render_split_comparison,
        "title_visual_caption": _render_title_visual_caption,
        "motion_annotated_visual": _render_motion_annotated_visual,
        "object_focus_callout": _render_object_focus_callout,
        "timeline_milestones": _render_timeline_milestones,
        "hook_title_visual": _render_hook_title_visual,
        "equation_warning": _render_equation_warning,
        "worked_example_stack": _render_worked_example_stack,
        "outro_takeaway": _render_outro_takeaway,
    }

    if archetype in planners:
        return planners[archetype]()

    template_dispatch: dict[str, Callable[[], SceneTimeline]] = {
        "equation_reveal": _render_equation_focus,
        "derivation_step": _render_derivation_build,
        "character_scene": _render_profile_quote,
        "historical_moment": _render_historical_profile,
        "two_character_debate": _render_dual_dialogue,
        "two_element_comparison": _render_split_comparison,
        "diagram_explanation": _render_title_visual_caption,
        "animation_scene": _render_motion_annotated_visual,
        "object_demo": _render_object_focus_callout,
        "timeline_sequence": _render_timeline_milestones,
        "narration_with_caption": _render_hook_title_visual,
        "limits_breakdown": _render_equation_warning,
        "worked_example": _render_worked_example_stack,
        "outro_bridge": _render_outro_takeaway,
    }
    return template_dispatch.get(template, _render_hook_title_visual)()


# ---------------------------------------------------------------------------
# FFmpeg concat helper
# ---------------------------------------------------------------------------

def concat_scene_videos(scene_mp4s: list[str], output_path: str) -> str:
    """
    Concatenate a list of scene MP4 files into a single output MP4 using
    FFmpeg's concat demuxer (lossless re-mux, no re-encode).

    Parameters
    ----------
    scene_mp4s : list[str]
        Ordered list of MP4 file paths.
    output_path : str
        Destination MP4 path.

    Returns
    -------
    str
        Absolute path to the output file.
    """
    if not scene_mp4s:
        raise ValueError("concat_scene_videos: scene_mp4s list is empty")

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Write a temporary concat list file
    list_fd, list_path = tempfile.mkstemp(suffix=".txt", prefix="concat_")
    try:
        with os.fdopen(list_fd, "w") as fh:
            for p in scene_mp4s:
                fh.write(f"file '{os.path.abspath(p)}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            str(out),
        ]
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg concat failed (rc={result.returncode}):\n"
                f"{result.stderr[-2000:]}"
            )
    finally:
        try:
            os.unlink(list_path)
        except OSError:
            pass

    return str(out.resolve())


# ---------------------------------------------------------------------------
# Single-episode renderer
# ---------------------------------------------------------------------------

def render_episode(
    script_path: str,
    output_mp4: str,
    aspect_ratio: str = "16:9",
    fps: int = 30,
    work_dir: Optional[str] = None,
    crf: int = 23,
    keep_work_dir: bool = False,
    verbose: bool = True,
    force_scene_indices: Optional[list[int]] = None,
) -> str:
    """
    Full pipeline: markdown script → rendered MP4.

    Steps
    -----
    1. Parse script and map to scene descriptors (via scene_mapper).
    2. For each scene descriptor build a SceneTimeline.
    3. Render all frames for each scene to a temp directory.
    4. Stitch each scene's frames into a per-scene MP4.
    5. Concatenate all per-scene MP4s into the final episode MP4.

    Parameters
    ----------
    script_path : str
        Absolute path to the *_youtube_long.md script file.
    output_mp4 : str
        Destination for the rendered episode MP4.
    aspect_ratio : str
        "16:9" (1920×1080) or "9:16" (1080×1920 Shorts).
    fps : int
        Frames per second.
    work_dir : str or None
        Scratch directory for intermediate frames and per-scene MP4s.
        Defaults to a fresh temporary directory that is cleaned up after
        rendering (unless keep_work_dir=True).
    crf : int
        H.264 CRF for per-scene encoding (lower = better quality).
    keep_work_dir : bool
        If True, preserve the work directory for debugging.
    verbose : bool
        Print progress messages.

    Returns
    -------
    str
        Absolute path to the output MP4.
    """
    script_path = str(Path(script_path).resolve())
    _log = print if verbose else (lambda *a, **k: None)

    # ------------------------------------------------------------------
    # Step 1: parse script → scenes.json in work_dir
    # ------------------------------------------------------------------
    managed_work = work_dir is None
    if managed_work:
        work_dir = tempfile.mkdtemp(prefix="ep_render_")

    work = Path(work_dir)
    scenes_json = work / "scenes.json"

    try:
        audio_path = _ensure_sibling_audio(script_path)
        vtt_path   = _resolve_sibling_vtt(script_path)
        _log(f"[render_episode] Parsing: {Path(script_path).name}")
        scenes = map_script_to_scenes(script_path, str(scenes_json))
        _log(f"[render_episode] {len(scenes)} scenes mapped")

        # Pre-flight: warn about any missing assets before spending time rendering
        preflight_warnings = _preflight_scenes(scenes, script_path)
        for w in preflight_warnings:
            log.warning("[preflight] %s", w)
        if preflight_warnings:
            _log(f"[render_episode] Pre-flight: {len(preflight_warnings)} missing asset(s) — see log")

        # ------------------------------------------------------------------
        # Step 2-4: render each scene → per-scene MP4
        # ------------------------------------------------------------------
        scenes_dir = _scenes_dir_for_script(script_path)
        scenes_dir.mkdir(parents=True, exist_ok=True)
        scene_manifest = _load_scene_manifest(scenes_dir)
        force_set = set(force_scene_indices or [])

        scene_mp4s: list[str] = []
        for idx, scene_dict in enumerate(scenes):
            scene_id = scene_dict.get("scene_id", f"scene_{idx:04d}")
            persistent_mp4 = scenes_dir / f"scene_{idx:04d}.mp4"
            scene_hash = _scene_dict_hash(scene_dict)
            frames_dir = str(work / f"frames_{idx:04d}")
            scene_mp4_tmp = str(work / f"scene_{idx:04d}.mp4")

            manifest_entry = scene_manifest.get(str(idx), {})
            can_skip = (
                idx not in force_set
                and persistent_mp4.is_file()
                and manifest_entry.get("hash") == scene_hash
            )

            if can_skip:
                _log(f"  [{idx+1}/{len(scenes)}] {scene_id} — cached ✓")
                scene_mp4s.append(str(persistent_mp4))
                continue

            _log(f"  [{idx+1}/{len(scenes)}] {scene_id}  "
                 f"template={scene_dict['template']}  "
                 f"dur={scene_dict['duration']:.1f}s")

            rendered_mp4: Optional[str] = None

            # Try Manim for equation/derivation scenes first
            if scene_dict.get("template") in ("equation_reveal", "derivation_step"):
                rendered_mp4 = _try_manim_equation(scene_dict, aspect_ratio, fps) or None

            # Fall back to PIL-based frame rendering
            if rendered_mp4 is None:
                try:
                    timeline = build_scene_timeline(scene_dict, aspect_ratio=aspect_ratio, fps=fps)
                    timeline.render_all(frames_dir, verbose=False)
                    frames_to_video(frames_dir, scene_mp4_tmp, fps=fps, crf=crf)
                    rendered_mp4 = scene_mp4_tmp
                except Exception as exc:
                    log.warning(
                        "Scene %s failed to render (%s): %s — inserting blank",
                        scene_id, type(exc).__name__, exc,
                    )
                    rendered_mp4 = _render_blank_scene(
                        scene_dict.get("duration", 3.0), work, idx, aspect_ratio, fps, crf
                    )

            # Persist the scene MP4
            shutil.copy2(rendered_mp4, persistent_mp4)
            scene_mp4s.append(str(persistent_mp4))
            import datetime as _dt
            scene_manifest[str(idx)] = {
                "scene_id": scene_id,
                "hash": scene_hash,
                "template": scene_dict.get("template"),
                "duration": scene_dict.get("duration"),
                "rendered_at": _dt.datetime.utcnow().isoformat(),
            }

        _save_scene_manifest(scenes_dir, scene_manifest)

        if not scene_mp4s:
            raise RuntimeError("No scenes rendered for: " + script_path)

        # ------------------------------------------------------------------
        # Step 5: concatenate → final episode MP4
        # ------------------------------------------------------------------
        _log(f"[render_episode] Concatenating {len(scene_mp4s)} scenes → {output_mp4}")
        concat_scene_videos(scene_mp4s, output_mp4)
        if audio_path:
            _log(f"[render_episode] Muxing audio{' + subtitles' if vtt_path else ''} → {Path(audio_path).name}")
            _mux_audio_into_video(output_mp4, audio_path, vtt_path=vtt_path)
        size_mb = os.path.getsize(output_mp4) / 1024 / 1024
        _log(f"[render_episode] Done: {output_mp4}  ({size_mb:.1f} MB)")

    finally:
        if managed_work and not keep_work_dir:
            shutil.rmtree(work_dir, ignore_errors=True)

    return str(Path(output_mp4).resolve())


def _render_blank_scene(
    duration: float,
    work: Path,
    idx: int,
    aspect_ratio: str,
    fps: int,
    crf: int,
) -> str:
    """Render a solid-color blank scene as a fallback for failed scenes."""
    from src.animation.scene_types import storybook_hook_title_card_scene
    blank = storybook_hook_title_card_scene(
        title_text="",
        subtitle_text="",
        duration=max(duration, 1.0),
        aspect_ratio=aspect_ratio,
        fps=fps,
    )
    frames_dir = str(work / f"blank_frames_{idx:04d}")
    out_mp4    = str(work / f"blank_{idx:04d}.mp4")
    blank.render_all(frames_dir, verbose=False)
    frames_to_video(frames_dir, out_mp4, fps=fps, crf=crf)
    return out_mp4


def render_scene(
    script_path: str,
    scene_index: int,
    output_mp4: Optional[str] = None,
    aspect_ratio: str = "16:9",
    fps: int = 30,
    crf: int = 23,
    verbose: bool = True,
) -> str:
    """
    Re-render a single scene by index and reassemble the full episode MP4.

    Use this to fix a single scene without waiting for a full episode re-render.
    The scene's persistent MP4 in media/scenes/ is overwritten, then all scenes
    are re-concatenated and re-muxed.

    Parameters
    ----------
    script_path : str
        Path to the episode markdown script.
    scene_index : int
        0-based index of the scene to re-render.
    output_mp4 : str or None
        Output path for the assembled episode MP4.  Defaults to
        ``media/<script_stem>.mp4`` beside the script.
    aspect_ratio, fps, crf, verbose
        Same as render_episode.

    Returns
    -------
    str
        Absolute path to the reassembled episode MP4.
    """
    script_path = str(Path(script_path).resolve())
    if output_mp4 is None:
        stem = Path(script_path).stem
        output_mp4 = str(_media_dir_for_script(script_path) / f"{stem}.mp4")

    return render_episode(
        script_path=script_path,
        output_mp4=output_mp4,
        aspect_ratio=aspect_ratio,
        fps=fps,
        crf=crf,
        verbose=verbose,
        force_scene_indices=[scene_index],
    )


# ---------------------------------------------------------------------------
# Batch renderer
# ---------------------------------------------------------------------------

def render_all_episodes(
    physics_dir: str,
    output_base: str,
    aspect_ratio: str = "16:9",
    fps: int = 30,
    crf: int = 23,
    verbose: bool = True,
    skip_existing: bool = True,
) -> list[dict]:
    """
    Walk the physics output tree and render every *_youtube_long.md script.

    Parameters
    ----------
    physics_dir : str
        Root of the physics output directory (e.g. output/physics/).
    output_base : str
        Root of the rendered video output directory.  Episode MP4s are written
        to a mirrored directory structure under this path.
    aspect_ratio : str
        "16:9" or "9:16".
    fps : int
        Frame rate.
    crf : int
        H.264 quality (18=lossless-ish, 23=default, 28=draft).
    verbose : bool
        Print progress for each episode.
    skip_existing : bool
        Skip episodes where the output MP4 already exists.

    Returns
    -------
    list[dict]
        One result record per episode:
        {"script": str, "output": str, "status": "ok"|"skipped"|"error",
         "error": str or None}
    """
    physics_root = Path(physics_dir).resolve()
    out_root     = Path(output_base).resolve()
    scripts      = sorted(physics_root.rglob("*_youtube_long.md"))

    results: list[dict] = []
    total = len(scripts)
    _log = print if verbose else (lambda *a, **k: None)
    _log(f"[render_all_episodes] Found {total} scripts under {physics_root}")

    for i, script_path in enumerate(scripts, 1):
        rel      = script_path.relative_to(physics_root)
        out_mp4  = out_root / rel.parent / (rel.stem + ".mp4")
        record: dict = {"script": str(script_path), "output": str(out_mp4),
                        "status": None, "error": None}

        if skip_existing and out_mp4.exists():
            _log(f"  [{i}/{total}] SKIP (exists): {rel}")
            record["status"] = "skipped"
            results.append(record)
            continue

        _log(f"\n  [{i}/{total}] Rendering: {rel}")
        try:
            render_episode(
                script_path=str(script_path),
                output_mp4=str(out_mp4),
                aspect_ratio=aspect_ratio,
                fps=fps,
                crf=crf,
                verbose=verbose,
            )
            record["status"] = "ok"
        except Exception as exc:
            log.error("Episode render failed: %s — %s", script_path.name, exc)
            record["status"] = "error"
            record["error"]  = str(exc)

        results.append(record)

    ok      = sum(1 for r in results if r["status"] == "ok")
    skipped = sum(1 for r in results if r["status"] == "skipped")
    errors  = sum(1 for r in results if r["status"] == "error")
    _log(f"\n[render_all_episodes] Complete: {ok} rendered, {skipped} skipped, {errors} errors")
    return results
