"""Aesthetic quality scorer using LAION Aesthetic Predictor."""
import logging
import torch
import numpy as np
from pathlib import Path
from PIL import Image

logger = logging.getLogger(__name__)


class AestheticScorer:
    """Score image aesthetic quality 1-10 using CLIP + linear probe."""

    def __init__(self, device: str = None):
        if device is None:
            device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        self.device = device
        self._model = None
        self._clip_model = None
        self._preprocess = None

    def load(self):
        """Load CLIP + aesthetic predictor."""
        import clip
        self._clip_model, self._preprocess = clip.load("ViT-L/14", device=self.device)

        # Load aesthetic predictor linear head
        from aesthetic_predictor import AestheticPredictor
        self._model = AestheticPredictor()
        self._model.load_state_dict(
            torch.load(
                self._get_predictor_weights(),
                map_location=self.device,
            )
        )
        self._model.to(self.device).eval()

    def _get_predictor_weights(self) -> Path:
        """Download/locate aesthetic predictor weights."""
        from huggingface_hub import hf_hub_download
        return Path(hf_hub_download(
            "christophschuhmann/improved-aesthetic-predictor",
            "sac+logos+ava1-l14-linearMSE.pth",
        ))

    def score(self, image) -> float:
        """Score an image's aesthetic quality. Returns 1.0-10.0."""
        if self._model is None:
            self.load()

        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        img_tensor = self._preprocess(image).unsqueeze(0).to(self.device)

        with torch.no_grad():
            clip_features = self._clip_model.encode_image(img_tensor)
            clip_features = clip_features / clip_features.norm(dim=-1, keepdim=True)
            score = self._model(clip_features.float())

        return float(score.squeeze().cpu().numpy())

    def score_normalized(self, image, min_val: float = 1.0, max_val: float = 10.0) -> float:
        """Score normalized to 0.0-1.0 range."""
        raw = self.score(image)
        return max(0.0, min(1.0, (raw - min_val) / (max_val - min_val)))

    def unload(self):
        """Release model memory."""
        del self._model, self._clip_model
        self._model = self._clip_model = None
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
        elif torch.backends.mps.is_available():
            torch.mps.empty_cache()
