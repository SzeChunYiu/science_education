"""Local discriminator inference for quality scoring.

Loads trained style, semantic, and flow discriminator checkpoints and
provides a unified scoring interface for the episode assembly pipeline.

If checkpoints do not exist yet (models not trained), all scores default
to 1.0 (pass) with a warning logged.
"""
import logging
from pathlib import Path
from typing import Union

from PIL import Image

logger = logging.getLogger(__name__)


class DiscriminatorScorer:
    """Unified scorer that loads and runs all three discriminators.

    Args:
        models_dir: Directory containing discriminator checkpoints.
            Expected structure:
                models_dir/style_discriminator.pt
                models_dir/semantic_discriminator.pt
                models_dir/flow_discriminator.pt
        device: Torch device string (default "cpu" -- discriminators
                are lightweight MLPs, CPU is fast enough).
    """

    def __init__(
        self,
        models_dir: Path = Path("models/discriminators"),
        device: str = "cpu",
    ):
        self.models_dir = Path(models_dir)
        self.device = device
        self._style = None
        self._semantic = None
        self._flow = None
        self._loaded = False

    def load_all(self):
        """Load all three discriminator checkpoints."""
        style_ckpt = self.models_dir / "style_discriminator.pt"
        semantic_ckpt = self.models_dir / "semantic_discriminator.pt"
        flow_ckpt = self.models_dir / "flow_discriminator.pt"

        # Style discriminator
        if style_ckpt.exists():
            try:
                from src.quality.discriminators.style_discriminator import (
                    StyleDiscriminator,
                )
                self._style = StyleDiscriminator(
                    checkpoint_path=style_ckpt, device=self.device
                )
                logger.info(f"Loaded style discriminator: {style_ckpt}")
            except Exception as e:
                logger.warning(f"Failed to load style discriminator: {e}")
        else:
            logger.warning(
                f"Style discriminator checkpoint not found: {style_ckpt}. "
                f"Scores will default to 1.0."
            )

        # Semantic discriminator
        if semantic_ckpt.exists():
            try:
                from src.quality.discriminators.semantic_discriminator import (
                    SemanticDiscriminator,
                )
                self._semantic = SemanticDiscriminator(
                    checkpoint_path=semantic_ckpt, device=self.device
                )
                logger.info(f"Loaded semantic discriminator: {semantic_ckpt}")
            except Exception as e:
                logger.warning(f"Failed to load semantic discriminator: {e}")
        else:
            logger.warning(
                f"Semantic discriminator checkpoint not found: {semantic_ckpt}. "
                f"Scores will default to 1.0."
            )

        # Flow discriminator
        if flow_ckpt.exists():
            try:
                from src.quality.discriminators.flow_discriminator import (
                    FlowDiscriminator,
                )
                self._flow = FlowDiscriminator(
                    checkpoint_path=flow_ckpt, device=self.device
                )
                logger.info(f"Loaded flow discriminator: {flow_ckpt}")
            except Exception as e:
                logger.warning(f"Failed to load flow discriminator: {e}")
        else:
            logger.warning(
                f"Flow discriminator checkpoint not found: {flow_ckpt}. "
                f"Scores will default to 1.0."
            )

        self._loaded = True

    def score_style(self, image: Union[Image.Image, Path, str]) -> float:
        """Score an image for TED-Ed art style conformance.

        Args:
            image: PIL Image or path to image file.

        Returns:
            Style score 0.0-1.0 (higher = more style-conformant).
        """
        if self._style is None:
            return 1.0

        try:
            return float(self._style.score(image))
        except Exception as e:
            logger.warning(f"Style scoring failed: {e}")
            return 1.0

    def score_semantic(
        self,
        image: Union[Image.Image, Path, str],
        narration: str,
    ) -> float:
        """Score image-narration semantic alignment.

        Args:
            image: PIL Image or path to image file.
            narration: Narration text that should match the image.

        Returns:
            Semantic match score 0.0-1.0 (higher = better match).
        """
        if self._semantic is None:
            return 1.0

        try:
            return float(self._semantic.score(image, narration))
        except Exception as e:
            logger.warning(f"Semantic scoring failed: {e}")
            return 1.0

    def score_flow(
        self,
        frame_a: Union[Image.Image, Path, str],
        frame_b: Union[Image.Image, Path, str],
        transition_type: str = "cut",
    ) -> float:
        """Score narrative flow coherence between consecutive scenes.

        Args:
            frame_a: First frame (PIL Image or path).
            frame_b: Second frame (PIL Image or path).
            transition_type: One of "cut", "dissolve", "fade".

        Returns:
            Flow coherence score 0.0-1.0 (higher = smoother flow).
        """
        if self._flow is None:
            return 1.0

        try:
            return float(self._flow.score(frame_a, frame_b, transition_type))
        except Exception as e:
            logger.warning(f"Flow scoring failed: {e}")
            return 1.0

    def check_episode_flow(
        self,
        scene_frames: list[Union[Image.Image, Path, str]],
        transitions: list[str],
    ) -> list[dict]:
        """Check flow coherence across all consecutive scene pairs.

        Args:
            scene_frames: List of frame images (one per scene).
            transitions: List of transition types between scenes.
                         Length should be len(scene_frames) - 1.

        Returns:
            List of dicts with keys: pair, score, transition, passed.
        """
        results = []

        if len(scene_frames) < 2:
            return results

        # Pad transitions if needed
        while len(transitions) < len(scene_frames) - 1:
            transitions.append("cut")

        for i in range(len(scene_frames) - 1):
            score = self.score_flow(
                scene_frames[i], scene_frames[i + 1], transitions[i]
            )
            results.append({
                "pair": f"scene_{i:03d}->scene_{i+1:03d}",
                "score": round(score, 3),
                "transition": transitions[i],
                "passed": score >= 0.6,
            })

        avg_score = (
            sum(r["score"] for r in results) / len(results) if results else 0
        )
        logger.info(
            f"Episode flow check: {len(results)} pairs, "
            f"avg score={avg_score:.3f}"
        )

        return results

    def unload(self):
        """Free all discriminator models."""
        self._style = None
        self._semantic = None
        self._flow = None
        self._loaded = False

        try:
            import torch
            if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                torch.mps.empty_cache()
        except ImportError:
            pass

        logger.info("Discriminator models unloaded")
