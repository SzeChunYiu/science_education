"""Generate WebVTT and SRT subtitles from word timestamps.

Timestamps come from the narration pipeline (F5Narrator.render_episode)
as a list of {"word": str, "start": float, "end": float} dicts.
"""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def generate_vtt(
    timestamps: list[dict],
    output_path: Path,
    words_per_line: int = 8,
) -> Path:
    """Generate a WebVTT subtitle file from word timestamps.

    Groups words into subtitle lines of up to ``words_per_line`` words,
    using the start time of the first word and end time of the last word
    in each group.

    Args:
        timestamps: List of word timestamp dicts with keys
                    "word", "start", "end".
        output_path: Where to write the .vtt file.
        words_per_line: Maximum words per subtitle line.

    Returns:
        Path to the generated .vtt file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    lines = ["WEBVTT", ""]

    # Group words into subtitle cues
    for i in range(0, len(timestamps), words_per_line):
        group = timestamps[i : i + words_per_line]
        if not group:
            continue

        start = group[0]["start"]
        end = group[-1]["end"]
        text = " ".join(w["word"] for w in group)

        lines.append(f"{_format_vtt_time(start)} --> {_format_vtt_time(end)}")
        lines.append(text)
        lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info(f"Generated VTT subtitles: {output_path}")
    return output_path


def vtt_to_srt(vtt_path: Path, output_path: Path) -> Path:
    """Convert a WebVTT file to SRT format for ffmpeg subtitle burn-in.

    Args:
        vtt_path: Path to input .vtt file.
        output_path: Path for output .srt file.

    Returns:
        Path to the generated .srt file.
    """
    vtt_path = Path(vtt_path)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    content = vtt_path.read_text(encoding="utf-8")
    lines = content.strip().split("\n")

    srt_lines = []
    cue_index = 0
    i = 0

    # Skip header
    while i < len(lines) and not _is_timestamp_line(lines[i]):
        i += 1

    while i < len(lines):
        line = lines[i].strip()

        if _is_timestamp_line(line):
            cue_index += 1
            # Convert VTT timestamp format (.) to SRT format (,)
            srt_timestamp = line.replace(".", ",")
            srt_lines.append(str(cue_index))
            srt_lines.append(srt_timestamp)
            # Collect text lines until blank
            i += 1
            while i < len(lines) and lines[i].strip():
                srt_lines.append(lines[i].strip())
                i += 1
            srt_lines.append("")
        else:
            i += 1

    output_path.write_text("\n".join(srt_lines), encoding="utf-8")
    logger.info(f"Converted VTT to SRT: {output_path}")
    return output_path


def _format_vtt_time(seconds: float) -> str:
    """Format seconds as VTT timestamp HH:MM:SS.mmm."""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"


def _is_timestamp_line(line: str) -> bool:
    """Check if a line contains a VTT/SRT timestamp arrow."""
    return "-->" in line
