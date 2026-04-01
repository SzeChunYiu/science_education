"""Camera motion classification using Farneback optical flow.

Computes dense optical flow between consecutive keyframes and classifies
the dominant camera motion pattern (pan, zoom, parallax, static) with
magnitude estimation.
"""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Motion type labels
MOTION_TYPES = [
    "static",
    "pan_left",
    "pan_right",
    "pan_up",
    "pan_down",
    "zoom_in",
    "zoom_out",
    "parallax",
]

# Farneback optical flow parameters
_FLOW_PARAMS = dict(
    pyr_scale=0.5,
    levels=3,
    winsize=15,
    iterations=3,
    poly_n=5,
    poly_sigma=1.2,
    flags=0,
)

# Thresholds
_STATIC_THRESHOLD = 1.0  # mean magnitude below this is considered static
_ZOOM_DIVERGENCE_THRESHOLD = 0.3  # radial divergence ratio for zoom detection
_PARALLAX_VARIANCE_RATIO = 0.4  # high local variance relative to mean indicates parallax


def _compute_optical_flow(gray_a: np.ndarray, gray_b: np.ndarray) -> np.ndarray:
    """Compute dense optical flow between two grayscale frames."""
    return cv2.calcOpticalFlowFarneback(gray_a, gray_b, None, **_FLOW_PARAMS)


def _classify_from_flow(flow: np.ndarray) -> dict:
    """Classify camera motion from a flow field.

    Args:
        flow: HxWx2 optical flow array (dx, dy per pixel).

    Returns:
        Dict with 'motion' (str) and 'magnitude' (str: slow/medium/fast).
    """
    h, w = flow.shape[:2]

    # Mean flow vector
    mean_dx = np.mean(flow[..., 0])
    mean_dy = np.mean(flow[..., 1])
    mean_mag = np.sqrt(mean_dx**2 + mean_dy**2)

    # Per-pixel magnitudes
    magnitudes = np.sqrt(flow[..., 0] ** 2 + flow[..., 1] ** 2)
    overall_mag = np.mean(magnitudes)

    if overall_mag < _STATIC_THRESHOLD:
        return {"motion": "static", "magnitude": "slow"}

    # Check for zoom: radial divergence from center
    cy, cx = h / 2.0, w / 2.0
    ys, xs = np.mgrid[0:h, 0:w]
    rx = (xs - cx).astype(np.float32)
    ry = (ys - cy).astype(np.float32)
    radial_dist = np.sqrt(rx**2 + ry**2) + 1e-6

    # Dot product of flow with radial direction (positive = zoom out, negative = zoom in)
    radial_component = (flow[..., 0] * rx + flow[..., 1] * ry) / radial_dist
    mean_radial = np.mean(radial_component)
    radial_ratio = abs(mean_radial) / (overall_mag + 1e-6)

    if radial_ratio > _ZOOM_DIVERGENCE_THRESHOLD:
        motion = "zoom_out" if mean_radial > 0 else "zoom_in"
        magnitude = _magnitude_label(overall_mag)
        return {"motion": motion, "magnitude": magnitude}

    # Check for parallax: high spatial variance of flow directions
    # Split into grid blocks and measure variance of mean flow
    block_size = max(h // 4, 1)
    block_flows = []
    for by in range(0, h - block_size + 1, block_size):
        for bx in range(0, w - block_size + 1, block_size):
            block = flow[by : by + block_size, bx : bx + block_size]
            block_flows.append([np.mean(block[..., 0]), np.mean(block[..., 1])])
    block_flows = np.array(block_flows)
    flow_variance = np.mean(np.var(block_flows, axis=0))
    variance_ratio = flow_variance / (overall_mag**2 + 1e-6)

    if variance_ratio > _PARALLAX_VARIANCE_RATIO:
        magnitude = _magnitude_label(overall_mag)
        return {"motion": "parallax", "magnitude": magnitude}

    # Pan classification based on dominant mean flow direction
    abs_dx = abs(mean_dx)
    abs_dy = abs(mean_dy)

    if abs_dx > abs_dy:
        motion = "pan_right" if mean_dx > 0 else "pan_left"
    else:
        motion = "pan_down" if mean_dy > 0 else "pan_up"

    magnitude = _magnitude_label(overall_mag)
    return {"motion": motion, "magnitude": magnitude}


def _magnitude_label(mag: float, max_expected: float = 30.0) -> str:
    """Map a flow magnitude to slow/medium/fast.

    Normalizes against max_expected, then bins into thirds.
    """
    normalized = min(mag / max_expected, 1.0)
    if normalized < 0.33:
        return "slow"
    elif normalized < 0.66:
        return "medium"
    else:
        return "fast"


def classify_camera_motion(frame_a_path: Path, frame_b_path: Path) -> dict:
    """Classify camera motion between two consecutive frames.

    Args:
        frame_a_path: Path to the first frame image.
        frame_b_path: Path to the second frame image.

    Returns:
        Dict with 'motion' (str from MOTION_TYPES) and 'magnitude' (str).
    """
    img_a = cv2.imread(str(frame_a_path), cv2.IMREAD_GRAYSCALE)
    img_b = cv2.imread(str(frame_b_path), cv2.IMREAD_GRAYSCALE)

    if img_a is None:
        raise FileNotFoundError(f"Could not read frame: {frame_a_path}")
    if img_b is None:
        raise FileNotFoundError(f"Could not read frame: {frame_b_path}")

    # Resize for performance if frames are very large
    max_dim = 640
    h, w = img_a.shape[:2]
    if max(h, w) > max_dim:
        scale = max_dim / max(h, w)
        new_w, new_h = int(w * scale), int(h * scale)
        img_a = cv2.resize(img_a, (new_w, new_h))
        img_b = cv2.resize(img_b, (new_w, new_h))

    flow = _compute_optical_flow(img_a, img_b)
    return _classify_from_flow(flow)


def classify_scene_motion(frames_dir: Path, scene: dict) -> dict:
    """Classify camera motion for a scene using majority vote.

    Args:
        frames_dir: Path to the directory containing frame images.
        scene: Dict with 'start_frame' (int) and 'end_frame' (int) keys,
               or 'start' and 'end' as float timestamps. Frame filenames
               are expected to be sortable (e.g., frame_0001.png).

    Returns:
        Dict with 'motion' (str), 'magnitude' (str), and 'confidence' (float)
        based on majority vote across frame pairs within the scene.
    """
    frame_paths = sorted(
        p for p in frames_dir.iterdir()
        if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
    )
    if not frame_paths:
        logger.warning("No frames found in %s", frames_dir)
        return {"motion": "static", "magnitude": "slow", "confidence": 0.0}

    # Select frames within scene boundaries
    start_idx = scene.get("start_frame", 0)
    end_idx = scene.get("end_frame", len(frame_paths) - 1)
    scene_frames = frame_paths[start_idx : end_idx + 1]

    if len(scene_frames) < 2:
        return {"motion": "static", "magnitude": "slow", "confidence": 1.0}

    # Classify motion between consecutive pairs
    motion_votes = []
    magnitude_votes = []
    for i in range(len(scene_frames) - 1):
        try:
            result = classify_camera_motion(scene_frames[i], scene_frames[i + 1])
            motion_votes.append(result["motion"])
            magnitude_votes.append(result["magnitude"])
        except Exception as e:
            logger.warning("Failed to classify motion for pair %d-%d: %s", i, i + 1, e)

    if not motion_votes:
        return {"motion": "static", "magnitude": "slow", "confidence": 0.0}

    # Majority vote for motion type
    from collections import Counter

    motion_counts = Counter(motion_votes)
    top_motion, top_count = motion_counts.most_common(1)[0]
    confidence = top_count / len(motion_votes)

    # Majority vote for magnitude
    mag_counts = Counter(magnitude_votes)
    top_magnitude = mag_counts.most_common(1)[0][0]

    return {
        "motion": top_motion,
        "magnitude": top_magnitude,
        "confidence": round(confidence, 3),
    }
