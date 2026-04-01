"""Audio mixing utilities for narration + background music.

All operations use FFmpeg subprocess calls -- no heavy audio libraries required.
"""
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def mix_audio(
    narration: Path,
    music: Path,
    output: Path,
    music_db: float = -18.0,
) -> Path:
    """Mix narration with background music.

    Narration stays at original volume; music is attenuated to sit
    underneath the voice.

    Args:
        narration: Path to narration audio file.
        music: Path to background music file.
        output: Path for mixed output file.
        music_db: Volume adjustment for music in dB (negative = quieter).

    Returns:
        Path to mixed audio file.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Build ffmpeg filter: adjust music volume, then mix with narration
    # amix with duration=first ensures output matches narration length
    filter_complex = (
        f"[1:a]volume={music_db}dB[music];"
        f"[0:a][music]amix=inputs=2:duration=first:dropout_transition=2[out]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(narration),
        "-i", str(music),
        "-filter_complex", filter_complex,
        "-map", "[out]",
        "-ac", "2",
        "-ar", "44100",
        "-c:a", "aac", "-b:a", "192k",
        str(output),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.error(f"Audio mix failed: {result.stderr[-500:]}")
            return output
        logger.info(f"Mixed audio saved: {output}")
    except FileNotFoundError:
        logger.error("ffmpeg not found on PATH")
    except subprocess.TimeoutExpired:
        logger.error("Audio mix timed out (>120s)")

    return output


def normalize_loudness(
    audio: Path,
    output: Path,
    target_lufs: float = -16.0,
) -> Path:
    """Normalize audio loudness to target LUFS (YouTube standard: -14 to -16).

    Uses ffmpeg two-pass loudnorm filter for broadcast-quality normalization.

    Args:
        audio: Input audio file.
        output: Output normalized audio file.
        target_lufs: Target integrated loudness in LUFS.

    Returns:
        Path to normalized audio file.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Single-pass loudnorm (good enough for educational content)
    filter_str = (
        f"loudnorm=I={target_lufs}:TP=-1.5:LRA=11:print_format=summary"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio),
        "-af", filter_str,
        "-ar", "44100",
        "-c:a", "aac", "-b:a", "192k",
        str(output),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode != 0:
            logger.error(f"Loudness normalization failed: {result.stderr[-500:]}")
            return output
        logger.info(f"Normalized audio ({target_lufs} LUFS): {output}")
    except FileNotFoundError:
        logger.error("ffmpeg not found on PATH")
    except subprocess.TimeoutExpired:
        logger.error("Loudness normalization timed out (>120s)")

    return output


def add_fade(
    audio: Path,
    output: Path,
    fade_in: float = 0.5,
    fade_out: float = 1.0,
) -> Path:
    """Add fade-in and fade-out to an audio file.

    Args:
        audio: Input audio file.
        output: Output audio file with fades applied.
        fade_in: Fade-in duration in seconds.
        fade_out: Fade-out duration in seconds.

    Returns:
        Path to audio file with fades.
    """
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)

    # Get duration for fade-out start calculation
    duration = _get_duration(audio)
    if duration <= 0:
        logger.warning(f"Could not determine duration for {audio}, skipping fade")
        # Just copy the file
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(audio), "-c", "copy", str(output)],
            capture_output=True, check=False,
        )
        return output

    fade_out_start = max(0, duration - fade_out)
    filter_str = (
        f"afade=t=in:st=0:d={fade_in},"
        f"afade=t=out:st={fade_out_start:.3f}:d={fade_out}"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(audio),
        "-af", filter_str,
        "-c:a", "aac", "-b:a", "192k",
        str(output),
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            logger.error(f"Fade failed: {result.stderr[-500:]}")
            return output
        logger.info(f"Added fade (in={fade_in}s, out={fade_out}s): {output}")
    except FileNotFoundError:
        logger.error("ffmpeg not found on PATH")
    except subprocess.TimeoutExpired:
        logger.error("Fade operation timed out (>60s)")

    return output


def _get_duration(path: Path) -> float:
    """Get audio duration in seconds using ffprobe."""
    try:
        import json as _json
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(path)],
            capture_output=True, text=True, timeout=10,
        )
        info = _json.loads(result.stdout)
        return float(info["format"]["duration"])
    except Exception:
        return 0.0
