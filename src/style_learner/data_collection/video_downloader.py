"""Download videos in batches with rate limiting and resumability.

Uses yt-dlp with --download-archive to track already-downloaded videos,
enabling safe resumption after interrupts. Downloads mp4 video, mp3 audio,
and auto-generated subtitles for each video.
"""

import logging
import subprocess
import time
from pathlib import Path

logger = logging.getLogger(__name__)

NEGATIVE_CHANNELS = {
    "kurzgesagt": "https://www.youtube.com/@kurzgesagt",
    "primer": "https://www.youtube.com/@PrimerBlobs",
    "crashcourse": "https://www.youtube.com/@crashcourse",
}


def _run_ytdlp(args: list[str], timeout: int = 600) -> bool:
    """Run a yt-dlp command, returning True on success."""
    cmd = ["yt-dlp"] + args
    logger.debug("Running: %s", " ".join(cmd))
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode != 0:
            logger.warning("yt-dlp error: %s", result.stderr.strip()[:500])
            return False
        return True
    except subprocess.TimeoutExpired:
        logger.warning("yt-dlp timed out after %ds", timeout)
        return False
    except FileNotFoundError:
        logger.error("yt-dlp not found. Install with: pip install yt-dlp")
        return False


def download_videos(
    videos: list[dict],
    output_dir: Path,
    batch_size: int = 10,
    delay: int = 30,
) -> list[str]:
    """Download videos with batching and rate limiting.

    Downloads each video as mp4 + mp3 + auto-subs into a per-video
    subdirectory under output_dir. Uses --download-archive for
    resumability so already-downloaded videos are skipped.

    Args:
        videos: List of dicts with at least 'video_id' and 'url' keys.
        output_dir: Base directory for downloads.
        batch_size: Number of videos per batch before pausing.
        delay: Seconds to wait between batches.

    Returns:
        List of video_ids that were successfully downloaded.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    archive_file = output_dir / ".download_archive"
    downloaded: list[str] = []

    for i, video in enumerate(videos):
        vid = video["video_id"]
        url = video["url"]
        vid_dir = output_dir / vid
        vid_dir.mkdir(parents=True, exist_ok=True)

        logger.info("[%d/%d] Downloading %s", i + 1, len(videos), vid)

        # Download video (mp4) — no archive here, skip check via file existence
        video_file = vid_dir / "video.mp4"
        if video_file.exists():
            video_ok = True
        else:
            video_ok = _run_ytdlp(
                [
                    "-f",
                    "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format",
                    "mp4",
                    "-o",
                    str(vid_dir / "video.%(ext)s"),
                    url,
                ],
                timeout=1200,
            )

        # Download audio (mp3)
        audio_ok = _run_ytdlp(
            [
                "-x",
                "--audio-format",
                "mp3",
                "-o",
                str(vid_dir / "audio.%(ext)s"),
                "--no-overwrites",
                url,
            ],
            timeout=600,
        )

        # Download auto-subs (VTT)
        subs_ok = _run_ytdlp(
            [
                "--write-auto-sub",
                "--sub-lang",
                "en",
                "--sub-format",
                "vtt",
                "--skip-download",
                "-o",
                str(vid_dir / "subs.%(ext)s"),
                "--no-overwrites",
                url,
            ],
            timeout=120,
        )

        if video_ok or audio_ok:
            downloaded.append(vid)
            logger.info("Downloaded %s (video=%s audio=%s subs=%s)",
                        vid, video_ok, audio_ok, subs_ok)
        else:
            logger.error("Failed to download %s", vid)

        # Rate limit between batches
        if (i + 1) % batch_size == 0 and (i + 1) < len(videos):
            logger.info("Batch pause: sleeping %ds...", delay)
            time.sleep(delay)

    logger.info("Downloaded %d/%d videos", len(downloaded), len(videos))
    return downloaded


def download_negative_channels(
    channels: dict[str, str] | None = None,
    max_videos: int = 20,
    output_base: Path = Path("data/style_reference/negatives"),
) -> None:
    """Download videos from negative-example channels for discriminator training.

    These channels (Kurzgesagt, Primer, CrashCourse) have distinct visual
    styles that serve as negative examples when training the style
    discriminator.

    Args:
        channels: Dict mapping channel name to URL. Defaults to NEGATIVE_CHANNELS.
        max_videos: Maximum videos to download per channel.
        output_base: Base output directory for negative samples.
    """
    if channels is None:
        channels = NEGATIVE_CHANNELS

    output_base.mkdir(parents=True, exist_ok=True)

    for name, url in channels.items():
        channel_dir = output_base / name
        channel_dir.mkdir(parents=True, exist_ok=True)
        archive_file = channel_dir / ".download_archive"

        logger.info("Downloading up to %d videos from %s", max_videos, name)

        ok = _run_ytdlp(
            [
                "--download-archive",
                str(archive_file),
                "--playlist-end",
                str(max_videos),
                "-f",
                "bestvideo[vcodec^=avc1][ext=mp4]+bestaudio[ext=m4a]/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                "--merge-output-format",
                "mp4",
                "-o",
                str(channel_dir / "%(id)s/video.%(ext)s"),
                "--write-auto-sub",
                "--sub-lang",
                "en",
                "--sub-format",
                "vtt",
                "-x",
                "--audio-format",
                "mp3",
                url,
            ],
            timeout=3600,
        )

        if ok:
            logger.info("Finished downloading from %s", name)
        else:
            logger.warning("Issues downloading from %s", name)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    # Quick test: download negatives only
    download_negative_channels(max_videos=3)
