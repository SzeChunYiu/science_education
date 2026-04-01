"""Style consistency checker using CLIP embedding centroid tracking."""
import logging
import torch
import numpy as np
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)

# Minimum accepted scenes before centroid is stable enough to score
MIN_SCENES_FOR_SCORING = 3


class StyleConsistencyChecker:
    """Maintain a running CLIP embedding centroid per episode.

    Scores new images by cosine similarity to the centroid.
    Skips scoring until at least MIN_SCENES_FOR_SCORING scenes
    have been accepted (centroid not yet stable).
    """

    def __init__(self, device: str = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self._clip_model = None
        self._preprocess = None
        self._embeddings: list[np.ndarray] = []
        self._centroid: np.ndarray | None = None

    def load(self):
        """Load CLIP ViT-B/32 model."""
        import clip
        self._clip_model, self._preprocess = clip.load(
            "ViT-B/32", device=self.device
        )

    def _get_embedding(self, image) -> np.ndarray:
        """Extract normalized CLIP embedding for an image."""
        if self._clip_model is None:
            self.load()

        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        img_tensor = self._preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            features = self._clip_model.encode_image(img_tensor)
            features = features / features.norm(dim=-1, keepdim=True)

        return features.squeeze().cpu().numpy()

    def _update_centroid(self):
        """Recompute centroid from all accepted embeddings."""
        if self._embeddings:
            stacked = np.stack(self._embeddings)
            centroid = stacked.mean(axis=0)
            # Normalize centroid
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            self._centroid = centroid

    def add_accepted_scene(self, image):
        """Add an accepted scene image to the centroid tracker.

        Args:
            image: PIL Image, file path string, or Path object.
        """
        embedding = self._get_embedding(image)
        self._embeddings.append(embedding)
        self._update_centroid()
        logger.debug(
            f"Added scene to centroid tracker "
            f"({len(self._embeddings)} total scenes)"
        )

    def score(self, image) -> float:
        """Score image style consistency against episode centroid.

        Args:
            image: PIL Image, file path string, or Path object.

        Returns:
            Cosine similarity to centroid [0.0, 1.0].
            Returns 1.0 if fewer than MIN_SCENES_FOR_SCORING scenes
            have been accepted (centroid not stable, auto-pass).
        """
        if len(self._embeddings) < MIN_SCENES_FOR_SCORING:
            logger.debug(
                f"Only {len(self._embeddings)} scenes accepted, "
                f"need {MIN_SCENES_FOR_SCORING} for stable centroid. "
                f"Auto-passing."
            )
            return 1.0

        embedding = self._get_embedding(image)
        similarity = float(np.dot(embedding, self._centroid))
        return max(0.0, min(1.0, similarity))

    def reset(self):
        """Clear all embeddings and centroid for a new episode."""
        self._embeddings.clear()
        self._centroid = None
        logger.debug("Style consistency checker reset")

    @property
    def scene_count(self) -> int:
        """Number of accepted scenes in the centroid."""
        return len(self._embeddings)

    def unload(self):
        """Release model memory."""
        del self._clip_model
        self._clip_model = None
        self._preprocess = None
        self._embeddings.clear()
        self._centroid = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif torch.backends.mps.is_available():
            torch.mps.empty_cache()
