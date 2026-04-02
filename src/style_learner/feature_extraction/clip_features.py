"""CLIP feature extraction for keyframe embeddings and zero-shot scene classification.

Uses openai/clip-vit-base-patch32 from HuggingFace transformers to compute
512-dimensional embeddings for images and text, and classify keyframes into
TED-Ed scene types via zero-shot classification.
"""

import json
import logging
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# TED-Ed scene type prompts for zero-shot classification
SCENE_TYPES = [
    "close-up of an illustrated object on a coloured background",
    "wide scene with multiple illustrated characters or figures",
    "historical map or geographic illustration",
    "scientific diagram, chart, or graph",
    "microscopic or cellular level visualization",
    "horizontal timeline of historical events",
    "large text title card with minimal illustration",
    "abstract decorative pattern or transition frame",
]


def _select_device(requested: str = "cuda") -> str:
    """Select best available device: CUDA > MPS > CPU."""
    import torch

    if requested == "cuda" and torch.cuda.is_available():
        logger.info("Using CUDA device")
        return "cuda"
    if requested == "mps" or (
        requested == "cuda" and hasattr(torch.backends, "mps") and torch.backends.mps.is_available()
    ):
        logger.info("Using MPS device")
        return "mps"
    logger.info("Falling back to CPU device")
    return "cpu"


class CLIPFeatureExtractor:
    """Extracts CLIP embeddings and performs zero-shot scene classification."""

    def __init__(self, device: str = "cuda") -> None:
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self.device = _select_device(device)
        self._torch = torch

        model_name = "openai/clip-vit-base-patch32"
        logger.info("Loading CLIP model: %s", model_name)
        self.model = CLIPModel.from_pretrained(model_name).to(self.device)
        self.model.eval()
        self.processor = CLIPProcessor.from_pretrained(model_name)

        # Pre-compute scene type text embeddings for zero-shot classification
        self._scene_type_embeddings = self._precompute_scene_embeddings()

    def _extract_features(self, result, projection):
        """Extract tensor from model output, handling API changes."""
        if isinstance(result, self._torch.Tensor):
            return result
        # Newer transformers returns BaseModelOutputWithPooling
        pooled = result.pooler_output
        # Only project if dimensions don't match (not already projected)
        if pooled.shape[-1] != projection.out_features:
            return projection(pooled)
        return pooled

    def _get_text_features(self, texts: list[str]):
        """Extract text features, handling transformers API changes."""
        inputs = self.processor(text=texts, return_tensors="pt", padding=True)
        text_inputs = {k: v.to(self.device) for k, v in inputs.items() if k in ("input_ids", "attention_mask")}
        result = self.model.get_text_features(**text_inputs)
        return self._extract_features(result, self.model.text_projection)

    def _get_image_features(self, pixel_values):
        """Extract image features, handling transformers API changes."""
        result = self.model.get_image_features(pixel_values=pixel_values)
        return self._extract_features(result, self.model.visual_projection)

    def _precompute_scene_embeddings(self) -> np.ndarray:
        """Pre-compute normalized text embeddings for all scene types."""
        with self._torch.no_grad():
            text_features = self._get_text_features(SCENE_TYPES)
            text_features = text_features / text_features.norm(dim=-1, keepdim=True)
        return text_features.cpu().numpy().astype(np.float32)

    def embed_image(self, image_path: Path) -> np.ndarray:
        """Compute 512-dim float32 CLIP embedding for an image.

        Args:
            image_path: Path to the image file.

        Returns:
            Normalized 512-dimensional float32 numpy array.
        """
        from PIL import Image

        image = Image.open(image_path).convert("RGB")
        with self._torch.no_grad():
            inputs = self.processor(images=image, return_tensors="pt")
            pixel_values = inputs["pixel_values"].to(self.device)
            features = self._get_image_features(pixel_values)
            features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().astype(np.float32).squeeze(0)

    def embed_text(self, text: str) -> np.ndarray:
        """Compute 512-dim float32 CLIP embedding for a text string.

        Args:
            text: Input text string.

        Returns:
            Normalized 512-dimensional float32 numpy array.
        """
        with self._torch.no_grad():
            features = self._get_text_features([text])
            features = features / features.norm(dim=-1, keepdim=True)
        return features.cpu().numpy().astype(np.float32).squeeze(0)

    def classify_scene_type(self, image_path: Path) -> dict:
        """Zero-shot classify an image against TED-Ed scene types.

        Args:
            image_path: Path to the keyframe image.

        Returns:
            Dict with 'top' (best label), 'top_score' (float), and
            'scores' (dict mapping each scene type to its similarity score).
        """
        image_embedding = self.embed_image(image_path)
        similarities = image_embedding @ self._scene_type_embeddings.T
        scores = {label: float(sim) for label, sim in zip(SCENE_TYPES, similarities)}
        top_label = max(scores, key=scores.get)
        return {
            "top": top_label,
            "top_score": scores[top_label],
            "scores": scores,
        }

    def embed_images_batch(self, image_paths: list[Path], batch_size: int = 16) -> list[np.ndarray]:
        """Batch-embed multiple images to avoid OOM on large datasets.

        Args:
            image_paths: List of image file paths.
            batch_size: Number of images per forward pass.

        Returns:
            List of 512-dim float32 numpy arrays, one per image.
        """
        from PIL import Image

        all_embeddings = []
        for i in range(0, len(image_paths), batch_size):
            batch_paths = image_paths[i : i + batch_size]
            images = [Image.open(p).convert("RGB") for p in batch_paths]
            with self._torch.no_grad():
                inputs = self.processor(images=images, return_tensors="pt", padding=True)
                pixel_values = inputs["pixel_values"].to(self.device)
                features = self._get_image_features(pixel_values)
                features = features / features.norm(dim=-1, keepdim=True)
            embeddings = features.cpu().numpy().astype(np.float32)
            for j in range(embeddings.shape[0]):
                all_embeddings.append(embeddings[j])
            logger.debug(
                "Embedded batch %d-%d / %d",
                i,
                min(i + batch_size, len(image_paths)),
                len(image_paths),
            )
        return all_embeddings

    def extract_for_video(self, video_dir: Path) -> None:
        """Process all keyframes in a video directory, save features.json.

        Expects keyframes in video_dir/frames/ as image files.
        Saves video_dir/features.json with per-frame embeddings and scene classifications.

        Args:
            video_dir: Path to the video data directory containing frames/.
        """
        frames_dir = video_dir / "frames"
        if not frames_dir.exists():
            logger.warning("No frames/ directory found in %s, skipping", video_dir)
            return

        frame_paths = sorted(
            p for p in frames_dir.iterdir()
            if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}
        )
        if not frame_paths:
            logger.warning("No image files found in %s", frames_dir)
            return

        logger.info("Extracting CLIP features for %d frames in %s", len(frame_paths), video_dir.name)

        # Batch embed all frames
        embeddings = self.embed_images_batch(frame_paths)

        # Classify each frame
        features = []
        for path, embedding in zip(frame_paths, embeddings):
            similarities = embedding @ self._scene_type_embeddings.T
            scores = {label: float(sim) for label, sim in zip(SCENE_TYPES, similarities)}
            top_label = max(scores, key=scores.get)
            features.append({
                "frame": path.name,
                "embedding": embedding.tolist(),
                "scene_type": {
                    "top": top_label,
                    "top_score": scores[top_label],
                    "scores": scores,
                },
            })

        output_path = video_dir / "features.json"
        with open(output_path, "w") as f:
            json.dump(features, f, indent=2)
        logger.info("Saved features for %d frames to %s", len(features), output_path)
