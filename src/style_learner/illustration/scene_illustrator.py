"""High-level orchestrator for per-scene illustration generation.

Combines prompt building, SDXL generation, quality scoring, and
consistency tracking into a single ``illustrate_episode`` entry point.
"""
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from .consistency_memory import ConsistencyMemory
from .prompt_builder import build_scene_prompt, build_title_card_prompt
from .sdxl_generator import SDXLGenerator

logger = logging.getLogger(__name__)


class SceneIllustrator:
    """Generates and selects illustrations for every scene in an episode.

    Workflow per scene:
        1. Build prompt via :mod:`prompt_builder`.
        2. Generate N candidates via :class:`SDXLGenerator`.
        3. Score with the external *quality_orchestrator*.
        4. Accept the best passing candidate.
        5. Update :class:`ConsistencyMemory` with the accepted image.
        6. Save the accepted illustration to *output_dir*.

    Args:
        style_lora_path: Path to the style LoRA weights file.
        quality_orchestrator: Object with a ``score(image, scene_data) -> dict``
            method that returns ``{"pass": bool, "score": float, ...}``.
        device: Torch device string (default ``"mps"``).
        candidates_per_scene: Number of candidate images per scene.
        character_lora_dir: Optional directory holding per-character LoRAs.
    """

    def __init__(
        self,
        style_lora_path: Optional[Path] = None,
        quality_orchestrator=None,
        device: str = "mps",
        candidates_per_scene: int = 4,
        character_lora_dir: Optional[Path] = None,
    ) -> None:
        self.style_lora_path = Path(style_lora_path) if style_lora_path else None
        self.quality_orchestrator = quality_orchestrator
        self.device = device
        self.candidates_per_scene = candidates_per_scene
        self.character_lora_dir = Path(character_lora_dir) if character_lora_dir else None

        # Lazy-loaded generator
        self._generator: Optional[SDXLGenerator] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def illustrate_episode(
        self,
        production_plan: dict,
        output_dir: Path,
    ) -> list[Path]:
        """Generate illustrations for every scene in *production_plan*.

        Args:
            production_plan: Full episode production plan with keys:
                ``episode_id``, ``palette``, ``character_descriptions``,
                ``scenes`` (list of scene dicts).
            output_dir: Directory to write accepted PNGs into.

        Returns:
            List of :class:`Path` objects pointing to the saved images,
            one per scene (in scene order).
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        episode_id = production_plan.get("episode_id", "unknown")
        palette = production_plan.get("palette", [])
        char_descs = production_plan.get("character_descriptions", {})
        scenes = production_plan.get("scenes", [])

        logger.info(
            "Illustrating episode %s — %d scenes", episode_id, len(scenes)
        )

        memory = ConsistencyMemory(episode_id)
        self._ensure_generator_loaded()

        saved_paths: list[Path] = []

        for idx, scene in enumerate(scenes):
            scene_id = idx + 1
            logger.info(
                "--- Scene %d / %d  type=%s ---",
                scene_id,
                len(scenes),
                scene.get("scene_type", "?"),
            )

            # Load character LoRA if needed
            self._maybe_load_character_lora(scene)

            # 1. Build prompt
            positive, negative = build_scene_prompt(
                scene=scene,
                episode_palette=palette,
                character_descriptions=char_descs,
                consistency_anchors=memory.get_anchors(),
            )
            logger.debug("Prompt: %s", positive[:200])

            # 2. Generate candidates
            candidates = self._generator.generate_candidates(
                prompt=positive,
                negative_prompt=negative,
                n=self.candidates_per_scene,
            )

            # 3. Score and select best
            best_image = self._select_best(candidates, scene)

            # 4. Update consistency memory
            memory.update(scene_id, best_image, scene)

            # 5. Save
            filename = f"scene_{scene_id:03d}.png"
            save_path = output_dir / filename
            best_image.save(save_path)
            saved_paths.append(save_path)
            logger.info("Saved %s", save_path)

        # Persist consistency memory alongside illustrations
        memory_path = output_dir / "consistency_memory.json"
        memory.save(memory_path)

        logger.info(
            "Episode %s illustration complete — %d images saved to %s",
            episode_id,
            len(saved_paths),
            output_dir,
        )
        return saved_paths

    def unload(self) -> None:
        """Release GPU memory held by the internal generator."""
        if self._generator is not None:
            self._generator.unload()
            self._generator = None
            logger.info("SceneIllustrator generator unloaded.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _ensure_generator_loaded(self) -> None:
        """Lazy-load the SDXL generator on first use."""
        if self._generator is None:
            self._generator = SDXLGenerator(
                style_lora_path=self.style_lora_path,
                device=self.device,
            )
            self._generator.load()

    def _maybe_load_character_lora(self, scene: dict) -> None:
        """Load the character LoRA for *scene* when available."""
        if self.character_lora_dir is None or self._generator is None:
            return
        character = scene.get("character", {})
        char_name = character.get("name", "")
        if char_name:
            self._generator.load_character_lora(
                char_name, self.character_lora_dir
            )

    def _select_best(
        self,
        candidates: list[Image.Image],
        scene: dict,
    ) -> Image.Image:
        """Score *candidates* and return the best passing one.

        If no quality orchestrator is configured, the first candidate is
        returned. If none of the candidates pass quality checks, the
        highest-scoring candidate is returned with a warning.
        """
        if self.quality_orchestrator is None:
            logger.debug("No quality orchestrator — returning first candidate.")
            return candidates[0]

        scored: list[tuple[float, bool, Image.Image]] = []
        for i, img in enumerate(candidates):
            result = self.quality_orchestrator.score(img, scene)
            score = result.get("score", 0.0)
            passed = result.get("pass", False)
            scored.append((score, passed, img))
            logger.debug(
                "Candidate %d: score=%.3f  pass=%s", i, score, passed
            )

        # Prefer passing candidates; among those pick highest score
        passing = [(s, img) for s, p, img in scored if p]
        if passing:
            passing.sort(key=lambda x: x[0], reverse=True)
            logger.info("Best passing candidate: score=%.3f", passing[0][0])
            return passing[0][1]

        # Fallback: highest score even if it didn't pass
        scored.sort(key=lambda x: x[0], reverse=True)
        logger.warning(
            "No candidate passed quality check — using best score %.3f",
            scored[0][0],
        )
        return scored[0][2]
