"""Prepare LoRA training datasets from extracted TED-Ed reference frames."""
import json
import shutil
import logging
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/style_reference")
LORA_DIR = Path("data/lora_training")


def prepare_style_dataset(
    data_dir: Path = DATA_DIR,
    output_dir: Path = LORA_DIR / "teded_style",
    max_images: int = 200,
    min_aesthetic_score: float = 5.0,
) -> int:
    """Select top-quality TED-Ed keyframes for style LoRA training.

    Selects frames ranked by aesthetic score, copies them to output_dir
    with auto-generated caption .txt files in kohya_ss format.
    Returns number of images prepared.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    # Collect all frames with quality scores
    scored_frames = []
    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue
        features_path = vid_dir / "features.json"
        if not features_path.exists():
            continue
        features = json.loads(features_path.read_text())
        frames_dir = vid_dir / "frames"
        for frame_info in features.get("frames", []):
            aesthetic = frame_info.get("aesthetic_score", 0)
            if aesthetic >= min_aesthetic_score:
                frame_path = frames_dir / frame_info["filename"]
                if frame_path.exists():
                    scored_frames.append((aesthetic, frame_path, frame_info))

    # Sort by aesthetic score descending, take top N
    scored_frames.sort(key=lambda x: x[0], reverse=True)
    selected = scored_frames[:max_images]

    count = 0
    for i, (score, frame_path, info) in enumerate(selected):
        # Copy image
        dest = output_dir / f"frame_{i:04d}.png"
        img = Image.open(frame_path).convert("RGB").resize((1024, 1024), Image.LANCZOS)
        img.save(dest, quality=95)

        # Generate caption
        scene_type = info.get("scene_type", "educational illustration")
        caption = (
            f"teded_style, educational animated illustration, {scene_type}, "
            f"flat color style, bold outlines, clean composition, "
            f"warm palette, children's educational animation"
        )
        dest.with_suffix(".txt").write_text(caption)
        count += 1

    logger.info(f"Prepared {count} images for style LoRA training in {output_dir}")
    return count


def prepare_character_dataset(
    character_name: str,
    reference_images: list[Path],
    output_dir: Path = None,
) -> int:
    """Prepare dataset for a character-specific LoRA.

    Takes manually curated reference images of a character.
    """
    if output_dir is None:
        output_dir = LORA_DIR / f"character_{character_name}"
    output_dir.mkdir(parents=True, exist_ok=True)

    count = 0
    for i, img_path in enumerate(reference_images):
        dest = output_dir / f"{character_name}_{i:04d}.png"
        img = Image.open(img_path).convert("RGB").resize((1024, 1024), Image.LANCZOS)
        img.save(dest, quality=95)

        caption = (
            f"teded_style, character {character_name}, "
            f"educational animated character, chibi style, "
            f"flat colors, bold outlines, consistent design"
        )
        dest.with_suffix(".txt").write_text(caption)
        count += 1

    logger.info(f"Prepared {count} images for {character_name} LoRA in {output_dir}")
    return count
