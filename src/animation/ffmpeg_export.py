"""
FFmpeg export utilities for physics education video production.

Converts a directory of numbered PNG frames into an MP4 video file using
FFmpeg's H.264 encoder with YouTube-compatible settings.

All functions are zero-cost — they shell out to the system FFmpeg binary and
do not require any third-party Python packages beyond the standard library.

Requirements
------------
- ffmpeg ≥ 4.0 on PATH (free, open-source)
- ffprobe on PATH (ships with ffmpeg distributions)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
from typing import Optional


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def check_ffmpeg() -> bool:
    """
    Return True if ffmpeg is installed and accessible on PATH, False otherwise.

    This is a safe check — it never raises.
    """
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"],
            capture_output=True,
            timeout=10,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired, OSError):
        return False


def frames_to_video(
    frames_dir: str,
    output_path: str,
    fps: int = 30,
    audio_path: Optional[str] = None,
    crf: int = 18,
    preset: str = "medium",
) -> str:
    """
    Stitch a directory of numbered PNG frames into an MP4 video file.

    The frames must be named with a consistent zero-padded numeric prefix,
    e.g. ``frame_000.png``, ``frame_001.png``, …  The pattern is
    auto-detected from the actual files in ``frames_dir``.

    Parameters
    ----------
    frames_dir : str
        Directory containing the numbered PNG frames.
    output_path : str
        Destination MP4 file path.  Parent directories are created as needed.
    fps : int
        Frame rate of the output video (default 30).
    audio_path : str or None
        Optional path to an audio file (WAV, MP3, AAC, etc.) to mux into the
        video.  The audio is trimmed or padded to match the video duration.
        If None, the video is mute.
    crf : int
        H.264 Constant Rate Factor.  Lower = higher quality / larger file.
        18 is visually lossless; 23 is FFmpeg default; 28 is acceptable for
        previews.
    preset : str
        H.264 encoder speed/compression trade-off.  One of:
        ultrafast, superfast, veryfast, faster, fast, medium, slow, slower,
        veryslow.  Slower presets produce smaller files at the same CRF.

    Returns
    -------
    str
        The absolute path to the created MP4 file.

    Raises
    ------
    RuntimeError
        If ffmpeg is not found, or if ffmpeg exits with a non-zero return code.
    FileNotFoundError
        If ``frames_dir`` does not exist or contains no PNG files.
    """
    if not check_ffmpeg():
        raise RuntimeError(
            "ffmpeg not found on PATH.  "
            "Install it with: brew install ffmpeg  (macOS)"
        )

    frames_dir = os.path.abspath(frames_dir)
    if not os.path.isdir(frames_dir):
        raise FileNotFoundError(f"frames_dir does not exist: {frames_dir!r}")

    # Auto-detect frame naming pattern
    pattern = _detect_frame_pattern(frames_dir)
    if pattern is None:
        raise FileNotFoundError(
            f"No numbered PNG frames found in {frames_dir!r}"
        )

    # Ensure output directory exists
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    cmd = _build_ffmpeg_command(
        frames_dir=frames_dir,
        pattern=pattern,
        output_path=output_path,
        fps=fps,
        audio_path=audio_path,
        crf=crf,
        preset=preset,
    )

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed (exit code {result.returncode}).\n"
            f"Command: {' '.join(cmd)}\n"
            f"stderr:\n{result.stderr[-3000:]}"  # last 3 KB of stderr
        )

    return output_path


def get_video_info(video_path: str) -> dict:
    """
    Return metadata about a video file using ffprobe.

    Parameters
    ----------
    video_path : str
        Path to the video file.

    Returns
    -------
    dict
        Keys: ``duration`` (float, seconds), ``fps`` (float),
        ``width`` (int), ``height`` (int), ``codec`` (str),
        ``audio_codec`` (str or None), ``file_size_bytes`` (int).

    Raises
    ------
    RuntimeError
        If ffprobe is not found or exits with a non-zero return code.
    FileNotFoundError
        If ``video_path`` does not exist.
    """
    video_path = os.path.abspath(video_path)
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path!r}")

    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_streams",
        "-show_format",
        video_path,
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "ffprobe not found on PATH.  "
            "It ships with ffmpeg — install ffmpeg to get ffprobe."
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"ffprobe failed (exit code {result.returncode}).\n"
            f"stderr: {result.stderr}"
        )

    data = json.loads(result.stdout)

    info: dict = {
        "duration": None,
        "fps": None,
        "width": None,
        "height": None,
        "codec": None,
        "audio_codec": None,
        "file_size_bytes": int(os.path.getsize(video_path)),
    }

    # Format-level duration
    fmt = data.get("format", {})
    if "duration" in fmt:
        info["duration"] = float(fmt["duration"])

    # Stream-level details
    for stream in data.get("streams", []):
        codec_type = stream.get("codec_type")
        if codec_type == "video" and info["codec"] is None:
            info["codec"] = stream.get("codec_name")
            info["width"] = stream.get("width")
            info["height"] = stream.get("height")
            # fps is stored as a rational string like "30/1" or "30000/1001"
            r_frame_rate = stream.get("r_frame_rate", "")
            info["fps"] = _parse_rational(r_frame_rate)
            if info["duration"] is None:
                raw = stream.get("duration")
                if raw:
                    info["duration"] = float(raw)
        elif codec_type == "audio" and info["audio_codec"] is None:
            info["audio_codec"] = stream.get("codec_name")

    return info


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_frame_pattern(frames_dir: str) -> Optional[str]:
    """
    Scan ``frames_dir`` for PNG files named with a consistent numeric suffix
    and return an ffmpeg input glob pattern such as ``frame_%03d.png``.

    Returns None if no suitable files are found.
    """
    png_files = sorted(
        f for f in os.listdir(frames_dir)
        if f.lower().endswith(".png")
    )
    if not png_files:
        return None

    # Try to match a pattern like  frame_000.png, frame_0000.png, etc.
    # We look at the first file to infer prefix and zero-padding width.
    first = png_files[0]
    match = re.match(r"^(.*?)(\d+)(\.png)$", first, re.IGNORECASE)
    if not match:
        return None

    prefix = match.group(1)
    num_part = match.group(2)
    suffix = match.group(3)
    width = len(num_part)

    # Verify at least one more file matches
    if len(png_files) > 1:
        second = png_files[1]
        expected_pattern = re.compile(
            rf"^{re.escape(prefix)}\d{{{width}}}{re.escape(suffix)}$",
            re.IGNORECASE,
        )
        if not expected_pattern.match(second):
            # Fall back to globbing all PNGs alphabetically
            return None

    return f"{prefix}%0{width}d{suffix}"


def _build_ffmpeg_command(
    frames_dir: str,
    pattern: str,
    output_path: str,
    fps: int,
    audio_path: Optional[str],
    crf: int,
    preset: str,
) -> list[str]:
    """Build the ffmpeg command list."""
    input_pattern = os.path.join(frames_dir, pattern)

    cmd = [
        "ffmpeg",
        "-y",                          # overwrite output without asking
        "-framerate", str(fps),
        "-i", input_pattern,
    ]

    if audio_path:
        audio_path = os.path.abspath(audio_path)
        cmd += ["-i", audio_path]

    cmd += [
        "-c:v", "libx264",
        "-crf", str(crf),
        "-preset", preset,
        "-pix_fmt", "yuv420p",         # required for YouTube / broad compatibility
        "-movflags", "+faststart",     # move moov atom to front for streaming
    ]

    if audio_path:
        cmd += [
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",               # trim to shortest stream (video or audio)
        ]

    cmd.append(output_path)
    return cmd


def _parse_rational(rational_str: str) -> Optional[float]:
    """Parse a rational string like '30/1' or '30000/1001' to a float."""
    if not rational_str:
        return None
    parts = rational_str.split("/")
    if len(parts) == 2:
        num, den = parts
        try:
            return float(num) / float(den)
        except (ValueError, ZeroDivisionError):
            return None
    try:
        return float(rational_str)
    except ValueError:
        return None
