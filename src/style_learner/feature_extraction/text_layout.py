"""Text region detection and layout analysis using EasyOCR.

Detects text regions in keyframes, classifies their role (title, subtitle,
caption, label, annotation), and tracks text entrance patterns across
consecutive frames.
"""

import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# Role classification thresholds (relative to frame dimensions)
_TITLE_MIN_HEIGHT_RATIO = 0.08
_SUBTITLE_MIN_HEIGHT_RATIO = 0.04
_CAPTION_MAX_HEIGHT_RATIO = 0.04


class TextLayoutExtractor:
    """Detects and classifies text regions in keyframes."""

    def __init__(self) -> None:
        import easyocr

        logger.info("Initializing EasyOCR reader (English)")
        self.reader = easyocr.Reader(["en"], gpu=True, verbose=False)

    def extract_text_regions(self, image_path: Path) -> list[dict]:
        """Detect text regions and classify their role.

        Args:
            image_path: Path to the keyframe image.

        Returns:
            List of dicts, each with keys:
                cx, cy: center position (normalized 0-1)
                w, h: width and height (normalized 0-1)
                content: detected text string
                role: one of title, subtitle, caption, label, annotation
                confidence: OCR confidence score (0-1)
        """
        img = cv2.imread(str(image_path))
        if img is None:
            raise FileNotFoundError(f"Could not read image: {image_path}")

        frame_h, frame_w = img.shape[:2]
        results = self.reader.readtext(str(image_path))

        regions = []
        for bbox, text, confidence in results:
            if confidence < 0.2:
                continue

            # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            xs = [pt[0] for pt in bbox]
            ys = [pt[1] for pt in bbox]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)

            # Normalize to 0-1 range
            cx = ((x_min + x_max) / 2.0) / frame_w
            cy = ((y_min + y_max) / 2.0) / frame_h
            w = (x_max - x_min) / frame_w
            h = (y_max - y_min) / frame_h

            role = self._classify_role(cx, cy, w, h)

            regions.append({
                "cx": round(cx, 4),
                "cy": round(cy, 4),
                "w": round(w, 4),
                "h": round(h, 4),
                "content": text.strip(),
                "role": role,
                "confidence": round(float(confidence), 4),
            })

        logger.debug("Found %d text regions in %s", len(regions), image_path.name)
        return regions

    def _classify_role(self, cx: float, cy: float, w: float, h: float) -> str:
        """Classify text role based on size and position.

        Rules:
            title: height > 8% AND in top 40% of frame
            subtitle: height 4-8% AND in top 50% of frame
            caption: height < 4% AND in bottom 25% of frame
            label: height < 4% AND in mid-frame (25-75% vertically)
            annotation: everything else
        """
        if h > _TITLE_MIN_HEIGHT_RATIO and cy < 0.40:
            return "title"
        elif _SUBTITLE_MIN_HEIGHT_RATIO <= h <= _TITLE_MIN_HEIGHT_RATIO and cy < 0.50:
            return "subtitle"
        elif h < _CAPTION_MAX_HEIGHT_RATIO and cy > 0.75:
            return "caption"
        elif h < _CAPTION_MAX_HEIGHT_RATIO and 0.25 <= cy <= 0.75:
            return "label"
        else:
            return "annotation"

    def track_text_entrance(self, frame_paths: list[Path]) -> list[dict]:
        """Track text appearance across consecutive frames and classify entrance type.

        Args:
            frame_paths: Ordered list of frame image paths.

        Returns:
            List of dicts describing text entrance events, each with keys:
                content: the text string
                first_frame: index of first appearance
                entrance: one of fade_in, slide_in, pop_in
                position: {cx, cy} of final position
        """
        if not frame_paths:
            return []

        # Extract text regions for each frame
        frame_regions = []
        for path in frame_paths:
            try:
                regions = self.extract_text_regions(path)
                frame_regions.append(regions)
            except Exception as e:
                logger.warning("Failed to extract text from %s: %s", path, e)
                frame_regions.append([])

        # Track unique text strings across frames
        text_tracking: dict[str, list[dict]] = {}
        for frame_idx, regions in enumerate(frame_regions):
            for region in regions:
                content = region["content"]
                if not content:
                    continue
                key = _normalize_text_key(content)
                if key not in text_tracking:
                    text_tracking[key] = []
                text_tracking[key].append({
                    "frame_idx": frame_idx,
                    "cx": region["cx"],
                    "cy": region["cy"],
                    "confidence": region["confidence"],
                    "content": content,
                })

        # Classify entrance for each text element
        entrances = []
        for key, appearances in text_tracking.items():
            if not appearances:
                continue

            appearances.sort(key=lambda x: x["frame_idx"])
            first_frame = appearances[0]["frame_idx"]
            final = appearances[-1]

            entrance_type = _classify_entrance(appearances)

            entrances.append({
                "content": appearances[0]["content"],
                "first_frame": first_frame,
                "entrance": entrance_type,
                "position": {"cx": final["cx"], "cy": final["cy"]},
            })

        entrances.sort(key=lambda x: x["first_frame"])
        return entrances


def _normalize_text_key(text: str) -> str:
    """Normalize text for matching across frames (lowercase, strip whitespace)."""
    return text.strip().lower()


def _classify_entrance(appearances: list[dict]) -> str:
    """Classify how text enters the frame based on position/confidence changes.

    - pop_in: appears in a single frame (no gradual appearance)
    - slide_in: position shifts significantly across first few frames
    - fade_in: confidence increases gradually (text becoming more readable)
    """
    if len(appearances) < 2:
        return "pop_in"

    # Check for position shift (slide_in)
    first = appearances[0]
    second = appearances[min(1, len(appearances) - 1)]
    dx = abs(second["cx"] - first["cx"])
    dy = abs(second["cy"] - first["cy"])
    position_shift = (dx**2 + dy**2) ** 0.5

    if position_shift > 0.05:
        return "slide_in"

    # Check for confidence ramp (fade_in)
    early_conf = np.mean([a["confidence"] for a in appearances[:2]])
    late_conf = np.mean([a["confidence"] for a in appearances[-2:]])
    if late_conf - early_conf > 0.15:
        return "fade_in"

    return "pop_in"
