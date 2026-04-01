"""Master orchestrator for feature extraction pipeline.

Runs all feature extractors in sequence on all videos in the data directory.
Produces per-video feature files and a final unified dataset.jsonl.

Usage:
    python -m src.style_learner.feature_extraction.extract_all [OPTIONS]

Options:
    --data-dir PATH     Root data directory (default: data/style_reference/videos)
    --device DEVICE     Torch device: cuda, mps, cpu (default: cuda)
    --test-mode         Process only the first 2 videos for quick testing
    --skip-clip         Skip CLIP feature extraction
    --skip-motion       Skip camera motion classification
    --skip-text         Skip text layout extraction
    --skip-quality      Skip quality score computation
    --skip-narration    Skip narration alignment
    --skip-dataset      Skip dataset assembly
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def _select_device(requested: str = "cuda") -> str:
    """Select best available device: CUDA > MPS > CPU."""
    import torch

    if requested == "cuda" and torch.cuda.is_available():
        return "cuda"
    if requested == "mps" or (
        requested == "cuda"
        and hasattr(torch.backends, "mps")
        and torch.backends.mps.is_available()
    ):
        return "mps"
    return "cpu"


def _find_video_dirs(data_dir: Path) -> list[Path]:
    """Find all video directories that have a frames/ subdirectory."""
    video_dirs = sorted(
        d for d in data_dir.iterdir()
        if d.is_dir() and (d / "frames").exists()
    )
    return video_dirs


def run_clip_extraction(video_dirs: list[Path], device: str) -> None:
    """Run CLIP feature extraction on all videos."""
    from src.style_learner.feature_extraction.clip_features import CLIPFeatureExtractor

    logger.info("=== CLIP Feature Extraction ===")
    extractor = CLIPFeatureExtractor(device=device)
    for i, video_dir in enumerate(video_dirs):
        logger.info("[%d/%d] Processing %s", i + 1, len(video_dirs), video_dir.name)
        try:
            extractor.extract_for_video(video_dir)
        except Exception as e:
            logger.error("Failed CLIP extraction for %s: %s", video_dir.name, e)


def run_camera_motion(video_dirs: list[Path]) -> None:
    """Run camera motion classification on all videos."""
    from src.style_learner.feature_extraction.camera_motion import classify_scene_motion

    logger.info("=== Camera Motion Classification ===")
    for i, video_dir in enumerate(video_dirs):
        logger.info("[%d/%d] Processing %s", i + 1, len(video_dirs), video_dir.name)
        frames_dir = video_dir / "frames"
        scenes_path = video_dir / "scenes.json"

        if not scenes_path.exists():
            logger.warning("No scenes.json for %s, skipping motion", video_dir.name)
            continue

        try:
            with open(scenes_path) as f:
                scenes = json.load(f)

            motion_results = []
            for scene in scenes:
                result = classify_scene_motion(frames_dir, scene)
                result["scene_id"] = scene.get("scene_id", scenes.index(scene))
                motion_results.append(result)

            output_path = video_dir / "camera_motion.json"
            with open(output_path, "w") as f:
                json.dump(motion_results, f, indent=2)
            logger.info("Saved camera motion for %d scenes", len(motion_results))
        except Exception as e:
            logger.error("Failed camera motion for %s: %s", video_dir.name, e)


def run_text_layout(video_dirs: list[Path]) -> None:
    """Run text layout extraction on all videos."""
    from src.style_learner.feature_extraction.text_layout import TextLayoutExtractor

    logger.info("=== Text Layout Extraction ===")
    extractor = TextLayoutExtractor()

    for i, video_dir in enumerate(video_dirs):
        logger.info("[%d/%d] Processing %s", i + 1, len(video_dirs), video_dir.name)
        frames_dir = video_dir / "frames"
        scenes_path = video_dir / "scenes.json"

        frame_paths = sorted(
            p for p in frames_dir.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )

        if not frame_paths:
            logger.warning("No frames for %s", video_dir.name)
            continue

        try:
            # Extract text for each frame
            all_regions = []
            for path in frame_paths:
                regions = extractor.extract_text_regions(path)
                all_regions.append({
                    "frame": path.name,
                    "regions": regions,
                })

            # Track text entrances across scenes if scenes exist
            text_results = all_regions
            if scenes_path.exists():
                with open(scenes_path) as f:
                    scenes = json.load(f)

                scene_text = []
                for scene_idx, scene in enumerate(scenes):
                    start = scene.get("start_frame", 0)
                    end = scene.get("end_frame", len(frame_paths) - 1)
                    scene_frames = frame_paths[start : end + 1]

                    entrances = extractor.track_text_entrance(scene_frames) if len(scene_frames) > 1 else []

                    # Collect all regions for this scene
                    scene_regions = []
                    for fr in all_regions[start : end + 1]:
                        scene_regions.extend(fr.get("regions", []))

                    scene_text.append({
                        "scene_id": scene.get("scene_id", scene_idx),
                        "regions": scene_regions,
                        "entrances": entrances,
                    })

                text_results = scene_text

            output_path = video_dir / "text_layout.json"
            with open(output_path, "w") as f:
                json.dump(text_results, f, indent=2)
            logger.info("Saved text layout for %s", video_dir.name)
        except Exception as e:
            logger.error("Failed text layout for %s: %s", video_dir.name, e)


def run_quality_scores(video_dirs: list[Path], device: str) -> None:
    """Compute quality scores for all videos."""
    from src.style_learner.feature_extraction.quality_scores import compute_all_quality_scores

    logger.info("=== Quality Score Computation ===")
    for i, video_dir in enumerate(video_dirs):
        logger.info("[%d/%d] Processing %s", i + 1, len(video_dirs), video_dir.name)
        try:
            compute_all_quality_scores(video_dir, device=device)
        except Exception as e:
            logger.error("Failed quality scores for %s: %s", video_dir.name, e)


def run_narration_alignment(video_dirs: list[Path]) -> None:
    """Run narration alignment on all videos."""
    from src.style_learner.feature_extraction.narration_alignment import align_narration_to_scenes

    logger.info("=== Narration Alignment ===")
    for i, video_dir in enumerate(video_dirs):
        logger.info("[%d/%d] Processing %s", i + 1, len(video_dirs), video_dir.name)
        whisper_path = video_dir / "whisper.json"
        scenes_path = video_dir / "scenes.json"

        if not whisper_path.exists():
            logger.warning("No whisper.json for %s, skipping narration", video_dir.name)
            continue
        if not scenes_path.exists():
            logger.warning("No scenes.json for %s, skipping narration", video_dir.name)
            continue

        try:
            with open(whisper_path) as f:
                whisper_data = json.load(f)
            with open(scenes_path) as f:
                scenes = json.load(f)

            # Extract word-level timestamps from Whisper output
            words = []
            for segment in whisper_data.get("segments", []):
                for word in segment.get("words", []):
                    words.append({
                        "word": word.get("word", ""),
                        "start": word.get("start", 0),
                        "end": word.get("end", 0),
                    })

            if not words:
                # Fallback: use segment-level text
                for segment in whisper_data.get("segments", []):
                    text = segment.get("text", "").strip()
                    if text:
                        words.append({
                            "word": text,
                            "start": segment.get("start", 0),
                            "end": segment.get("end", 0),
                        })

            results = align_narration_to_scenes(words, scenes)

            # Serialize (remove word dicts to save space, keep sentences)
            serializable = []
            for r in results:
                serializable.append({
                    "scene_id": r["scene_id"],
                    "start": r["start"],
                    "end": r["end"],
                    "sentences": r["sentences"],
                    "wpm": r["wpm"],
                    "narration_phase": r["narration_phase"],
                    "word_count": len(r["words"]),
                })

            output_path = video_dir / "narration_alignment.json"
            with open(output_path, "w") as f:
                json.dump(serializable, f, indent=2)
            logger.info("Saved narration alignment for %d scenes", len(serializable))
        except Exception as e:
            logger.error("Failed narration alignment for %s: %s", video_dir.name, e)


def run_dataset_build(data_dir: Path) -> None:
    """Assemble final dataset from all video features."""
    from src.style_learner.feature_extraction.dataset_builder import (
        build_dataset,
        generate_report,
        split_dataset,
    )

    logger.info("=== Dataset Assembly ===")
    try:
        dataset_path = build_dataset(data_dir)
        splits = split_dataset(dataset_path)
        report = generate_report(dataset_path, splits)
        print(report)
    except Exception as e:
        logger.error("Failed dataset assembly: %s", e)
        raise


def main() -> None:
    """Main entry point for feature extraction pipeline."""
    parser = argparse.ArgumentParser(
        description="Extract features from TED-Ed video dataset"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("data/style_reference/videos"),
        help="Root data directory containing video subdirectories",
    )
    parser.add_argument(
        "--device",
        type=str,
        default="cuda",
        choices=["cuda", "mps", "cpu"],
        help="Torch device for inference",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Process only the first 2 videos for quick testing",
    )
    parser.add_argument("--skip-clip", action="store_true", help="Skip CLIP extraction")
    parser.add_argument("--skip-motion", action="store_true", help="Skip camera motion")
    parser.add_argument("--skip-text", action="store_true", help="Skip text layout")
    parser.add_argument("--skip-quality", action="store_true", help="Skip quality scores")
    parser.add_argument("--skip-narration", action="store_true", help="Skip narration alignment")
    parser.add_argument("--skip-dataset", action="store_true", help="Skip dataset assembly")
    args = parser.parse_args()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

    device = _select_device(args.device)
    logger.info("Using device: %s", device)

    data_dir = args.data_dir.resolve()
    if not data_dir.exists():
        logger.error("Data directory does not exist: %s", data_dir)
        sys.exit(1)

    video_dirs = _find_video_dirs(data_dir)
    if not video_dirs:
        logger.error("No video directories with frames/ found in %s", data_dir)
        sys.exit(1)

    if args.test_mode:
        video_dirs = video_dirs[:2]
        logger.info("Test mode: processing %d videos", len(video_dirs))
    else:
        logger.info("Processing %d videos", len(video_dirs))

    start_time = time.time()

    # Run extraction pipeline in sequence
    if not args.skip_clip:
        run_clip_extraction(video_dirs, device)

    if not args.skip_motion:
        run_camera_motion(video_dirs)

    if not args.skip_text:
        run_text_layout(video_dirs)

    if not args.skip_quality:
        run_quality_scores(video_dirs, device)

    if not args.skip_narration:
        run_narration_alignment(video_dirs)

    if not args.skip_dataset:
        run_dataset_build(data_dir)

    elapsed = time.time() - start_time
    logger.info("Feature extraction complete in %.1f seconds (%.1f minutes)", elapsed, elapsed / 60)


if __name__ == "__main__":
    main()
