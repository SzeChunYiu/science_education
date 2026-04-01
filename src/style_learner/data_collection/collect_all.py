"""Master orchestrator for the data collection pipeline.

Runs all collection steps in sequence:
1. Fetch playlist metadata
2. Download videos (positive examples)
3. Download negative channel examples
4. Extract frames
5. Extract transcripts
6. Detect scenes

Usage:
    python -m src.style_learner.data_collection.collect_all
    python -m src.style_learner.data_collection.collect_all --test-mode
    python -m src.style_learner.data_collection.collect_all --skip-download --skip-negatives
"""

import argparse
import json
import logging
import sys
from pathlib import Path

from .playlist_fetcher import fetch_all_playlists
from .video_downloader import (
    NEGATIVE_CHANNELS,
    download_negative_channels,
    download_videos,
)
from .frame_extractor import extract_all_frames
from .transcript_extractor import extract_all_transcripts
from .scene_detector import detect_all_scenes

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/style_reference")
VIDEOS_DIR = DATA_DIR / "videos"
PLAYLISTS_FILE = DATA_DIR / "playlists.txt"


def main() -> None:
    """Run the full data collection pipeline."""
    parser = argparse.ArgumentParser(
        description="Collect style reference data from YouTube channels."
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Limit to 3 videos for quick testing.",
    )
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip video download step (use existing downloads).",
    )
    parser.add_argument(
        "--skip-negatives",
        action="store_true",
        help="Skip downloading negative channel examples.",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    logger.info("=== Data Collection Pipeline ===")
    if args.test_mode:
        logger.info("TEST MODE: limiting to 3 videos")

    # Step 1: Fetch playlist metadata
    logger.info("--- Step 1: Fetching playlist metadata ---")
    index_path = DATA_DIR / "index.json"
    if index_path.exists():
        logger.info("index.json already exists, loading...")
        videos = json.loads(index_path.read_text())
    else:
        videos = fetch_all_playlists(PLAYLISTS_FILE)

    if not videos:
        logger.error("No videos found. Check playlists.txt and try again.")
        sys.exit(1)

    if args.test_mode:
        videos = videos[:3]

    logger.info("Working with %d videos", len(videos))

    # Step 2: Download videos
    if not args.skip_download:
        logger.info("--- Step 2: Downloading videos ---")
        batch_size = 3 if args.test_mode else 10
        delay = 10 if args.test_mode else 30
        downloaded = download_videos(
            videos,
            output_dir=VIDEOS_DIR,
            batch_size=batch_size,
            delay=delay,
        )
        logger.info("Downloaded %d videos", len(downloaded))
    else:
        logger.info("--- Step 2: Skipping download (--skip-download) ---")

    # Step 3: Download negative examples
    if not args.skip_negatives and not args.skip_download:
        logger.info("--- Step 3: Downloading negative channel examples ---")
        max_neg = 3 if args.test_mode else 20
        download_negative_channels(
            channels=NEGATIVE_CHANNELS,
            max_videos=max_neg,
        )
    else:
        logger.info("--- Step 3: Skipping negatives ---")

    # Step 4: Extract frames
    logger.info("--- Step 4: Extracting frames ---")
    frame_results = extract_all_frames(VIDEOS_DIR, fps=2)
    logger.info(
        "Frames: %d videos, %d total frames",
        len(frame_results),
        sum(frame_results.values()),
    )

    # Step 5: Extract transcripts
    logger.info("--- Step 5: Extracting transcripts ---")
    transcript_results = extract_all_transcripts(VIDEOS_DIR)
    logger.info(
        "Transcripts: %d videos, %d total words",
        len(transcript_results),
        sum(transcript_results.values()),
    )

    # Step 6: Detect scenes
    logger.info("--- Step 6: Detecting scenes ---")
    scene_results = detect_all_scenes(VIDEOS_DIR, threshold=27.0)
    logger.info(
        "Scenes: %d videos, %d total scenes",
        len(scene_results),
        sum(scene_results.values()),
    )

    # Summary
    logger.info("=== Pipeline Complete ===")
    logger.info("Videos indexed: %d", len(videos))
    logger.info("Frames extracted: %d", sum(frame_results.values()))
    logger.info("Words transcribed: %d", sum(transcript_results.values()))
    logger.info("Scenes detected: %d", sum(scene_results.values()))


if __name__ == "__main__":
    main()
