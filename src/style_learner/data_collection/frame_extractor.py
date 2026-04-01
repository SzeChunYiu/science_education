"""Extract frames from downloaded videos using ffmpeg.

Extracts frames at a configurable FPS (default 2fps) from each video,
saving them as numbered JPEG files in a per-video frames/ subdirectory.
Idempotent: skips videos that already have extracted frames.
"""

import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)


def extract_frames(video_path: Path, output_dir: Path, fps: int = 2) -> int:
    """Extract frames from a single video file at the given FPS.

    Args:
        video_path: Path to the video file (mp4).
        output_dir: Directory to save extracted frame images.
        fps: Frames per second to extract.

    Returns:
        Number of frames extracted, or 0 on failure.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    output_pattern = str(output_dir / "frame_%06d.jpg")

    cmd = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vf",
        f"fps={fps}",
        "-q:v",
        "2",
        "-y",
        output_pattern,
    ]

    logger.debug("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600,
        )
        if result.returncode != 0:
            logger.warning(
                "ffmpeg failed for %s: %s",
                video_path,
                result.stderr.strip()[:300],
            )
            return 0
    except subprocess.TimeoutExpired:
        logger.warning("ffmpeg timed out for %s", video_path)
        return 0
    except FileNotFoundError:
        logger.error("ffmpeg not found. Install ffmpeg to extract frames.")
        return 0

    frame_count = len(list(output_dir.glob("frame_*.jpg")))
    logger.info("Extracted %d frames from %s", frame_count, video_path.name)
    return frame_count


def extract_all_frames(
    data_dir: Path,
    fps: int = 2,
) -> dict[str, int]:
    """Extract frames from all downloaded videos in data_dir.

    Expects data_dir to contain per-video subdirectories, each with a
    video.mp4 file. Creates a frames/ subdirectory in each. Skips
    videos that already have frames extracted.

    Args:
        data_dir: Base directory containing per-video subdirectories.
        fps: Frames per second to extract.

    Returns:
        Dict mapping video_id to frame count.
    """
    results: dict[str, int] = {}

    if not data_dir.exists():
        logger.error("Data directory does not exist: %s", data_dir)
        return results

    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue

        video_file = vid_dir / "video.mp4"
        if not video_file.exists():
            logger.debug("No video.mp4 in %s, skipping", vid_dir.name)
            continue

        frames_dir = vid_dir / "frames"

        # Skip if frames already extracted
        if frames_dir.exists() and any(frames_dir.glob("frame_*.jpg")):
            existing = len(list(frames_dir.glob("frame_*.jpg")))
            logger.info(
                "Skipping %s: %d frames already extracted",
                vid_dir.name,
                existing,
            )
            results[vid_dir.name] = existing
            continue

        count = extract_frames(video_file, frames_dir, fps=fps)
        results[vid_dir.name] = count

    logger.info(
        "Frame extraction complete: %d videos, %d total frames",
        len(results),
        sum(results.values()),
    )
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    extract_all_frames(Path("data/style_reference/videos"))
