"""Sync visual reveals to narration word timestamps."""
import logging
import re
from pathlib import Path

logger = logging.getLogger(__name__)


def find_trigger_timestamp(
    trigger_word: str, transcript: list[dict], tolerance: float = 0.0
) -> float | None:
    """Find the start time of a trigger word in the transcript.

    Args:
        trigger_word: Word to search for (case-insensitive, strips punctuation)
        transcript: List of {word, start, end} dicts from Whisper
        tolerance: Not used currently, reserved for fuzzy matching

    Returns:
        Start time in seconds, or None if not found.
    """
    clean_trigger = re.sub(r"[^a-zA-Z0-9]", "", trigger_word.lower())

    for entry in transcript:
        clean_word = re.sub(r"[^a-zA-Z0-9]", "", entry.get("word", "").lower())
        if clean_word == clean_trigger:
            return entry["start"]

    # Fuzzy: check if trigger is a substring of any word
    for entry in transcript:
        clean_word = re.sub(r"[^a-zA-Z0-9]", "", entry.get("word", "").lower())
        if clean_trigger in clean_word or clean_word in clean_trigger:
            return entry["start"]

    return None


def plan_visual_reveals(
    scene: dict,
    transcript: list[dict],
    scene_start_time: float,
    scene_duration: float,
) -> list[dict]:
    """Plan visual element reveal timings based on narration.

    Args:
        scene: Scene dict with text_elements containing trigger_word
        transcript: Full episode transcript [{word, start, end}]
        scene_start_time: When this scene starts in the episode
        scene_duration: Duration of this scene in seconds

    Returns:
        List of {element, animation_type, start_time, duration} dicts
        where start_time is relative to scene start.
    """
    reveals = []
    scene_end = scene_start_time + scene_duration

    # Filter transcript to this scene's time window
    scene_words = [
        w for w in transcript
        if w["start"] >= scene_start_time and w["start"] < scene_end
    ]

    for elem in scene.get("text_elements", []):
        trigger = elem.get("trigger_word", "")
        anim_type = elem.get("animation", "fade_in")

        if trigger and scene_words:
            timestamp = find_trigger_timestamp(trigger, scene_words)
            if timestamp is not None:
                # Start animation 0.1s before word is spoken (anticipation)
                rel_start = max(0, timestamp - scene_start_time - 0.1)
                reveals.append({
                    "element": elem,
                    "animation_type": anim_type,
                    "start_time": rel_start,
                    "duration": 0.5,  # Default reveal duration
                })
                continue

        # Fallback: evenly space reveals across scene duration
        idx = scene.get("text_elements", []).index(elem)
        total = len(scene.get("text_elements", []))
        rel_start = (idx / max(total, 1)) * scene_duration * 0.8
        reveals.append({
            "element": elem,
            "animation_type": anim_type,
            "start_time": rel_start,
            "duration": 0.5,
        })

    return reveals


def apply_reveals_to_frames(
    frames: list,  # list of PIL.Image
    reveals: list[dict],
    fps: int = 30,
    canvas_size: tuple[int, int] = (1920, 1080),
) -> list:
    """Overlay text reveals onto existing parallax frames.

    Composites text elements with entrance animations on top of
    the parallax-rendered frames based on reveal timing.
    """
    from PIL import Image, ImageDraw, ImageFont

    result_frames = []

    for frame_idx, frame in enumerate(frames):
        canvas = frame.copy()
        t = frame_idx / fps  # Current time in seconds
        draw = ImageDraw.Draw(canvas)

        for reveal in reveals:
            elem = reveal["element"]
            start = reveal["start_time"]
            duration = reveal["duration"]
            anim_type = reveal["animation_type"]

            if t < start:
                continue  # Not yet visible

            progress = min(1.0, (t - start) / max(duration, 0.01))
            content = elem.get("content", "")
            x_norm = elem.get("x", 0.5)
            y_norm = elem.get("y", 0.5)
            font_ratio = elem.get("font_size_ratio", 0.04)

            x = int(x_norm * canvas_size[0])
            y = int(y_norm * canvas_size[1])
            font_size = max(16, int(font_ratio * canvas_size[1]))

            try:
                font = ImageFont.truetype("data/fonts/Nunito-Regular.ttf", font_size)
            except (OSError, IOError):
                font = ImageFont.load_default()

            # Apply animation
            alpha = int(255 * progress) if anim_type == "fade_in" else 255

            if anim_type == "slide_in":
                x = int(x - (1 - progress) * 200)
            elif anim_type == "pop_in":
                if progress < 1.0:
                    scale = 0.5 + 0.5 * progress
                    font_size = int(font_size * scale)
                    try:
                        font = ImageFont.truetype("data/fonts/Nunito-Regular.ttf", font_size)
                    except (OSError, IOError):
                        font = ImageFont.load_default()

            # Draw text with alpha
            txt_layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
            txt_draw = ImageDraw.Draw(txt_layer)
            txt_draw.text((x, y), content, fill=(255, 255, 255, alpha), font=font)
            canvas = Image.alpha_composite(canvas.convert("RGBA"), txt_layer).convert("RGB")

        result_frames.append(canvas)

    return result_frames
