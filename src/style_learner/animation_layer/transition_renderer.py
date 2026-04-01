"""Render transitions between scene clips using FFmpeg.

Supports cut (direct concatenation), dissolve (crossfade), and wipe
transitions via FFmpeg's xfade filter.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

logger = logging.getLogger(__name__)

# Supported transition types mapped to FFmpeg xfade names
XFADE_TYPES = {
    "dissolve": "fade",
    "fade": "fade",
    "wipe": "wipeleft",
    "wipe_left": "wipeleft",
    "wipe_right": "wiperight",
    "wipe_up": "wipeup",
    "wipe_down": "wipedown",
    "slide_left": "slideleft",
    "slide_right": "slideright",
    "circle_open": "circleopen",
    "circle_close": "circleclose",
}


def _probe_duration(clip: Path) -> float:
    """Get clip duration in seconds using ffprobe."""
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(clip),
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=30
        )
        return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError) as e:
        logger.warning("Could not probe duration for %s: %s", clip, e)
        return 0.0


def render_transition(
    clip_a: Path,
    clip_b: Path,
    transition_type: str = "cut",
    duration: float = 0.5,
    output: Path | None = None,
) -> Path:
    """Render a transition between two video clips.

    Args:
        clip_a: Path to the first clip.
        clip_b: Path to the second clip.
        transition_type: One of "cut", "dissolve", "wipe", etc.
        duration: Transition duration in seconds (ignored for "cut").
        output: Output file path. Auto-generated if None.

    Returns:
        Path to the rendered output file.
    """
    clip_a = Path(clip_a)
    clip_b = Path(clip_b)

    if output is None:
        output = clip_a.parent / f"transition_{clip_a.stem}_{clip_b.stem}.mp4"
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if transition_type == "cut":
        return _concatenate_cut([clip_a, clip_b], output)

    # Use xfade filter
    dur_a = _probe_duration(clip_a)
    if dur_a <= 0:
        logger.warning("Cannot determine clip_a duration, falling back to cut")
        return _concatenate_cut([clip_a, clip_b], output)

    xfade_name = XFADE_TYPES.get(transition_type, "fade")
    offset = max(0, dur_a - duration)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(clip_a),
        "-i", str(clip_b),
        "-filter_complex",
        f"[0:v][1:v]xfade=transition={xfade_name}:duration={duration}:offset={offset}[v]",
        "-map", "[v]",
        "-c:v", "libx264", "-crf", "18", "-preset", "medium",
        "-pix_fmt", "yuv420p",
        str(output),
    ]

    logger.info("Rendering %s transition (%.1fs): %s -> %s",
                transition_type, duration, clip_a.name, clip_b.name)

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            logger.error("FFmpeg xfade failed: %s", result.stderr[-500:])
            logger.info("Falling back to cut concatenation")
            return _concatenate_cut([clip_a, clip_b], output)
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        logger.error("FFmpeg not available or timed out: %s", e)
        raise RuntimeError(f"FFmpeg transition rendering failed: {e}") from e

    return output


def _concatenate_cut(clips: list[Path], output: Path) -> Path:
    """Concatenate clips without any transition (hard cut).

    Uses FFmpeg concat demuxer for fast, lossless concatenation.
    """
    if len(clips) == 1:
        # Single clip — just copy
        import shutil
        shutil.copy2(clips[0], output)
        return output

    # Write concat list to temp file
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".txt", delete=False, prefix="concat_"
    ) as f:
        for clip in clips:
            f.write(f"file '{clip.resolve()}'\n")
        concat_list = Path(f.name)

    cmd = [
        "ffmpeg", "-y",
        "-f", "concat", "-safe", "0",
        "-i", str(concat_list),
        "-c", "copy",
        str(output),
    ]

    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, timeout=300
        )
        if result.returncode != 0:
            logger.error("FFmpeg concat failed: %s", result.stderr[-500:])
            raise RuntimeError("FFmpeg concatenation failed")
    except (subprocess.TimeoutExpired, FileNotFoundError) as e:
        raise RuntimeError(f"FFmpeg not available: {e}") from e
    finally:
        concat_list.unlink(missing_ok=True)

    return output


def concatenate_with_transitions(
    clips: list[Path],
    transitions: list[dict],
    output: Path,
) -> Path:
    """Chain all clips with their specified transitions.

    Args:
        clips: Ordered list of clip paths.
        transitions: List of transition dicts, one per gap between clips.
            Each dict has "type" (str) and optional "duration" (float).
            Length must be len(clips) - 1.
        output: Final output file path.

    Returns:
        Path to the final concatenated video.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    if not clips:
        raise ValueError("No clips provided")

    if len(clips) == 1:
        import shutil
        shutil.copy2(clips[0], output)
        return output

    # Validate transitions count
    if len(transitions) != len(clips) - 1:
        logger.warning(
            "Expected %d transitions, got %d. Padding with cuts.",
            len(clips) - 1, len(transitions),
        )
        while len(transitions) < len(clips) - 1:
            transitions.append({"type": "cut", "duration": 0.0})

    # Check if all transitions are cuts — use fast concat
    all_cuts = all(t.get("type", "cut") == "cut" for t in transitions)
    if all_cuts:
        logger.info("All transitions are cuts, using fast concat for %d clips", len(clips))
        return _concatenate_cut(clips, output)

    # Build complex filter chain for mixed transitions
    # Process pairs iteratively, writing intermediate files
    logger.info("Rendering %d clips with mixed transitions", len(clips))

    current = clips[0]
    temp_files = []

    for i, transition in enumerate(transitions):
        next_clip = clips[i + 1]
        t_type = transition.get("type", "cut")
        t_duration = transition.get("duration", 0.5)

        is_last = i == len(transitions) - 1
        if is_last:
            step_output = output
        else:
            step_output = output.parent / f"_intermediate_{i}.mp4"
            temp_files.append(step_output)

        current = render_transition(
            clip_a=current,
            clip_b=next_clip,
            transition_type=t_type,
            duration=t_duration,
            output=step_output,
        )

    # Clean up intermediate files
    for tmp in temp_files:
        tmp.unlink(missing_ok=True)

    return output
