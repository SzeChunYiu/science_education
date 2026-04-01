"""Detect scene boundaries in downloaded videos using PySceneDetect.

Uses the ContentDetector algorithm to identify cuts and transitions,
producing a scenes.json file per video with timestamp boundaries.
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def detect_scenes(
    video_path: Path,
    threshold: float = 27.0,
) -> list[dict]:
    """Detect scene boundaries in a single video.

    Args:
        video_path: Path to the video file (mp4).
        threshold: ContentDetector sensitivity threshold.
            Lower values detect more scenes. Default 27.0 is a good
            balance for educational content.

    Returns:
        List of dicts: [{scene_id, start_time, end_time, duration}, ...].
    """
    try:
        from scenedetect import open_video, SceneManager
        from scenedetect.detectors import ContentDetector
    except ImportError:
        logger.error(
            "scenedetect not installed. Install with: pip install scenedetect[opencv]"
        )
        return []

    if not video_path.exists():
        logger.error("Video file not found: %s", video_path)
        return []

    logger.info("Detecting scenes in %s (threshold=%.1f)", video_path.name, threshold)

    try:
        video = open_video(str(video_path))
        scene_manager = SceneManager()
        scene_manager.add_detector(ContentDetector(threshold=threshold))
        scene_manager.detect_scenes(video)
        scene_list = scene_manager.get_scene_list()
    except Exception:
        logger.exception("Scene detection failed for %s", video_path)
        return []

    scenes: list[dict] = []
    for i, (start, end) in enumerate(scene_list):
        start_sec = start.get_seconds()
        end_sec = end.get_seconds()
        scenes.append(
            {
                "scene_id": i,
                "start_time": round(start_sec, 3),
                "end_time": round(end_sec, 3),
                "duration": round(end_sec - start_sec, 3),
            }
        )

    logger.info("Detected %d scenes in %s", len(scenes), video_path.name)
    return scenes


def detect_all_scenes(
    data_dir: Path,
    threshold: float = 27.0,
) -> dict[str, int]:
    """Detect scenes in all downloaded videos.

    Expects data_dir to contain per-video subdirectories, each with a
    video.mp4 file. Saves scenes.json in each video directory. Skips
    videos that already have scenes.json.

    Args:
        data_dir: Base directory containing per-video subdirectories.
        threshold: ContentDetector sensitivity threshold.

    Returns:
        Dict mapping video_id to scene count.
    """
    results: dict[str, int] = {}

    if not data_dir.exists():
        logger.error("Data directory does not exist: %s", data_dir)
        return results

    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue

        video_file = vid_dir / "video.mp4"
        scenes_file = vid_dir / "scenes.json"

        if not video_file.exists():
            logger.debug("No video.mp4 in %s, skipping", vid_dir.name)
            continue

        # Idempotent: skip if already processed
        if scenes_file.exists():
            try:
                existing = json.loads(scenes_file.read_text())
                logger.info(
                    "Skipping %s: %d scenes already detected",
                    vid_dir.name,
                    len(existing),
                )
                results[vid_dir.name] = len(existing)
                continue
            except (json.JSONDecodeError, OSError):
                logger.warning("Corrupt scenes.json in %s, re-detecting", vid_dir.name)

        try:
            scenes = detect_scenes(video_file, threshold=threshold)
            if scenes:
                scenes_file.write_text(json.dumps(scenes, indent=2))
                logger.info(
                    "Saved %d scenes to %s", len(scenes), scenes_file
                )
            results[vid_dir.name] = len(scenes)
        except Exception:
            logger.exception("Error detecting scenes for %s", vid_dir.name)
            results[vid_dir.name] = 0

    logger.info(
        "Scene detection complete: %d videos, %d total scenes",
        len(results),
        sum(results.values()),
    )
    return results


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    detect_all_scenes(Path("data/style_reference/videos"))
