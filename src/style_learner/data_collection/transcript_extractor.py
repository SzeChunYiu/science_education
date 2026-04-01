"""Extract transcripts with word-level timestamps from downloaded videos.

Prefers auto-generated VTT subtitles downloaded alongside the video.
Falls back to OpenAI Whisper (large-v2) for word-level transcription
when VTT files are missing or unparseable.
"""

import json
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def parse_vtt_to_words(vtt_path: Path) -> list[dict]:
    """Parse a WebVTT subtitle file into word-level timestamps.

    VTT cues typically contain phrases with start/end times. This parser
    splits cues into individual words and distributes timing evenly
    across words within each cue.

    Args:
        vtt_path: Path to the .vtt subtitle file.

    Returns:
        List of dicts: [{word, start, end}, ...].
    """
    if not vtt_path.exists():
        logger.debug("VTT file not found: %s", vtt_path)
        return []

    content = vtt_path.read_text(encoding="utf-8", errors="replace")

    # Match VTT timestamp lines: 00:00:01.000 --> 00:00:04.000
    timestamp_pattern = re.compile(
        r"(\d{2}:\d{2}:\d{2}\.\d{3})\s+-->\s+(\d{2}:\d{2}:\d{2}\.\d{3})"
    )

    words: list[dict] = []
    lines = content.splitlines()
    i = 0

    while i < len(lines):
        match = timestamp_pattern.search(lines[i])
        if match:
            start_str, end_str = match.group(1), match.group(2)
            start = _vtt_time_to_seconds(start_str)
            end = _vtt_time_to_seconds(end_str)

            # Collect text lines until blank line or next timestamp
            text_lines: list[str] = []
            i += 1
            while i < len(lines) and lines[i].strip() and not timestamp_pattern.search(lines[i]):
                # Strip VTT formatting tags
                clean = re.sub(r"<[^>]+>", "", lines[i]).strip()
                if clean:
                    text_lines.append(clean)
                i += 1

            text = " ".join(text_lines)
            cue_words = text.split()
            if not cue_words:
                continue

            # Distribute timing evenly across words
            duration = end - start
            word_duration = duration / len(cue_words)
            for j, w in enumerate(cue_words):
                words.append(
                    {
                        "word": w,
                        "start": round(start + j * word_duration, 3),
                        "end": round(start + (j + 1) * word_duration, 3),
                    }
                )
        else:
            i += 1

    logger.info("Parsed %d words from %s", len(words), vtt_path.name)
    return words


def _vtt_time_to_seconds(time_str: str) -> float:
    """Convert VTT timestamp (HH:MM:SS.mmm) to seconds."""
    parts = time_str.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])
    return hours * 3600 + minutes * 60 + seconds


def extract_transcript_whisper(audio_path: Path) -> list[dict]:
    """Extract word-level transcript using OpenAI Whisper large-v2.

    Whisper is imported lazily to avoid loading the model unless needed.

    Args:
        audio_path: Path to audio file (mp3 or wav).

    Returns:
        List of dicts: [{word, start, end}, ...].
    """
    if not audio_path.exists():
        logger.error("Audio file not found: %s", audio_path)
        return []

    try:
        import whisper  # noqa: delayed import
    except ImportError:
        logger.error(
            "openai-whisper not installed. Install with: pip install openai-whisper"
        )
        return []

    logger.info("Running Whisper large-v2 on %s", audio_path.name)
    model = whisper.load_model("large-v2")
    result = model.transcribe(
        str(audio_path),
        word_timestamps=True,
        language="en",
    )

    words: list[dict] = []
    for segment in result.get("segments", []):
        for w in segment.get("words", []):
            words.append(
                {
                    "word": w.get("word", "").strip(),
                    "start": round(w.get("start", 0.0), 3),
                    "end": round(w.get("end", 0.0), 3),
                }
            )

    logger.info("Whisper extracted %d words from %s", len(words), audio_path.name)
    return words


def extract_transcript(vid_dir: Path) -> list[dict]:
    """Extract transcript for a video, trying VTT first then Whisper.

    Saves the result as transcript.json in the video directory. If
    transcript.json already exists, loads and returns it.

    Args:
        vid_dir: Per-video directory containing subs.en.vtt and/or audio.mp3.

    Returns:
        List of dicts: [{word, start, end}, ...].
    """
    transcript_path = vid_dir / "transcript.json"

    # Idempotent: skip if already extracted
    if transcript_path.exists():
        logger.info("Transcript already exists: %s", transcript_path)
        try:
            return json.loads(transcript_path.read_text())
        except (json.JSONDecodeError, OSError):
            logger.warning("Corrupt transcript.json, re-extracting")

    # Try VTT first
    vtt_candidates = list(vid_dir.glob("subs*.vtt")) + list(vid_dir.glob("*.en.vtt"))
    words: list[dict] = []

    for vtt_path in vtt_candidates:
        words = parse_vtt_to_words(vtt_path)
        if words:
            break

    # Fall back to Whisper
    if not words:
        audio_path = vid_dir / "audio.mp3"
        if audio_path.exists():
            logger.info("No VTT subs found, falling back to Whisper for %s", vid_dir.name)
            words = extract_transcript_whisper(audio_path)
        else:
            logger.warning("No subs or audio found in %s", vid_dir.name)

    # Save transcript
    if words:
        transcript_path.write_text(json.dumps(words, indent=2))
        logger.info(
            "Saved %d words to %s", len(words), transcript_path
        )

    return words


def extract_all_transcripts(data_dir: Path) -> dict[str, int]:
    """Extract transcripts from all downloaded videos.

    Args:
        data_dir: Base directory containing per-video subdirectories.

    Returns:
        Dict mapping video_id to word count.
    """
    results: dict[str, int] = {}

    if not data_dir.exists():
        logger.error("Data directory does not exist: %s", data_dir)
        return results

    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue

        try:
            words = extract_transcript(vid_dir)
            results[vid_dir.name] = len(words)
        except Exception:
            logger.exception("Error extracting transcript for %s", vid_dir.name)
            results[vid_dir.name] = 0

    logger.info(
        "Transcript extraction complete: %d videos, %d total words",
        len(results),
        sum(results.values()),
    )
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    extract_all_transcripts(Path("data/style_reference/videos"))
