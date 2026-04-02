"""Video quality checker for rendered episode videos.

Extracts frames at regular intervals and runs heuristic checks for
production readiness: background quality, text placement, asset sizing,
visual clutter, blank frames, duration, scene transitions, and audio.

Usage:
    from src.quality.video_qa import check_video_quality
    report = check_video_quality("path/to/video.mp4")
    print(report["summary"])

CLI:
    python3 src/quality/video_qa.py path/to/video.mp4
"""
import json
import logging
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
FRAME_INTERVAL_SEC = 10
SUBTITLE_ZONE_RATIO = 0.20  # bottom 20%
MIN_ASSET_RATIO = 0.05  # assets smaller than 5% of canvas are suspect
MAX_VISUAL_ELEMENTS = 6
MIN_DURATION_SEC = 300  # 5 minutes
MAX_DURATION_SEC = 900  # 15 minutes
BLANK_THRESHOLD = 0.95  # fraction of pixels in dominant color to flag blank
COLOR_STD_THRESHOLD = 12.0  # std-dev below which a frame is "flat" color
SCENE_CHANGE_THRESHOLD = 15.0  # mean pixel diff to count as scene change


# ---------------------------------------------------------------------------
# ffmpeg / ffprobe helpers
# ---------------------------------------------------------------------------

def _run_cmd(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run a subprocess command and return the result."""
    return subprocess.run(cmd, capture_output=True, text=True, timeout=120)


def _get_video_duration(video_path: str) -> float:
    """Return video duration in seconds via ffprobe."""
    result = _run_cmd([
        "ffprobe", "-v", "quiet",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        video_path,
    ])
    if result.returncode != 0:
        logger.warning("ffprobe duration failed: %s", result.stderr)
        return 0.0
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def _has_audio_track(video_path: str) -> bool:
    """Return True if the video contains at least one audio stream."""
    result = _run_cmd([
        "ffprobe", "-v", "quiet",
        "-select_streams", "a",
        "-show_entries", "stream=index",
        "-of", "csv=p=0",
        video_path,
    ])
    return bool(result.stdout.strip())


def _extract_frames(video_path: str, interval: int, output_dir: str) -> list[str]:
    """Extract one frame every *interval* seconds. Return list of paths."""
    pattern = str(Path(output_dir) / "frame_%05d.png")
    result = _run_cmd([
        "ffmpeg", "-i", video_path,
        "-vf", f"fps=1/{interval}",
        "-q:v", "2",
        pattern,
    ])
    if result.returncode != 0:
        logger.warning("ffmpeg frame extraction failed: %s", result.stderr)
        return []
    frames = sorted(Path(output_dir).glob("frame_*.png"))
    return [str(f) for f in frames]


# ---------------------------------------------------------------------------
# Per-frame checks
# ---------------------------------------------------------------------------

def _check_blank_frame(arr: np.ndarray) -> dict:
    """Detect frames that are mostly one solid color."""
    gray = np.mean(arr, axis=2)  # average across channels
    std = float(np.std(gray))
    is_blank = std < COLOR_STD_THRESHOLD

    # Also check dominant-color pixel fraction
    rounded = (arr // 32).reshape(-1, 3)
    _, counts = np.unique(rounded, axis=0, return_counts=True)
    dominant_frac = float(counts.max()) / len(rounded)

    return {
        "is_blank": is_blank or dominant_frac > BLANK_THRESHOLD,
        "color_std": round(std, 2),
        "dominant_color_fraction": round(dominant_frac, 3),
    }


def _check_background(arr: np.ndarray) -> dict:
    """Check whether the frame has a real background (not flat solid)."""
    h, w = arr.shape[:2]
    # Sample the outer border ring (top/bottom 5%, left/right 5%)
    border_top = arr[:int(h * 0.05), :, :]
    border_bot = arr[int(h * 0.95):, :, :]
    border_left = arr[:, :int(w * 0.05), :]
    border_right = arr[:, int(w * 0.95):, :]

    border = np.concatenate([
        border_top.reshape(-1, 3),
        border_bot.reshape(-1, 3),
        border_left.reshape(-1, 3),
        border_right.reshape(-1, 3),
    ], axis=0)

    border_std = float(np.std(border))
    # Also check full-frame std
    full_std = float(np.std(arr.astype(np.float32)))

    has_background = full_std > 20.0 and border_std > 8.0
    return {
        "has_proper_background": has_background,
        "full_frame_std": round(full_std, 2),
        "border_std": round(border_std, 2),
    }


def _check_subtitle_zone(arr: np.ndarray) -> dict:
    """Check if the bottom 20% zone has content that could clash with subtitles.

    Heuristic: high edge density in subtitle zone suggests placed content
    that would overlap with subtitle text.
    """
    h, w = arr.shape[:2]
    zone_start = int(h * (1.0 - SUBTITLE_ZONE_RATIO))
    zone = arr[zone_start:, :, :]

    gray_zone = np.mean(zone, axis=2)
    # Simple edge detection via horizontal gradient magnitude
    dx = np.abs(np.diff(gray_zone, axis=1).astype(np.float32))
    dy = np.abs(np.diff(gray_zone, axis=0).astype(np.float32))
    edge_density = float(np.mean(dx > 30) + np.mean(dy > 30)) / 2.0

    # Compare to content zone (top 80%)
    content = arr[:zone_start, :, :]
    gray_content = np.mean(content, axis=2)
    cdx = np.abs(np.diff(gray_content, axis=1).astype(np.float32))
    cdy = np.abs(np.diff(gray_content, axis=0).astype(np.float32))
    content_edge_density = float(np.mean(cdx > 30) + np.mean(cdy > 30)) / 2.0

    # If subtitle zone has comparable or higher edge density, flag it
    zone_cluttered = edge_density > 0.05 and edge_density > content_edge_density * 0.5
    return {
        "subtitle_zone_clear": not zone_cluttered,
        "zone_edge_density": round(edge_density, 4),
        "content_edge_density": round(content_edge_density, 4),
    }


def _check_asset_sizes(arr: np.ndarray) -> dict:
    """Detect if placed assets are too small (thumbnail-sized).

    Heuristic: find connected regions of non-background color and check
    if any are smaller than MIN_ASSET_RATIO of the canvas.
    Uses a simplified approach based on color clustering.
    """
    h, w = arr.shape[:2]
    canvas_area = h * w

    gray = np.mean(arr, axis=2)
    # Find high-contrast regions via thresholding on local variance
    from PIL import ImageFilter
    img = Image.fromarray(arr)
    edges = np.array(img.filter(ImageFilter.FIND_EDGES).convert("L"), dtype=np.float32)

    # Binary mask of "object" pixels (edges above threshold)
    mask = edges > 40
    object_pixel_count = int(np.sum(mask))
    object_ratio = object_pixel_count / canvas_area

    # Look for tiny clusters: split into grid and check
    tiny_assets = 0
    grid_size = 8
    cell_h, cell_w = h // grid_size, w // grid_size
    small_clusters = []
    for r in range(grid_size):
        for c in range(grid_size):
            cell = mask[r * cell_h:(r + 1) * cell_h, c * cell_w:(c + 1) * cell_w]
            cell_density = float(np.mean(cell))
            cell_area_ratio = (cell_h * cell_w) / canvas_area
            if 0.1 < cell_density < 0.8 and cell_area_ratio < MIN_ASSET_RATIO:
                # This cell has an object fragment that fits in a tiny region
                tiny_assets += 1
                small_clusters.append((r, c))

    has_tiny_assets = tiny_assets > 2  # multiple tiny clusters suggest thumbnails
    return {
        "has_tiny_assets": has_tiny_assets,
        "object_coverage_ratio": round(object_ratio, 4),
        "tiny_cluster_count": tiny_assets,
    }


def _check_visual_clutter(arr: np.ndarray) -> dict:
    """Estimate number of distinct visual elements via color segmentation.

    Simple approach: quantize colors, count distinct regions.
    """
    h, w = arr.shape[:2]
    # Downsample for speed
    small = Image.fromarray(arr).resize((w // 4, h // 4), Image.NEAREST)
    small_arr = np.array(small)

    # Quantize to 8 colors
    quantized = (small_arr // 48) * 48
    flat = quantized.reshape(-1, 3)
    unique_colors = np.unique(flat, axis=0)
    n_regions = len(unique_colors)

    # Map to approximate "element count" (very rough heuristic)
    # Few unique quantized colors = few elements, many = complex scene
    # Typical good frame: 8-25 quantized colors
    estimated_elements = max(0, n_regions - 3)  # subtract background-ish colors
    too_many = estimated_elements > MAX_VISUAL_ELEMENTS * 4  # quantized colors != elements
    too_few = estimated_elements < 2

    return {
        "estimated_elements": estimated_elements,
        "too_cluttered": too_many,
        "too_empty": too_few,
        "quantized_color_count": n_regions,
    }


# ---------------------------------------------------------------------------
# Full-video checks
# ---------------------------------------------------------------------------

def _check_duration(duration: float) -> dict:
    """Check video duration is within expected range for youtube_long."""
    return {
        "duration_sec": round(duration, 1),
        "in_range": MIN_DURATION_SEC <= duration <= MAX_DURATION_SEC,
        "min_expected": MIN_DURATION_SEC,
        "max_expected": MAX_DURATION_SEC,
    }


def _check_scene_transitions(frame_paths: list[str]) -> dict:
    """Detect whether the video has scene changes (not stuck on one frame)."""
    if len(frame_paths) < 2:
        return {"scene_changes": 0, "has_transitions": False, "total_frames": len(frame_paths)}

    changes = 0
    prev_arr = np.array(Image.open(frame_paths[0]).convert("RGB"), dtype=np.float32)

    for fp in frame_paths[1:]:
        curr_arr = np.array(Image.open(fp).convert("RGB"), dtype=np.float32)
        # Resize to same dims if needed (shouldn't differ, but safe)
        if curr_arr.shape != prev_arr.shape:
            curr_img = Image.open(fp).convert("RGB").resize(
                (prev_arr.shape[1], prev_arr.shape[0])
            )
            curr_arr = np.array(curr_img, dtype=np.float32)

        diff = float(np.mean(np.abs(curr_arr - prev_arr)))
        if diff > SCENE_CHANGE_THRESHOLD:
            changes += 1
        prev_arr = curr_arr

    return {
        "scene_changes": changes,
        "has_transitions": changes >= 1,
        "total_frames": len(frame_paths),
    }


# ---------------------------------------------------------------------------
# Scoring helpers
# ---------------------------------------------------------------------------

def _score_from_bool(value: bool) -> int:
    """Convert boolean pass/fail to 0 or 100."""
    return 100 if value else 0


def _compute_frame_scores(frame_results: list[dict]) -> dict[str, int]:
    """Aggregate per-frame check results into 0-100 scores."""
    if not frame_results:
        return {
            "background": 0,
            "subtitle_zone": 0,
            "asset_quality": 0,
            "visual_clutter": 0,
            "blank_frames": 0,
        }

    n = len(frame_results)

    bg_pass = sum(1 for f in frame_results if f["background"]["has_proper_background"]) / n
    sub_pass = sum(1 for f in frame_results if f["subtitle_zone"]["subtitle_zone_clear"]) / n
    asset_pass = sum(1 for f in frame_results if not f["asset_sizes"]["has_tiny_assets"]) / n
    clutter_pass = sum(
        1 for f in frame_results
        if not f["visual_clutter"]["too_cluttered"] and not f["visual_clutter"]["too_empty"]
    ) / n
    blank_pass = sum(1 for f in frame_results if not f["blank"]["is_blank"]) / n

    return {
        "background": int(round(bg_pass * 100)),
        "subtitle_zone": int(round(sub_pass * 100)),
        "asset_quality": int(round(asset_pass * 100)),
        "visual_clutter": int(round(clutter_pass * 100)),
        "blank_frames": int(round(blank_pass * 100)),
    }


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def check_video_quality(video_path: str, frame_interval: int = FRAME_INTERVAL_SEC) -> dict[str, Any]:
    """Run all quality checks on a rendered video and return a JSON-serializable report.

    Args:
        video_path: Path to the video file.
        frame_interval: Seconds between extracted frames (default 10).

    Returns:
        Dict with keys: passed, scores, issues, frame_count, summary.
    """
    video_path = str(Path(video_path).resolve())
    if not Path(video_path).exists():
        return {
            "passed": False,
            "scores": {},
            "issues": [{"timestamp": None, "check": "file", "message": "Video file not found"}],
            "frame_count": 0,
            "summary": f"FAIL: Video file not found: {video_path}",
        }

    issues: list[dict] = []

    # --- Full-video checks ---
    duration = _get_video_duration(video_path)
    duration_result = _check_duration(duration)
    if not duration_result["in_range"]:
        issues.append({
            "timestamp": None,
            "check": "duration",
            "message": (
                f"Duration {duration_result['duration_sec']}s outside "
                f"expected range [{MIN_DURATION_SEC}-{MAX_DURATION_SEC}]s"
            ),
        })

    audio_present = _has_audio_track(video_path)
    if not audio_present:
        issues.append({
            "timestamp": None,
            "check": "audio",
            "message": "No audio track found in video",
        })

    # --- Extract frames ---
    with tempfile.TemporaryDirectory(prefix="video_qa_") as tmpdir:
        frame_paths = _extract_frames(video_path, frame_interval, tmpdir)

        # --- Scene transitions ---
        transition_result = _check_scene_transitions(frame_paths)
        if not transition_result["has_transitions"]:
            issues.append({
                "timestamp": None,
                "check": "scene_transitions",
                "message": "No scene transitions detected -- video may be stuck on one frame",
            })

        # --- Per-frame checks ---
        frame_results = []
        for idx, fp in enumerate(frame_paths):
            timestamp_sec = idx * frame_interval
            arr = np.array(Image.open(fp).convert("RGB"))

            result = {
                "timestamp": timestamp_sec,
                "blank": _check_blank_frame(arr),
                "background": _check_background(arr),
                "subtitle_zone": _check_subtitle_zone(arr),
                "asset_sizes": _check_asset_sizes(arr),
                "visual_clutter": _check_visual_clutter(arr),
            }
            frame_results.append(result)

            # Collect issues
            ts_str = f"{timestamp_sec // 60}:{timestamp_sec % 60:02d}"
            if result["blank"]["is_blank"]:
                issues.append({
                    "timestamp": ts_str,
                    "check": "blank_frame",
                    "message": f"Blank/solid frame at {ts_str} (std={result['blank']['color_std']})",
                })
            if not result["background"]["has_proper_background"]:
                issues.append({
                    "timestamp": ts_str,
                    "check": "background",
                    "message": f"Missing/flat background at {ts_str}",
                })
            if not result["subtitle_zone"]["subtitle_zone_clear"]:
                issues.append({
                    "timestamp": ts_str,
                    "check": "subtitle_zone",
                    "message": (
                        f"Content in subtitle zone at {ts_str} "
                        f"(edge_density={result['subtitle_zone']['zone_edge_density']})"
                    ),
                })
            if result["asset_sizes"]["has_tiny_assets"]:
                issues.append({
                    "timestamp": ts_str,
                    "check": "asset_quality",
                    "message": f"Tiny assets detected at {ts_str}",
                })
            if result["visual_clutter"]["too_cluttered"]:
                issues.append({
                    "timestamp": ts_str,
                    "check": "visual_clutter",
                    "message": (
                        f"Too cluttered at {ts_str} "
                        f"({result['visual_clutter']['estimated_elements']} elements)"
                    ),
                })
            if result["visual_clutter"]["too_empty"]:
                issues.append({
                    "timestamp": ts_str,
                    "check": "visual_clutter",
                    "message": f"Too few visual elements at {ts_str}",
                })

    # --- Compute scores ---
    frame_scores = _compute_frame_scores(frame_results)
    scores = {
        **frame_scores,
        "duration": _score_from_bool(duration_result["in_range"]),
        "scene_transitions": _score_from_bool(transition_result["has_transitions"]),
        "audio_presence": _score_from_bool(audio_present),
    }

    # Overall pass: all scores >= 60
    passed = all(v >= 60 for v in scores.values())

    # Summary
    failing = [k for k, v in scores.items() if v < 60]
    if passed:
        summary = f"PASS: All {len(scores)} checks passed ({len(frame_results)} frames analyzed)"
    else:
        summary = (
            f"FAIL: {len(failing)} check(s) below threshold: "
            f"{', '.join(failing)} | {len(issues)} issue(s) found"
        )

    return {
        "passed": passed,
        "scores": scores,
        "issues": issues,
        "frame_count": len(frame_results),
        "duration_sec": round(duration, 1),
        "details": {
            "duration": duration_result,
            "transitions": transition_result,
            "audio_present": audio_present,
        },
        "summary": summary,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    """CLI entry point."""
    if len(sys.argv) < 2:
        print(f"Usage: python3 {sys.argv[0]} <video_path> [--interval N]")
        sys.exit(1)

    video_path = sys.argv[1]
    interval = FRAME_INTERVAL_SEC

    if "--interval" in sys.argv:
        idx = sys.argv.index("--interval")
        if idx + 1 < len(sys.argv):
            interval = int(sys.argv[idx + 1])

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    print(f"Checking video: {video_path}")
    print(f"Frame interval: {interval}s")
    print()

    report = check_video_quality(video_path, frame_interval=interval)

    # Print summary
    status = "PASS" if report["passed"] else "FAIL"
    print(f"Result: {status}")
    print(f"Frames analyzed: {report['frame_count']}")
    print(f"Duration: {report.get('duration_sec', 0)}s")
    print()

    # Print scores
    print("Scores:")
    for check_name, score in report["scores"].items():
        marker = "OK" if score >= 60 else "!!"
        print(f"  [{marker}] {check_name}: {score}/100")
    print()

    # Print issues
    if report["issues"]:
        print(f"Issues ({len(report['issues'])}):")
        for issue in report["issues"]:
            ts = issue["timestamp"] or "global"
            print(f"  [{ts}] {issue['check']}: {issue['message']}")
    else:
        print("No issues found.")
    print()
    print(report["summary"])

    # Also write JSON report alongside the video
    json_path = Path(video_path).with_suffix(".qa_report.json")
    with open(json_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nJSON report written to: {json_path}")

    sys.exit(0 if report["passed"] else 1)


if __name__ == "__main__":
    main()
