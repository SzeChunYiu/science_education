"""Text placement predictor: scene context → position, size, animation."""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import json
import numpy as np
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TEXT_ROLES = ["title", "subtitle", "caption", "label", "annotation"]
NARRATION_PHASES = ["introducing", "listing", "concluding", "explaining"]
ANIMATIONS = ["fade_in", "slide_in", "pop_in", "none"]

NUM_SCENE_TYPES = 8


class TextPlacementMLP(nn.Module):
    """3-layer MLP with four output heads for text placement prediction.

    Input: 8-dim scene type + 5-dim text role + 1-dim normalised text length
           + 4-dim narration phase = 18-dim total.
    Outputs:
        x (sigmoid), y (sigmoid), font_size_ratio (sigmoid), animation (4-class).
    """

    def __init__(
        self,
        input_dim: int = 18,
        hidden1: int = 64,
        hidden2: int = 32,
        num_animations: int = 4,
    ):
        super().__init__()
        self.backbone = nn.Sequential(
            nn.Linear(input_dim, hidden1),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden1, hidden2),
            nn.ReLU(),
            nn.Dropout(0.2),
        )
        self.x_head = nn.Sequential(nn.Linear(hidden2, 1), nn.Sigmoid())
        self.y_head = nn.Sequential(nn.Linear(hidden2, 1), nn.Sigmoid())
        self.font_size_head = nn.Sequential(nn.Linear(hidden2, 1), nn.Sigmoid())
        self.animation_head = nn.Linear(hidden2, num_animations)

    def forward(
        self, x: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor]:
        features = self.backbone(x)
        pos_x = self.x_head(features).squeeze(-1)
        pos_y = self.y_head(features).squeeze(-1)
        font_size = self.font_size_head(features).squeeze(-1)
        anim_logits = self.animation_head(features)
        return pos_x, pos_y, font_size, anim_logits


class TextPlacementDataset(Dataset):
    """Dataset for text placement training. Only includes scenes with text elements."""

    def __init__(self, records: list[dict]):
        self.inputs = []
        self.targets_x = []
        self.targets_y = []
        self.targets_font = []
        self.targets_anim = []
        self.weights = []

        for r in records:
            # Skip records without text placement data
            if "text_x" not in r or "text_y" not in r:
                continue

            # Scene type one-hot (8-dim)
            scene_onehot = np.zeros(NUM_SCENE_TYPES, dtype=np.float32)
            scene_idx = r.get("scene_type_idx", 0)
            if 0 <= scene_idx < NUM_SCENE_TYPES:
                scene_onehot[scene_idx] = 1.0

            # Text role one-hot (5-dim)
            role_onehot = np.zeros(len(TEXT_ROLES), dtype=np.float32)
            role = r.get("text_role", "caption")
            if role in TEXT_ROLES:
                role_onehot[TEXT_ROLES.index(role)] = 1.0
            else:
                role_onehot[TEXT_ROLES.index("caption")] = 1.0

            # Normalised text length (1-dim)
            text_len = np.array(
                [float(r.get("text_length_norm", 0.5))], dtype=np.float32
            )

            # Narration phase one-hot (4-dim)
            phase_onehot = np.zeros(len(NARRATION_PHASES), dtype=np.float32)
            phase = r.get("narration_phase", "explaining")
            if phase in NARRATION_PHASES:
                phase_onehot[NARRATION_PHASES.index(phase)] = 1.0
            else:
                phase_onehot[NARRATION_PHASES.index("explaining")] = 1.0

            combined = np.concatenate([scene_onehot, role_onehot, text_len, phase_onehot])
            self.inputs.append(combined)

            # Targets
            self.targets_x.append(float(r.get("text_x", 0.5)))
            self.targets_y.append(float(r.get("text_y", 0.5)))
            self.targets_font.append(float(r.get("font_size_ratio", 0.5)))

            anim = r.get("text_animation", "none")
            self.targets_anim.append(
                ANIMATIONS.index(anim) if anim in ANIMATIONS else ANIMATIONS.index("none")
            )

            self.weights.append(float(r.get("sample_weight", 1.0)))

    def __len__(self) -> int:
        return len(self.inputs)

    def __getitem__(
        self, idx: int
    ) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, torch.Tensor, float]:
        return (
            torch.tensor(self.inputs[idx]),
            torch.tensor(self.targets_x[idx], dtype=torch.float32),
            torch.tensor(self.targets_y[idx], dtype=torch.float32),
            torch.tensor(self.targets_font[idx], dtype=torch.float32),
            torch.tensor(self.targets_anim[idx], dtype=torch.long),
            self.weights[idx],
        )


def train_text_placement(
    dataset_path: Path,
    splits_path: Path,
    output_path: Path,
    epochs: int = 100,
    lr: float = 1e-3,
    patience: int = 10,
    device: str = "cuda",
) -> float:
    """Train text placement predictor. Returns best validation loss.

    Combined loss: MSE(x, y, font_size) + cross-entropy(animation), equal weight.
    """
    records = [json.loads(line) for line in dataset_path.read_text().strip().split("\n")]
    splits = json.loads(splits_path.read_text())

    train_records = [r for r in records if r["video_id"] in splits["train"]]
    val_records = [r for r in records if r["video_id"] in splits["val"]]

    train_ds = TextPlacementDataset(train_records)
    val_ds = TextPlacementDataset(val_records)

    if len(train_ds) == 0:
        logger.warning("No text placement training data found. Skipping.")
        return 0.0

    sampler = WeightedRandomSampler(
        weights=[d[5] for d in train_ds],
        num_samples=len(train_ds),
        replacement=True,
    )

    train_loader = DataLoader(train_ds, batch_size=64, sampler=sampler)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    model = TextPlacementMLP().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    ce_loss = nn.CrossEntropyLoss()
    mse_loss = nn.MSELoss()

    best_val_loss = float("inf")
    patience_counter = 0

    for epoch in range(epochs):
        # Train
        model.train()
        for inputs, tx, ty, tf, ta, _ in train_loader:
            inputs = inputs.to(device)
            tx, ty, tf = tx.to(device), ty.to(device), tf.to(device)
            ta = ta.to(device)

            pred_x, pred_y, pred_font, anim_logits = model(inputs)

            pos_loss = mse_loss(pred_x, tx) + mse_loss(pred_y, ty) + mse_loss(pred_font, tf)
            anim_loss = ce_loss(anim_logits, ta)
            loss = pos_loss + anim_loss

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        # Validate
        model.eval()
        val_loss_total = 0.0
        val_batches = 0
        with torch.no_grad():
            for inputs, tx, ty, tf, ta, _ in val_loader:
                inputs = inputs.to(device)
                tx, ty, tf = tx.to(device), ty.to(device), tf.to(device)
                ta = ta.to(device)

                pred_x, pred_y, pred_font, anim_logits = model(inputs)

                pos_loss = mse_loss(pred_x, tx) + mse_loss(pred_y, ty) + mse_loss(pred_font, tf)
                anim_loss = ce_loss(anim_logits, ta)
                val_loss_total += (pos_loss + anim_loss).item()
                val_batches += 1

        val_loss = val_loss_total / max(val_batches, 1)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            patience_counter = 0
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output_path)
            logger.info(f"Epoch {epoch}: val_loss={val_loss:.4f} (new best), saved")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break

    logger.info(f"Training complete. Best val loss: {best_val_loss:.4f}")
    return best_val_loss


def load_text_placement(checkpoint_path: Path, device: str = "cpu") -> TextPlacementMLP:
    """Load trained text placement model for inference."""
    model = TextPlacementMLP()
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    return model


def predict_text_placement(
    model: TextPlacementMLP,
    scene_type_idx: int,
    text_role: str,
    text_length_norm: float,
    narration_phase: str,
) -> dict:
    """Predict text placement from scene context."""
    # Build input vector
    scene_onehot = np.zeros(NUM_SCENE_TYPES, dtype=np.float32)
    if 0 <= scene_type_idx < NUM_SCENE_TYPES:
        scene_onehot[scene_type_idx] = 1.0

    role_onehot = np.zeros(len(TEXT_ROLES), dtype=np.float32)
    if text_role in TEXT_ROLES:
        role_onehot[TEXT_ROLES.index(text_role)] = 1.0

    text_len = np.array([float(text_length_norm)], dtype=np.float32)

    phase_onehot = np.zeros(len(NARRATION_PHASES), dtype=np.float32)
    if narration_phase in NARRATION_PHASES:
        phase_onehot[NARRATION_PHASES.index(narration_phase)] = 1.0

    combined = np.concatenate([scene_onehot, role_onehot, text_len, phase_onehot])

    with torch.no_grad():
        inp = torch.tensor(combined).unsqueeze(0)
        pred_x, pred_y, pred_font, anim_logits = model(inp)
        anim_probs = torch.softmax(anim_logits, dim=1).squeeze().numpy()

    top_anim_idx = int(anim_probs.argmax())
    return {
        "x": float(pred_x.item()),
        "y": float(pred_y.item()),
        "font_size_ratio": float(pred_font.item()),
        "animation": ANIMATIONS[top_anim_idx],
        "animation_confidence": float(anim_probs[top_anim_idx]),
    }
