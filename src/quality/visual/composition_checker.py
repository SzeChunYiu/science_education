"""Composition quality checker using rule-of-thirds and visual balance analysis."""
import logging
import numpy as np
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class CompositionChecker:
    """Score image composition quality using structural heuristics.

    Checks:
        - Rule of thirds: brightness distribution across 3x3 grid
        - Visual balance: left/right brightness ratio (flag if outside 0.7-1.3)

    Returns average of both sub-scores.
    """

    def score(self, image) -> float:
        """Score image composition quality.

        Args:
            image: PIL Image, file path string, or Path object.

        Returns:
            Composition score in [0.0, 1.0] range.
        """
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        gray = np.array(image.convert("L"), dtype=np.float32)

        thirds_score = self._rule_of_thirds_score(gray)
        balance_score = self._visual_balance_score(gray)

        composite = (thirds_score + balance_score) / 2.0
        logger.debug(
            f"Composition: thirds={thirds_score:.3f}, "
            f"balance={balance_score:.3f}, composite={composite:.3f}"
        )
        return composite

    def _rule_of_thirds_score(self, gray: np.ndarray) -> float:
        """Score based on brightness distribution across a 3x3 grid.

        Good composition tends to have interesting content (higher contrast
        or brightness variation) near the thirds intersection points.
        A flat, uniform image scores lower.
        """
        h, w = gray.shape
        h_third, w_third = h // 3, w // 3

        # Split into 3x3 grid and compute mean brightness per cell
        cells = []
        for row in range(3):
            for col in range(3):
                r_start = row * h_third
                r_end = (row + 1) * h_third if row < 2 else h
                c_start = col * w_third
                c_end = (col + 1) * w_third if col < 2 else w
                cell = gray[r_start:r_end, c_start:c_end]
                cells.append(cell.mean())

        cells = np.array(cells)

        # Score based on variance across cells -- some variation indicates
        # compositional interest; very low variance means flat/boring
        variance = cells.var()
        # Normalize: typical variance for good composition is 200-2000
        # Map to 0-1 with a sigmoid-like curve
        score = 1.0 - np.exp(-variance / 500.0)

        # Bonus: check if intersection points (cells 0,2,6,8 corners
        # and 1,3,5,7 edges) have contrast with center (cell 4)
        center = cells[4]
        intersection_cells = [cells[i] for i in [0, 2, 6, 8]]
        intersection_contrast = np.mean(
            [abs(c - center) for c in intersection_cells]
        )
        contrast_bonus = min(0.2, intersection_contrast / 500.0)

        return min(1.0, score + contrast_bonus)

    def _visual_balance_score(self, gray: np.ndarray) -> float:
        """Score left-right brightness balance.

        Ratio outside 0.7-1.3 is penalized.
        """
        h, w = gray.shape
        mid = w // 2

        left_mean = gray[:, :mid].mean()
        right_mean = gray[:, mid:].mean()

        # Avoid division by zero
        if right_mean < 1e-6 and left_mean < 1e-6:
            return 1.0  # Both sides equally dark
        if right_mean < 1e-6:
            ratio = 2.0  # Extreme imbalance
        else:
            ratio = left_mean / right_mean

        # Perfect balance = ratio of 1.0
        # Acceptable range: 0.7 to 1.3
        if 0.7 <= ratio <= 1.3:
            # Within acceptable range: scale 0.7-1.0 based on closeness to 1.0
            deviation = abs(ratio - 1.0)
            return 1.0 - (deviation / 0.3) * 0.3  # Maps to 0.7-1.0
        else:
            # Outside acceptable range: penalize heavily
            deviation = min(abs(ratio - 0.7), abs(ratio - 1.3))
            return max(0.0, 0.7 - deviation)

    def unload(self):
        """No models to release, but provided for interface consistency."""
        pass
