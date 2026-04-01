"""Semantic alignment scorer using CLIP cosine similarity."""
import logging
import torch
import numpy as np
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class SemanticAligner:
    """Score image-text alignment via CLIP cosine similarity.

    Thresholds:
        >= 0.22 for scene images
        >= 0.25 for title cards
    """

    def __init__(self, device: str = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self._clip_model = None
        self._preprocess = None
        self._tokenize = None

    def load(self):
        """Load CLIP ViT-B/32 model."""
        import clip
        self._clip_model, self._preprocess = clip.load(
            "ViT-B/32", device=self.device
        )
        self._tokenize = clip.tokenize

    def score(self, image, text: str = "") -> float:
        """Score cosine similarity between image and text prompt.

        Args:
            image: PIL Image, file path string, or Path object.
            text: Text prompt to compare against.

        Returns:
            Cosine similarity in [0.0, 1.0] range.
        """
        if self._clip_model is None:
            self.load()

        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        img_tensor = self._preprocess(image).unsqueeze(0).to(self.device)
        text_tokens = self._tokenize([text]).to(self.device)

        with torch.no_grad():
            img_features = self._clip_model.encode_image(img_tensor)
            txt_features = self._clip_model.encode_text(text_tokens)

            # Normalize
            img_features = img_features / img_features.norm(dim=-1, keepdim=True)
            txt_features = txt_features / txt_features.norm(dim=-1, keepdim=True)

            similarity = (img_features @ txt_features.T).squeeze()

        return float(similarity.cpu().numpy())

    def score_scene(self, image, text: str, threshold: float = 0.22) -> dict:
        """Score a scene image with pass/fail against scene threshold.

        Returns:
            dict with 'score', 'passed', 'threshold' keys.
        """
        s = self.score(image, text)
        return {"score": s, "passed": s >= threshold, "threshold": threshold}

    def score_title(self, image, text: str, threshold: float = 0.25) -> dict:
        """Score a title card image with pass/fail against title threshold.

        Returns:
            dict with 'score', 'passed', 'threshold' keys.
        """
        s = self.score(image, text)
        return {"score": s, "passed": s >= threshold, "threshold": threshold}

    def unload(self):
        """Release model memory."""
        del self._clip_model
        self._clip_model = None
        self._preprocess = None
        self._tokenize = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif torch.backends.mps.is_available():
            torch.mps.empty_cache()
