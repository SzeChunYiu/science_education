"""SDXL inference with LoRA on Apple MPS.

Manages model loading and unloading to stay within 16 GB unified memory.
Uses attention slicing and VAE slicing to reduce peak memory usage.
"""
import gc
import logging
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

logger = logging.getLogger(__name__)

_DEFAULT_BASE_MODEL = "stabilityai/stable-diffusion-xl-base-1.0"


class SDXLGenerator:
    """SDXL image generator optimised for Apple M-series (MPS backend).

    Typical usage::

        gen = SDXLGenerator(style_lora_path=Path("loras/teded_style.safetensors"))
        gen.load()
        img = gen.generate("teded_style, a friendly scientist", "blurry, dark")
        gen.unload()
    """

    def __init__(
        self,
        style_lora_path: Optional[Path] = None,
        device: str = "mps",
        base_model: str = _DEFAULT_BASE_MODEL,
    ) -> None:
        self.style_lora_path = Path(style_lora_path) if style_lora_path else None
        self.device = device
        self.base_model = base_model
        self._pipe = None
        self._active_character_lora: Optional[str] = None

    # ------------------------------------------------------------------
    # Model lifecycle
    # ------------------------------------------------------------------

    def load(self) -> None:
        """Load SDXL base pipeline and optional style LoRA.

        Enables attention slicing and VAE slicing to keep peak VRAM
        usage within the 16 GB budget of an M4 Mac mini.
        """
        if self._pipe is not None:
            logger.info("Pipeline already loaded — skipping.")
            return

        from diffusers import StableDiffusionXLPipeline

        logger.info("Loading SDXL base from %s ...", self.base_model)
        self._pipe = StableDiffusionXLPipeline.from_pretrained(
            self.base_model,
            torch_dtype=torch.float16,
            variant="fp16",
            use_safetensors=True,
        )

        # Memory optimisations
        self._pipe.enable_attention_slicing()
        self._pipe.enable_vae_slicing()

        # Load style LoRA if provided
        if self.style_lora_path and self.style_lora_path.exists():
            logger.info("Loading style LoRA from %s", self.style_lora_path)
            self._pipe.load_lora_weights(
                str(self.style_lora_path.parent),
                weight_name=self.style_lora_path.name,
            )

        self._pipe = self._pipe.to(self.device)
        logger.info("SDXL pipeline ready on %s", self.device)

    def load_character_lora(
        self,
        character_name: str,
        lora_dir: Path,
    ) -> None:
        """Load an additional character-specific LoRA.

        If a different character LoRA is already active it will be
        unloaded first to avoid weight contamination.

        Args:
            character_name: Human-readable character identifier.
            lora_dir: Directory containing ``<character_name>.safetensors``.
        """
        if self._pipe is None:
            raise RuntimeError("Pipeline not loaded. Call load() first.")

        lora_file = Path(lora_dir) / f"{character_name}.safetensors"
        if not lora_file.exists():
            logger.warning(
                "Character LoRA not found at %s — skipping.", lora_file
            )
            return

        # Unload previous character LoRA if different
        if self._active_character_lora and self._active_character_lora != character_name:
            logger.info(
                "Unloading previous character LoRA (%s)",
                self._active_character_lora,
            )
            self._pipe.unload_lora_weights()
            # Re-load style LoRA (unload removes all)
            if self.style_lora_path and self.style_lora_path.exists():
                self._pipe.load_lora_weights(
                    str(self.style_lora_path.parent),
                    weight_name=self.style_lora_path.name,
                )

        logger.info("Loading character LoRA: %s", character_name)
        self._pipe.load_lora_weights(
            str(lora_file.parent),
            weight_name=lora_file.name,
        )
        self._active_character_lora = character_name

    def unload(self) -> None:
        """Free GPU memory occupied by the pipeline."""
        if self._pipe is not None:
            del self._pipe
            self._pipe = None
            self._active_character_lora = None

        gc.collect()

        if torch.backends.mps.is_available():
            torch.mps.empty_cache()

        logger.info("SDXL pipeline unloaded — MPS cache cleared.")

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate(
        self,
        prompt: str,
        negative_prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 25,
        guidance_scale: float = 7.5,
        seed: Optional[int] = None,
    ) -> Image.Image:
        """Generate a single image from the given prompts.

        Args:
            prompt: Positive text prompt.
            negative_prompt: Negative text prompt.
            width: Output width in pixels (must be multiple of 8).
            height: Output height in pixels (must be multiple of 8).
            steps: Number of denoising steps.
            guidance_scale: Classifier-free guidance scale.
            seed: Optional reproducibility seed.

        Returns:
            A PIL Image.
        """
        if self._pipe is None:
            raise RuntimeError("Pipeline not loaded. Call load() first.")

        generator = None
        if seed is not None:
            # MPS generator must live on CPU for deterministic seeding
            generator = torch.Generator("cpu").manual_seed(seed)

        logger.info(
            "Generating %dx%d  steps=%d  cfg=%.1f  seed=%s",
            width,
            height,
            steps,
            guidance_scale,
            seed,
        )

        result = self._pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )

        image = result.images[0]
        logger.debug("Generation complete.")
        return image

    def generate_candidates(
        self,
        prompt: str,
        negative_prompt: str,
        n: int = 4,
        **kwargs,
    ) -> list[Image.Image]:
        """Generate *n* candidate images with different random seeds.

        Any extra *kwargs* are forwarded to :meth:`generate`.

        Returns:
            List of PIL Images.
        """
        import random

        base_seed = kwargs.pop("seed", None)
        if base_seed is None:
            base_seed = random.randint(0, 2**32 - 1)

        candidates: list[Image.Image] = []
        for i in range(n):
            seed = base_seed + i
            img = self.generate(
                prompt=prompt,
                negative_prompt=negative_prompt,
                seed=seed,
                **kwargs,
            )
            candidates.append(img)

        logger.info("Generated %d candidates (seeds %d..%d)", n, base_seed, base_seed + n - 1)
        return candidates
