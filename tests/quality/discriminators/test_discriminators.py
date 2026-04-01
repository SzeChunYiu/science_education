"""Tests for discriminator model architectures.

Uses random tensors on CPU -- no pretrained weights, GPU, or CLIP needed.
"""

import pytest
import torch
from unittest.mock import MagicMock, patch


# ---------------------------------------------------------------------------
# SemanticMLP (internal architecture)
# ---------------------------------------------------------------------------


class TestSemanticMLP:
    def test_forward_shape(self):
        """896-dim input -> (1,) sigmoid-ready output (before sigmoid in score())."""
        from src.quality.discriminators.semantic_discriminator import _SemanticMLP

        model = _SemanticMLP(input_dim=896, hidden_dim=512)
        model.eval()
        x = torch.randn(1, 896)
        with torch.no_grad():
            out = model(x)
        # forward squeezes last dim: (1, 1) -> (1,)
        assert out.shape == (1,)

    def test_batch_forward(self):
        """Batch of 4 should produce (4,)."""
        from src.quality.discriminators.semantic_discriminator import _SemanticMLP

        model = _SemanticMLP(input_dim=896, hidden_dim=512)
        model.eval()
        x = torch.randn(4, 896)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (4,)

    def test_sigmoid_output_bounded(self):
        """After sigmoid, output must be in [0, 1]."""
        from src.quality.discriminators.semantic_discriminator import _SemanticMLP

        model = _SemanticMLP()
        model.eval()
        x = torch.randn(10, 896)
        with torch.no_grad():
            logits = model(x)
            probs = torch.sigmoid(logits)
        assert (probs >= 0.0).all()
        assert (probs <= 1.0).all()


class TestSemanticDiscriminatorScore:
    def test_score_returns_float(self):
        """Mock internal models, verify score() returns 0-1 float."""
        from src.quality.discriminators.semantic_discriminator import (
            SemanticDiscriminator,
            _SemanticMLP,
        )

        disc = SemanticDiscriminator(checkpoint_path=None, device="cpu")

        # Build and assign the MLP directly
        disc.model = _SemanticMLP(input_dim=896, hidden_dim=512)
        disc.model.eval()

        # Mock CLIP and sentence model to return fixed embeddings
        fake_img_emb = torch.randn(512)
        fake_img_emb = fake_img_emb / fake_img_emb.norm()
        fake_txt_emb = torch.randn(384)

        disc._encode_image = MagicMock(return_value=fake_img_emb)
        disc._encode_text = MagicMock(return_value=fake_txt_emb)

        from PIL import Image
        img = Image.new("RGB", (64, 64), color=(128, 128, 128))
        score = disc.score(img, "A scientist examining cells")

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0


# ---------------------------------------------------------------------------
# FlowMLP (internal architecture)
# ---------------------------------------------------------------------------


class TestFlowMLP:
    def test_forward_shape(self):
        """1027-dim input -> (1,) sigmoid-ready output."""
        from src.quality.discriminators.flow_discriminator import _FlowMLP

        model = _FlowMLP(input_dim=1027, hidden_dim=512)
        model.eval()
        x = torch.randn(1, 1027)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (1,)

    def test_batch_forward(self):
        """Batch of 4 should produce (4,)."""
        from src.quality.discriminators.flow_discriminator import _FlowMLP

        model = _FlowMLP(input_dim=1027, hidden_dim=512)
        model.eval()
        x = torch.randn(4, 1027)
        with torch.no_grad():
            out = model(x)
        assert out.shape == (4,)

    def test_sigmoid_output_bounded(self):
        """After sigmoid, output must be in [0, 1]."""
        from src.quality.discriminators.flow_discriminator import _FlowMLP

        model = _FlowMLP()
        model.eval()
        x = torch.randn(10, 1027)
        with torch.no_grad():
            logits = model(x)
            probs = torch.sigmoid(logits)
        assert (probs >= 0.0).all()
        assert (probs <= 1.0).all()


class TestFlowDiscriminatorScore:
    def test_score_returns_float(self):
        """Mock internal models, verify score() returns 0-1 float."""
        from src.quality.discriminators.flow_discriminator import (
            FlowDiscriminator,
            _FlowMLP,
        )

        disc = FlowDiscriminator(checkpoint_path=None, device="cpu")

        # Build and assign the MLP directly
        disc.model = _FlowMLP(input_dim=1027, hidden_dim=512)
        disc.model.eval()

        # Mock CLIP encoding
        fake_emb_a = torch.randn(512)
        fake_emb_a = fake_emb_a / fake_emb_a.norm()
        fake_emb_b = torch.randn(512)
        fake_emb_b = fake_emb_b / fake_emb_b.norm()

        disc._encode_image = MagicMock(side_effect=[fake_emb_a, fake_emb_b])

        from PIL import Image
        img_a = Image.new("RGB", (64, 64), color=(100, 100, 100))
        img_b = Image.new("RGB", (64, 64), color=(200, 200, 200))
        score = disc.score(img_a, img_b, transition_type="cut")

        assert isinstance(score, float)
        assert 0.0 <= score <= 1.0
