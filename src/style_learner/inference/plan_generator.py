"""Generate production_plan.json from a parsed script using style models.

Runs all four trained MLP models (scene classifier, camera predictor,
text placement, transition predictor) over each scene in a parsed script
to produce a complete production plan.  If models are not yet trained,
sensible defaults are used.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import numpy as np

logger = logging.getLogger(__name__)

# Default values when models are unavailable
_DEFAULT_SCENE_TYPE = "wide scene with characters"
_DEFAULT_CAMERA_MOTION = "static"
_DEFAULT_CAMERA_MAGNITUDE = 0.3
_DEFAULT_TRANSITION_TYPE = "cut"
_DEFAULT_TRANSITION_DURATION = 0.0
_DEFAULT_TEXT_X = 0.5
_DEFAULT_TEXT_Y = 0.2
_DEFAULT_FONT_SIZE_RATIO = 0.04
_DEFAULT_ANIMATION = "fade_in"


class ProductionPlanGenerator:
    """Generate a production plan dict from a parsed script.

    Uses four MLP models to predict per-scene style decisions:
        1. SceneClassifierMLP  — scene type from CLIP embedding
        2. CameraMotionMLP     — camera motion from sentence embedding + scene type
        3. TextPlacementMLP    — text position/size/animation
        4. TransitionMLP       — transition type/duration between consecutive scenes

    If any model checkpoint is missing, that model's predictions fall back
    to sensible defaults.

    Args:
        models_dir: Directory containing model checkpoint files.
        device: Torch device ("cpu", "mps", "cuda").
    """

    def __init__(
        self,
        models_dir: Path = Path("models/style_learner"),
        device: str = "cpu",
    ):
        self.models_dir = Path(models_dir)
        self.device = device
        self._scene_classifier = None
        self._camera_predictor = None
        self._text_placement = None
        self._transition_predictor = None
        self._models_loaded = False

    def load_models(self) -> None:
        """Load all four MLP models from checkpoints.

        Missing checkpoints are logged as warnings; those models
        will use defaults during plan generation.
        """
        try:
            import torch
        except ImportError:
            logger.warning("PyTorch not available — all models will use defaults")
            self._models_loaded = True
            return

        # Scene classifier
        ckpt = self.models_dir / "scene_classifier.pt"
        if ckpt.exists():
            try:
                from src.style_learner.training.scene_classifier import SceneClassifierMLP
                self._scene_classifier = SceneClassifierMLP()
                self._scene_classifier.load_state_dict(
                    torch.load(ckpt, map_location=self.device, weights_only=True)
                )
                self._scene_classifier.eval()
                logger.info("Loaded scene_classifier from %s", ckpt)
            except Exception as e:
                logger.warning("Failed to load scene_classifier: %s", e)
        else:
            logger.info("No scene_classifier checkpoint at %s — using defaults", ckpt)

        # Camera predictor
        ckpt = self.models_dir / "camera_predictor.pt"
        if ckpt.exists():
            try:
                from src.style_learner.training.camera_predictor import CameraMotionMLP
                self._camera_predictor = CameraMotionMLP()
                self._camera_predictor.load_state_dict(
                    torch.load(ckpt, map_location=self.device, weights_only=True)
                )
                self._camera_predictor.eval()
                logger.info("Loaded camera_predictor from %s", ckpt)
            except Exception as e:
                logger.warning("Failed to load camera_predictor: %s", e)
        else:
            logger.info("No camera_predictor checkpoint at %s — using defaults", ckpt)

        # Text placement
        ckpt = self.models_dir / "text_placement.pt"
        if ckpt.exists():
            try:
                from src.style_learner.training.text_placement import TextPlacementMLP
                self._text_placement = TextPlacementMLP()
                self._text_placement.load_state_dict(
                    torch.load(ckpt, map_location=self.device, weights_only=True)
                )
                self._text_placement.eval()
                logger.info("Loaded text_placement from %s", ckpt)
            except Exception as e:
                logger.warning("Failed to load text_placement: %s", e)
        else:
            logger.info("No text_placement checkpoint at %s — using defaults", ckpt)

        # Transition predictor
        ckpt = self.models_dir / "transition_predictor.pt"
        if ckpt.exists():
            try:
                from src.style_learner.training.transition_predictor import TransitionMLP
                self._transition_predictor = TransitionMLP()
                self._transition_predictor.load_state_dict(
                    torch.load(ckpt, map_location=self.device, weights_only=True)
                )
                self._transition_predictor.eval()
                logger.info("Loaded transition_predictor from %s", ckpt)
            except Exception as e:
                logger.warning("Failed to load transition_predictor: %s", e)
        else:
            logger.info("No transition_predictor checkpoint at %s — using defaults", ckpt)

        self._models_loaded = True

    # ------------------------------------------------------------------
    # Internal prediction methods
    # ------------------------------------------------------------------

    def _predict_scene_type(self, clip_embedding: list[float] | None) -> str:
        """Classify scene type from CLIP embedding."""
        if self._scene_classifier is None or clip_embedding is None:
            return _DEFAULT_SCENE_TYPE

        try:
            import torch
            from src.style_learner.training.scene_classifier import SCENE_TYPES

            x = torch.tensor([clip_embedding], dtype=torch.float32).to(self.device)
            with torch.no_grad():
                logits = self._scene_classifier(x)
            idx = logits.argmax(dim=-1).item()
            return SCENE_TYPES[idx]
        except Exception as e:
            logger.warning("Scene type prediction failed: %s", e)
            return _DEFAULT_SCENE_TYPE

    def _predict_camera_motion(
        self,
        sentence_embedding: list[float] | None,
        scene_type_idx: int,
    ) -> tuple[str, float]:
        """Predict camera motion and magnitude."""
        if self._camera_predictor is None or sentence_embedding is None:
            return _DEFAULT_CAMERA_MOTION, _DEFAULT_CAMERA_MAGNITUDE

        try:
            import torch
            from src.style_learner.training.camera_predictor import CAMERA_MOTIONS

            # Build input: 384-dim sentence emb + 8-dim scene type one-hot
            scene_onehot = [0.0] * 8
            if 0 <= scene_type_idx < 8:
                scene_onehot[scene_type_idx] = 1.0
            features = list(sentence_embedding) + scene_onehot

            x = torch.tensor([features], dtype=torch.float32).to(self.device)
            with torch.no_grad():
                motion_logits, magnitude = self._camera_predictor(x)
            motion_idx = motion_logits.argmax(dim=-1).item()
            return CAMERA_MOTIONS[motion_idx], float(magnitude.item())
        except Exception as e:
            logger.warning("Camera motion prediction failed: %s", e)
            return _DEFAULT_CAMERA_MOTION, _DEFAULT_CAMERA_MAGNITUDE

    def _predict_text_placement(
        self,
        scene_type_idx: int,
        text_role: str,
        text_length: int,
        narration_phase: str,
    ) -> dict:
        """Predict text placement (x, y, font_size_ratio, animation)."""
        if self._text_placement is None:
            return {
                "x": _DEFAULT_TEXT_X,
                "y": _DEFAULT_TEXT_Y,
                "font_size_ratio": _DEFAULT_FONT_SIZE_RATIO,
                "animation": _DEFAULT_ANIMATION,
            }

        try:
            import torch
            from src.style_learner.training.text_placement import (
                TEXT_ROLES, NARRATION_PHASES, ANIMATIONS,
            )

            # scene type one-hot (8)
            scene_oh = [0.0] * 8
            if 0 <= scene_type_idx < 8:
                scene_oh[scene_type_idx] = 1.0

            # text role one-hot (5)
            role_oh = [0.0] * len(TEXT_ROLES)
            if text_role in TEXT_ROLES:
                role_oh[TEXT_ROLES.index(text_role)] = 1.0
            else:
                role_oh[0] = 1.0

            # normalized text length (1)
            norm_len = [min(text_length / 100.0, 1.0)]

            # narration phase one-hot (4)
            phase_oh = [0.0] * len(NARRATION_PHASES)
            if narration_phase in NARRATION_PHASES:
                phase_oh[NARRATION_PHASES.index(narration_phase)] = 1.0
            else:
                phase_oh[0] = 1.0

            features = scene_oh + role_oh + norm_len + phase_oh
            x = torch.tensor([features], dtype=torch.float32).to(self.device)

            with torch.no_grad():
                pos_x, pos_y, font_size, anim_logits = self._text_placement(x)

            anim_idx = anim_logits.argmax(dim=-1).item()
            return {
                "x": round(float(pos_x.item()), 3),
                "y": round(float(pos_y.item()), 3),
                "font_size_ratio": round(float(font_size.item()), 4),
                "animation": ANIMATIONS[anim_idx],
            }
        except Exception as e:
            logger.warning("Text placement prediction failed: %s", e)
            return {
                "x": _DEFAULT_TEXT_X,
                "y": _DEFAULT_TEXT_Y,
                "font_size_ratio": _DEFAULT_FONT_SIZE_RATIO,
                "animation": _DEFAULT_ANIMATION,
            }

    def _predict_transition(
        self,
        clip_emb_a: list[float] | None,
        clip_emb_b: list[float] | None,
        narration_phase: str,
    ) -> dict:
        """Predict transition type and duration between two scenes."""
        if (
            self._transition_predictor is None
            or clip_emb_a is None
            or clip_emb_b is None
        ):
            return {
                "type": _DEFAULT_TRANSITION_TYPE,
                "duration": _DEFAULT_TRANSITION_DURATION,
            }

        try:
            import torch
            from src.style_learner.training.transition_predictor import (
                TRANSITION_TYPES, NARRATION_PHASES,
            )

            phase_oh = [0.0] * len(NARRATION_PHASES)
            if narration_phase in NARRATION_PHASES:
                phase_oh[NARRATION_PHASES.index(narration_phase)] = 1.0
            else:
                phase_oh[0] = 1.0

            features = list(clip_emb_a) + list(clip_emb_b) + phase_oh
            x = torch.tensor([features], dtype=torch.float32).to(self.device)

            with torch.no_grad():
                trans_logits, duration = self._transition_predictor(x)
            trans_idx = trans_logits.argmax(dim=-1).item()
            return {
                "type": TRANSITION_TYPES[trans_idx],
                "duration": round(float(duration.item()), 2),
            }
        except Exception as e:
            logger.warning("Transition prediction failed: %s", e)
            return {
                "type": _DEFAULT_TRANSITION_TYPE,
                "duration": _DEFAULT_TRANSITION_DURATION,
            }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_plan(
        self,
        parsed_script: dict,
        episode_palette: list[str] | None = None,
    ) -> dict:
        """Generate a full production plan from a parsed script.

        Args:
            parsed_script: Dict with "segments" list, each containing
                "narration", "scene_description", "key_phrases", etc.
            episode_palette: Optional list of hex color strings for the episode.

        Returns:
            Production plan dict with episode metadata and per-scene plans.
        """
        if not self._models_loaded:
            self.load_models()

        from src.style_learner.inference.visual_metaphor import suggest_metaphor

        segments = parsed_script.get("segments", parsed_script.get("scenes", []))
        episode_title = parsed_script.get("title", "Untitled Episode")
        episode_mood = parsed_script.get("mood", "educational")

        if episode_palette is None:
            episode_palette = ["#2C3E50", "#E74C3C", "#ECF0F1", "#3498DB", "#2ECC71"]

        scenes_plan = []
        prev_clip_emb = None

        for idx, segment in enumerate(segments):
            narration = segment.get("narration", "")
            scene_desc = segment.get("scene_description", narration[:200])
            duration = segment.get("duration", 5.0)
            key_phrases = segment.get("key_phrases", [])
            narration_phase = segment.get("narration_phase", "explaining")

            # Embeddings (may be precomputed or None)
            clip_emb = segment.get("clip_embedding", None)
            sentence_emb = segment.get("sentence_embedding", None)

            # 1. Scene type
            scene_type = self._predict_scene_type(clip_emb)
            try:
                from src.style_learner.training.scene_classifier import SCENE_TYPES
                scene_type_idx = SCENE_TYPES.index(scene_type)
            except (ImportError, ValueError):
                scene_type_idx = 0

            # 2. Camera motion
            camera_motion, camera_magnitude = self._predict_camera_motion(
                sentence_emb, scene_type_idx
            )

            # 3. Text elements with placement
            text_elements = []
            for phrase_idx, phrase in enumerate(key_phrases[:5]):
                # Determine role heuristically
                if phrase_idx == 0 and idx == 0:
                    role = "title"
                elif len(phrase) < 20:
                    role = "label"
                else:
                    role = "caption"

                placement = self._predict_text_placement(
                    scene_type_idx, role, len(phrase), narration_phase
                )
                text_elements.append({
                    "content": phrase,
                    "role": role,
                    "trigger_word": phrase.split()[0] if phrase.split() else "",
                    **placement,
                })

            # 4. Transition to next scene
            next_clip_emb = None
            if idx + 1 < len(segments):
                next_clip_emb = segments[idx + 1].get("clip_embedding", None)
            transition = self._predict_transition(
                clip_emb, next_clip_emb, narration_phase
            )

            # 5. Visual metaphor
            metaphor = suggest_metaphor(narration)

            scene_plan = {
                "scene_id": f"scene_{idx:03d}",
                "scene_type": scene_type,
                "scene_description": scene_desc,
                "narration": narration,
                "duration": duration,
                "camera_motion": camera_motion,
                "camera_magnitude": camera_magnitude,
                "text_elements": text_elements,
                "transition_out": transition,
                "visual_metaphor": metaphor,
                "narration_phase": narration_phase,
            }
            scenes_plan.append(scene_plan)
            prev_clip_emb = clip_emb

        plan = {
            "title": episode_title,
            "episode_mood": episode_mood,
            "episode_palette": episode_palette,
            "fps": 30,
            "total_scenes": len(scenes_plan),
            "total_duration": sum(s["duration"] for s in scenes_plan),
            "scenes": scenes_plan,
        }

        logger.info(
            "Generated production plan: %d scenes, %.1fs total",
            plan["total_scenes"], plan["total_duration"],
        )
        return plan

    def save_plan(self, plan: dict, output_path: Path) -> None:
        """Save production plan to JSON file.

        Args:
            plan: Production plan dict from generate_plan().
            output_path: Path to write the JSON file.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)

        logger.info("Production plan saved to %s", output_path)
