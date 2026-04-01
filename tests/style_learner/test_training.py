"""Tests for src/style_learner/training/ model architectures.

Uses small random tensors on CPU only -- no GPU or trained weights needed.
"""

import numpy as np
import pytest
import torch


# ---------------------------------------------------------------------------
# SceneClassifierMLP
# ---------------------------------------------------------------------------


class TestSceneClassifierMLP:
    def test_forward_shape(self):
        """Input (1, 512) -> output (1, 8)."""
        from src.style_learner.training.scene_classifier import SceneClassifierMLP

        model = SceneClassifierMLP(input_dim=512, hidden_dim=256, num_classes=8)
        model.eval()
        x = torch.randn(1, 512)
        out = model(x)
        assert out.shape == (1, 8)

    def test_batch_forward(self):
        """Batch of 4 should produce (4, 8)."""
        from src.style_learner.training.scene_classifier import SceneClassifierMLP

        model = SceneClassifierMLP()
        model.eval()
        x = torch.randn(4, 512)
        out = model(x)
        assert out.shape == (4, 8)

    def test_predict_scene_type(self):
        """predict_scene_type returns dict with expected keys."""
        from src.style_learner.training.scene_classifier import (
            SceneClassifierMLP,
            predict_scene_type,
            SCENE_TYPES,
        )

        model = SceneClassifierMLP()
        model.eval()
        embedding = np.random.randn(512).astype(np.float32)
        result = predict_scene_type(model, embedding)

        assert "scene_type" in result
        assert result["scene_type"] in SCENE_TYPES
        assert 0.0 <= result["confidence"] <= 1.0
        assert "scores" in result
        assert len(result["scores"]) == 8

    def test_save_load_roundtrip(self, tmp_path):
        """Save model, reload, verify same output."""
        from src.style_learner.training.scene_classifier import (
            SceneClassifierMLP,
            load_scene_classifier,
        )

        model = SceneClassifierMLP()
        model.eval()
        x = torch.randn(1, 512)

        with torch.no_grad():
            expected = model(x)

        ckpt = tmp_path / "scene_cls.pt"
        torch.save(model.state_dict(), ckpt)

        loaded = load_scene_classifier(ckpt, device="cpu")
        with torch.no_grad():
            actual = loaded(x)

        assert torch.allclose(expected, actual, atol=1e-6)


# ---------------------------------------------------------------------------
# CameraMotionMLP
# ---------------------------------------------------------------------------


class TestCameraMotionMLP:
    def test_forward_shape(self):
        """Input (1, 392) -> motion (1, 8), magnitude (1,)."""
        from src.style_learner.training.camera_predictor import CameraMotionMLP

        model = CameraMotionMLP(input_dim=392)
        model.eval()
        x = torch.randn(1, 392)
        motion, magnitude = model(x)
        assert motion.shape == (1, 8)
        assert magnitude.shape == (1,)

    def test_magnitude_is_sigmoid(self):
        """Magnitude output must be in [0, 1] due to sigmoid."""
        from src.style_learner.training.camera_predictor import CameraMotionMLP

        model = CameraMotionMLP()
        model.eval()
        x = torch.randn(10, 392)
        with torch.no_grad():
            _, magnitude = model(x)
        assert (magnitude >= 0.0).all()
        assert (magnitude <= 1.0).all()

    def test_predict_camera_motion(self):
        """predict_camera_motion returns dict with expected keys."""
        from src.style_learner.training.camera_predictor import (
            CameraMotionMLP,
            predict_camera_motion,
            CAMERA_MOTIONS,
        )

        model = CameraMotionMLP()
        model.eval()
        sent_emb = np.random.randn(384).astype(np.float32)
        result = predict_camera_motion(model, sent_emb, scene_type_idx=2)

        assert result["camera_motion"] in CAMERA_MOTIONS
        assert 0.0 <= result["confidence"] <= 1.0
        assert 0.0 <= result["magnitude"] <= 1.0
        assert len(result["scores"]) == 8


# ---------------------------------------------------------------------------
# TextPlacementMLP
# ---------------------------------------------------------------------------


class TestTextPlacementMLP:
    def test_forward_shape(self):
        """Input (1, 18) -> 4 output heads."""
        from src.style_learner.training.text_placement import TextPlacementMLP

        model = TextPlacementMLP(input_dim=18)
        model.eval()
        x = torch.randn(1, 18)
        pos_x, pos_y, font_size, anim_logits = model(x)

        assert pos_x.shape == (1,)
        assert pos_y.shape == (1,)
        assert font_size.shape == (1,)
        assert anim_logits.shape == (1, 4)

    def test_sigmoid_outputs_bounded(self):
        """x, y, font_size heads use sigmoid, must be in [0, 1]."""
        from src.style_learner.training.text_placement import TextPlacementMLP

        model = TextPlacementMLP()
        model.eval()
        x = torch.randn(10, 18)
        with torch.no_grad():
            px, py, fs, _ = model(x)
        for t in [px, py, fs]:
            assert (t >= 0.0).all()
            assert (t <= 1.0).all()

    def test_predict_text_placement(self):
        """predict_text_placement returns dict with expected keys."""
        from src.style_learner.training.text_placement import (
            TextPlacementMLP,
            predict_text_placement,
            ANIMATIONS,
        )

        model = TextPlacementMLP()
        model.eval()
        result = predict_text_placement(
            model,
            scene_type_idx=3,
            text_role="title",
            text_length_norm=0.5,
            narration_phase="introducing",
        )

        assert 0.0 <= result["x"] <= 1.0
        assert 0.0 <= result["y"] <= 1.0
        assert 0.0 <= result["font_size_ratio"] <= 1.0
        assert result["animation"] in ANIMATIONS


# ---------------------------------------------------------------------------
# TransitionMLP
# ---------------------------------------------------------------------------


class TestTransitionMLP:
    def test_forward_shape(self):
        """Input (1, 1028) -> transition (1, 3), duration (1,)."""
        from src.style_learner.training.transition_predictor import TransitionMLP

        model = TransitionMLP(input_dim=1028)
        model.eval()
        x = torch.randn(1, 1028)
        trans, dur = model(x)
        assert trans.shape == (1, 3)
        assert dur.shape == (1,)

    def test_duration_sigmoid_bounded(self):
        """Duration output must be in [0, 1] due to sigmoid."""
        from src.style_learner.training.transition_predictor import TransitionMLP

        model = TransitionMLP()
        model.eval()
        x = torch.randn(10, 1028)
        with torch.no_grad():
            _, dur = model(x)
        assert (dur >= 0.0).all()
        assert (dur <= 1.0).all()

    def test_predict_transition(self):
        """predict_transition returns dict with expected keys."""
        from src.style_learner.training.transition_predictor import (
            TransitionMLP,
            predict_transition,
            TRANSITION_TYPES,
        )

        model = TransitionMLP()
        model.eval()
        prev = np.random.randn(512).astype(np.float32)
        next_ = np.random.randn(512).astype(np.float32)
        result = predict_transition(model, prev, next_, narration_phase="explaining")

        assert result["transition_type"] in TRANSITION_TYPES
        assert 0.0 <= result["confidence"] <= 1.0
        assert 0.0 <= result["duration"] <= 1.0
        assert len(result["scores"]) == 3

    def test_save_load_roundtrip(self, tmp_path):
        """Save model, reload, verify same output for TransitionMLP."""
        from src.style_learner.training.transition_predictor import (
            TransitionMLP,
            load_transition_predictor,
        )

        model = TransitionMLP()
        model.eval()
        x = torch.randn(1, 1028)

        with torch.no_grad():
            expected_t, expected_d = model(x)

        ckpt = tmp_path / "transition.pt"
        torch.save(model.state_dict(), ckpt)

        loaded = load_transition_predictor(ckpt, device="cpu")
        with torch.no_grad():
            actual_t, actual_d = loaded(x)

        assert torch.allclose(expected_t, actual_t, atol=1e-6)
        assert torch.allclose(expected_d, actual_d, atol=1e-6)
