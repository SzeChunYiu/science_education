"""Fetch video metadata from YouTube playlists using yt-dlp.

Runs yt-dlp --dump-json --flat-playlist to collect metadata without
downloading actual video content. Deduplicates across playlists by
video_id and saves a consolidated index.json to data/style_reference/.
"""

import json
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/style_reference")


def fetch_playlist_metadata(playlist_url: str) -> list[dict]:
    """Fetch video metadata from a single YouTube playlist.

    Args:
        playlist_url: Full YouTube playlist URL.

    Returns:
        List of dicts with keys: video_id, title, duration, view_count, url.
    """
    logger.info("Fetching playlist: %s", playlist_url)
    cmd = [
        "yt-dlp",
        "--dump-json",
        "--flat-playlist",
        "--no-warnings",
        playlist_url,
    ]
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=300,
        )
    except subprocess.TimeoutExpired:
        logger.error("Timeout fetching playlist: %s", playlist_url)
        return []
    except FileNotFoundError:
        logger.error("yt-dlp not found. Install with: pip install yt-dlp")
        return []

    if result.returncode != 0:
        logger.error(
            "yt-dlp failed for %s: %s", playlist_url, result.stderr.strip()
        )
        return []

    videos = []
    for line in result.stdout.strip().splitlines():
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Skipping malformed JSON line in playlist output")
            continue

        video_id = entry.get("id", "")
        if not video_id:
            continue

        videos.append(
            {
                "video_id": video_id,
                "title": entry.get("title", ""),
                "duration": entry.get("duration"),
                "view_count": entry.get("view_count"),
                "url": f"https://www.youtube.com/watch?v={video_id}",
            }
        )

    logger.info("Found %d videos in playlist", len(videos))
    return videos


def fetch_all_playlists(playlists_file: Path) -> list[dict]:
    """Fetch metadata from all playlists listed in a text file.

    Reads one playlist URL per line from playlists_file, fetches metadata
    for each, deduplicates by video_id, and saves the result to
    data/style_reference/index.json.

    Args:
        playlists_file: Path to text file with one playlist URL per line.

    Returns:
        Deduplicated list of video metadata dicts.
    """
    if not playlists_file.exists():
        logger.error("Playlists file not found: %s", playlists_file)
        return []

    urls = [
        line.strip()
        for line in playlists_file.read_text().splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    logger.info("Processing %d playlists", len(urls))

    all_videos: list[dict] = []
    for url in urls:
        videos = fetch_playlist_metadata(url)
        all_videos.extend(videos)

    # Deduplicate by video_id, keeping first occurrence
    seen: set[str] = set()
    unique: list[dict] = []
    for v in all_videos:
        if v["video_id"] not in seen:
            seen.add(v["video_id"])
            unique.append(v)

    logger.info(
        "Total: %d videos (%d after dedup)", len(all_videos), len(unique)
    )

    # Save index
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    index_path = DATA_DIR / "index.json"
    index_path.write_text(json.dumps(unique, indent=2))
    logger.info("Saved index to %s", index_path)

    return unique


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    playlists_file = DATA_DIR / "playlists.txt"
    fetch_all_playlists(playlists_file)
