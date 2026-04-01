"""
Depth-based layer splitter for parallax animation.

Uses MiDaS depth estimation to split a single illustration into three
depth layers (foreground, midground, background) suitable for parallax
camera motion.  Each layer is returned as an RGBA image with an alpha
mask derived from the depth map.

The layers are slightly expanded (5%) beyond their mask boundaries to
prevent visible edge gaps during parallax motion.

Requirements
------------
- torch (MPS-aware for Apple Silicon)
- PIL / Pillow
- numpy
"""

from __future__ import annotations

import logging
from typing import Optional

import numpy as np
from PIL import Image, ImageFilter

logger = logging.getLogger(__name__)


class DepthSplitter:
    """
    Split an illustration into three depth layers using MiDaS.

    Parameters
    ----------
    device : str
        Torch device string.  ``"mps"`` for Apple Silicon, ``"cpu"`` for
        fallback.  CUDA is also supported but not expected in this project.
    """

    def __init__(self, device: str = "mps") -> None:
        self._device_name = device
        self._model = None
        self._transform = None
        self._loaded = False

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load MiDaS small model from torch.hub (lazy, idempotent)."""
        if self._loaded:
            return

        import torch

        # Validate device availability
        if self._device_name == "mps" and not torch.backends.mps.is_available():
            logger.warning("MPS not available, falling back to CPU")
            self._device_name = "cpu"

        device = torch.device(self._device_name)

        logger.info("Loading MiDaS small model from torch.hub ...")
        self._model = torch.hub.load(
            "intel-isl/MiDaS",
            "MiDaS_small",
            trust_repo=True,
        )
        self._model.to(device)
        self._model.eval()

        # Load the corresponding transform
        midas_transforms = torch.hub.load(
            "intel-isl/MiDaS",
            "transforms",
            trust_repo=True,
        )
        self._transform = midas_transforms.small_transform

        self._loaded = True
        logger.info("MiDaS model loaded on %s", self._device_name)

    def unload(self) -> None:
        """Free GPU memory by deleting the model."""
        if self._model is not None:
            del self._model
            self._model = None
        if self._transform is not None:
            del self._transform
            self._transform = None
        self._loaded = False

        # Attempt to reclaim MPS/CUDA memory
        try:
            import torch
            if self._device_name == "mps" and hasattr(torch.mps, "empty_cache"):
                torch.mps.empty_cache()
            elif self._device_name.startswith("cuda"):
                torch.cuda.empty_cache()
        except Exception:
            pass

        logger.info("MiDaS model unloaded")

    # ------------------------------------------------------------------
    # Depth estimation
    # ------------------------------------------------------------------

    def estimate_depth(self, image: Image.Image) -> np.ndarray:
        """
        Estimate a normalised depth map from a PIL image.

        Parameters
        ----------
        image : PIL.Image.Image
            Input illustration (any mode; converted to RGB internally).

        Returns
        -------
        np.ndarray
            Float32 array of shape (H, W) with values in [0, 1].
            Higher values = closer to camera (foreground).
        """
        import torch

        self.load()  # lazy load

        img_rgb = image.convert("RGB")
        img_np = np.array(img_rgb)

        # Apply MiDaS transform
        input_batch = self._transform(img_np).to(torch.device(self._device_name))

        with torch.no_grad():
            prediction = self._model(input_batch)

            # Resize to original image dimensions
            prediction = torch.nn.functional.interpolate(
                prediction.unsqueeze(1),
                size=img_np.shape[:2],
                mode="bicubic",
                align_corners=False,
            ).squeeze()

        depth = prediction.cpu().numpy()

        # Normalise to [0, 1] — higher = closer (foreground)
        d_min = depth.min()
        d_max = depth.max()
        if d_max - d_min > 1e-6:
            depth = (depth - d_min) / (d_max - d_min)
        else:
            depth = np.zeros_like(depth)

        return depth.astype(np.float32)

    # ------------------------------------------------------------------
    # Layer splitting
    # ------------------------------------------------------------------

    def split_layers(
        self,
        image: Image.Image,
        depth: np.ndarray,
        fg_threshold: float = 0.6,
        bg_threshold: float = 0.3,
    ) -> tuple[Image.Image, Image.Image, Image.Image]:
        """
        Split an image into three RGBA layers based on depth thresholds.

        Parameters
        ----------
        image : PIL.Image.Image
            Original illustration.
        depth : np.ndarray
            Normalised depth map from ``estimate_depth()``.
        fg_threshold : float
            Minimum depth value for foreground (default 0.6).
        bg_threshold : float
            Maximum depth value for background (default 0.3).

        Returns
        -------
        tuple[PIL.Image, PIL.Image, PIL.Image]
            (foreground, midground, background) as RGBA images.
            Each layer has an alpha channel derived from its depth mask.
            Layers are expanded 5% beyond mask boundaries to prevent
            edge gaps during parallax motion.
        """
        img_rgba = image.convert("RGBA")
        h, w = depth.shape

        # Create binary masks for each layer
        fg_mask = (depth >= fg_threshold).astype(np.uint8) * 255
        bg_mask = (depth <= bg_threshold).astype(np.uint8) * 255
        mid_mask = (
            (depth > bg_threshold) & (depth < fg_threshold)
        ).astype(np.uint8) * 255

        # Expand masks slightly (5% dilation) to prevent edge gaps
        expand_radius = max(1, int(min(w, h) * 0.05))

        fg_layer = self._apply_mask(img_rgba, fg_mask, expand_radius)
        mid_layer = self._apply_mask(img_rgba, mid_mask, expand_radius)
        bg_layer = self._apply_mask(img_rgba, bg_mask, expand_radius)

        return fg_layer, mid_layer, bg_layer

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _apply_mask(
        image: Image.Image,
        mask: np.ndarray,
        expand_radius: int,
    ) -> Image.Image:
        """
        Apply a binary mask as the alpha channel of an RGBA image,
        with slight dilation to prevent edge gaps.
        """
        # Convert mask to PIL and dilate
        mask_img = Image.fromarray(mask, mode="L")

        # Dilate by applying MaxFilter (expands white regions)
        if expand_radius > 0:
            # MaxFilter kernel size must be odd
            kernel_size = expand_radius * 2 + 1
            # PIL MaxFilter max kernel is limited; apply iteratively for large radii
            remaining = expand_radius
            expanded = mask_img
            while remaining > 0:
                k = min(remaining * 2 + 1, 9)  # max kernel 9
                expanded = expanded.filter(ImageFilter.MaxFilter(k))
                remaining -= (k - 1) // 2
            mask_img = expanded

        # Slight Gaussian blur on the mask edges for smoother blending
        mask_img = mask_img.filter(ImageFilter.GaussianBlur(radius=1))

        # Apply mask as alpha channel
        result = image.copy()
        result.putalpha(mask_img)

        return result
