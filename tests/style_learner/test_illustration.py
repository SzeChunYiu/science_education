"""Tests for src/style_learner/illustration/ modules.

No ML models needed -- prompt_builder is pure string logic,
consistency_memory uses PIL but no CLIP.
"""

import json

import numpy as np
import pytest
from PIL import Image
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# prompt_builder tests
# ---------------------------------------------------------------------------


class TestBuildScenePrompt:
    def test_includes_trigger(self):
        """Verify 'teded_style' trigger word is in the positive prompt."""
        from src.style_learner.illustration.prompt_builder import build_scene_prompt

        scene = {"narration": "Newton discovered gravity", "scene_type": "wide scene with characters"}
        positive, negative = build_scene_prompt(scene)
        assert "teded_style" in positive

    def test_includes_metaphor(self):
        """Scene with visual_metaphor -> metaphor text included in prompt."""
        from src.style_learner.illustration.prompt_builder import build_scene_prompt

        scene = {
            "narration": "Gravity pulls objects",
            "scene_type": "scientific diagram",
            "visual_metaphor": "apple falling from tree toward Earth",
        }
        positive, _ = build_scene_prompt(scene)
        assert "apple falling from tree toward Earth" in positive

    def test_includes_palette(self):
        """Palette hex codes appear in prompt."""
        from src.style_learner.illustration.prompt_builder import build_scene_prompt

        scene = {"narration": "Test", "scene_type": "text title card"}
        palette = ["#ff5733", "#33ff57", "#3357ff"]
        positive, _ = build_scene_prompt(scene, episode_palette=palette)
        assert "#ff5733" in positive
        assert "#33ff57" in positive

    def test_negative_prompt_present(self):
        """Verify negative prompt is non-empty."""
        from src.style_learner.illustration.prompt_builder import build_scene_prompt

        scene = {"narration": "Something", "scene_type": "close-up illustrated object"}
        _, negative = build_scene_prompt(scene)
        assert len(negative) > 10
        assert "photorealistic" in negative

    def test_includes_character_description(self):
        """Character descriptions from consistency memory appear in prompt."""
        from src.style_learner.illustration.prompt_builder import build_scene_prompt

        scene = {
            "narration": "Newton thinks",
            "scene_type": "wide scene with characters",
            "character": {"name": "Newton", "pose": "sitting"},
        }
        char_descs = {"Newton": "chibi boy with white wig and brown coat"}
        positive, _ = build_scene_prompt(scene, character_descriptions=char_descs)
        assert "chibi boy with white wig and brown coat" in positive
        assert "sitting pose" in positive

    def test_includes_consistency_anchors(self):
        """Consistency anchors from prior scenes appear in prompt."""
        from src.style_learner.illustration.prompt_builder import build_scene_prompt

        scene = {"narration": "Test", "scene_type": "abstract pattern"}
        anchors = ["warm palette using #ff5733", "same character design"]
        positive, _ = build_scene_prompt(scene, consistency_anchors=anchors)
        assert "warm palette using #ff5733" in positive
        assert "same character design" in positive

    def test_scene_type_hint_included(self):
        """Known scene types get their hint text."""
        from src.style_learner.illustration.prompt_builder import (
            build_scene_prompt,
            SCENE_TYPE_HINTS,
        )

        scene = {"narration": "Map", "scene_type": "historical map"}
        positive, _ = build_scene_prompt(scene)
        assert SCENE_TYPE_HINTS["historical map"] in positive


# ---------------------------------------------------------------------------
# consistency_memory tests
# ---------------------------------------------------------------------------


class TestConsistencyMemory:
    def _make_image(self, color=(128, 100, 80)):
        """Create a small test image."""
        return Image.new("RGB", (64, 64), color=color)

    def test_update_and_anchors(self):
        """Add scenes, verify anchors returned."""
        from src.style_learner.illustration.consistency_memory import ConsistencyMemory

        mem = ConsistencyMemory(episode_id="ep01")

        # Mock _extract_colours to avoid colorthief dependency
        with patch.object(
            ConsistencyMemory,
            "_extract_colours",
            return_value=["#ff5733", "#33ff57", "#aabbcc"],
        ):
            mem.update(
                scene_id=0,
                image=self._make_image(),
                scene_data={
                    "scene_type": "wide scene with characters",
                    "character": {"name": "Newton"},
                    "visual_metaphor": "falling apple",
                },
            )
            mem.update(
                scene_id=1,
                image=self._make_image(),
                scene_data={
                    "scene_type": "scientific diagram",
                    "character": {"name": "Newton"},
                    "visual_metaphor": "falling apple",
                },
            )

        assert len(mem.scenes) == 2

        anchors = mem.get_anchors()
        assert isinstance(anchors, list)
        assert len(anchors) > 0

        # Should mention palette
        palette_anchor = [a for a in anchors if "#ff5733" in a]
        assert len(palette_anchor) >= 1

        # Should mention character
        char_anchor = [a for a in anchors if "Newton" in a]
        assert len(char_anchor) >= 1

        # Should mention recurring visual elements (falling apple appears 2x)
        recurring = [a for a in anchors if "falling apple" in a]
        assert len(recurring) >= 1

    def test_save_load_roundtrip(self, tmp_path):
        """Save to JSON, reload, verify same data."""
        from src.style_learner.illustration.consistency_memory import ConsistencyMemory

        mem = ConsistencyMemory(episode_id="ep42")

        with patch.object(
            ConsistencyMemory,
            "_extract_colours",
            return_value=["#aabb00", "#112233"],
        ):
            mem.update(
                scene_id=0,
                image=self._make_image(),
                scene_data={
                    "scene_type": "close-up illustrated object",
                    "character": {},
                    "visual_metaphor": "magnifying glass",
                },
            )

        save_path = tmp_path / "memory.json"
        mem.save(save_path)

        loaded = ConsistencyMemory.load(save_path)
        assert loaded.episode_id == "ep42"
        assert len(loaded.scenes) == 1
        assert loaded.scenes[0]["scene_type"] == "close-up illustrated object"

        # Palette should survive roundtrip
        palette = loaded.get_palette()
        assert "#aabb00" in palette
        assert "#112233" in palette

    def test_empty_memory_anchors(self):
        """Empty memory returns empty anchors list."""
        from src.style_learner.illustration.consistency_memory import ConsistencyMemory

        mem = ConsistencyMemory(episode_id="empty")
        assert mem.get_anchors() == []
        assert mem.get_palette() == []
