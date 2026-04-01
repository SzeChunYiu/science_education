"""Camera motion predictor: sentence embedding + scene type → motion class + magnitude."""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import json
import numpy as np
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)

CAMERA_MOTIONS = [
    "static",
    "pan_left",
    "pan_right",
    "pan_up",
    "pan_down",
    "zoom_in",
    "zoom_out",
    "parallax",
]

NUM_SCENE_TYPES = 8  # matches scene_classifier.SCENE_TYPES


class CameraMotionMLP(nn.Module):
    """3-layer MLP with two output heads for camera motion prediction.

    Input: 384-dim sentence embedding + 8-dim scene type one-hot = 392-dim.
    Head 1: 8-class camera motion.
    Head 2: 1-dim sigmoid magnitude (0-1).
    """

    def __init__(
        self,
        input_dim: int = 392,
        hidden1: int = 256,
        hidden2: int = 128,
        num_motions: int = 8,
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
        self.motion_head = nn.Linear(hidden2, num_motions)
        self.magnitude_head = nn.Sequential(
            nn.Linear(hidden2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.backbone(x)
        motion_logits = self.motion_head(features)
        magnitude = self.magnitude_head(features).squeeze(-1)
        return motion_logits, magnitude


class CameraDataset(Dataset):
    """Dataset loading sentence embeddings + scene types + camera labels."""

    def __init__(self, records: list[dict]):
        self.inputs = []
        self.motion_labels = []
        self.magnitudes = []
        self.weights = []

        for r in records:
            # Sentence embedding (384-dim)
            sent_emb = np.array(
                r.get("sentence_embedding", np.zeros(384)),
                dtype=np.float32,
            )
            if sent_emb.shape[0] != 384:
                sent_emb = np.zeros(384, dtype=np.float32)

            # Scene type one-hot (8-dim)
            scene_onehot = np.zeros(NUM_SCENE_TYPES, dtype=np.float32)
            scene_idx = r.get("scene_type_idx", 0)
            if 0 <= scene_idx < NUM_SCENE_TYPES:
                scene_onehot[scene_idx] = 1.0

            combined = np.concatenate([sent_emb, scene_onehot])
            self.inputs.append(combined)

            # Camera motion label
            motion = r.get("camera_motion", "static")
            self.motion_labels.append(
                CAMERA_MOTIONS.index(motion) if motion in CAMERA_MOTIONS else 0
            )

            # Magnitude
            self.magnitudes.append(float(r.get("camera_magnitude", 0.0)))

            # Sample weight
            self.weights.append(float(r.get("sample_weight", 1.0)))

    def __len__(self) -> int:
        return len(self.inputs)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, float]:
        return (
            torch.tensor(self.inputs[idx]),
            torch.tensor(self.motion_labels[idx], dtype=torch.long),
            torch.tensor(self.magnitudes[idx], dtype=torch.float32),
            self.weights[idx],
        )


def train_camera_predictor(
    dataset_path: Path,
    splits_path: Path,
    output_path: Path,
    epochs: int = 100,
    lr: float = 1e-3,
    patience: int = 10,
    device: str = "cuda",
    alpha: float = 0.7,
) -> float:
    """Train camera motion predictor. Returns best validation accuracy.

    Combined loss: alpha * cross-entropy(motion) + (1-alpha) * MSE(magnitude).
    """
    records = [json.loads(line) for line in dataset_path.read_text().strip().split("\n")]
    splits = json.loads(splits_path.read_text())

    train_records = [r for r in records if r["video_id"] in splits["train"]]
    val_records = [r for r in records if r["video_id"] in splits["val"]]

    train_ds = CameraDataset(train_records)
    val_ds = CameraDataset(val_records)

    sampler = WeightedRandomSampler(
        weights=[d[3] for d in train_ds],
        num_samples=len(train_ds),
        replacement=True,
    )

    train_loader = DataLoader(train_ds, batch_size=64, sampler=sampler)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    model = CameraMotionMLP().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    ce_loss = nn.CrossEntropyLoss()
    mse_loss = nn.MSELoss()

    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(epochs):
        # Train
        model.train()
        for inputs, motion_labels, magnitudes, _ in train_loader:
            inputs = inputs.to(device)
            motion_labels = motion_labels.to(device)
            magnitudes = magnitudes.to(device)

            motion_logits, mag_pred = model(inputs)
            loss = alpha * ce_loss(motion_logits, motion_labels) + (1 - alpha) * mse_loss(mag_pred, magnitudes)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        # Validate
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, motion_labels, magnitudes, _ in val_loader:
                inputs = inputs.to(device)
                motion_labels = motion_labels.to(device)

                motion_logits, _ = model(inputs)
                preds = motion_logits.argmax(dim=1)
                correct += (preds == motion_labels).sum().item()
                total += motion_labels.size(0)

        val_acc = correct / max(total, 1)

        if val_acc > best_val_acc:
            best_val_acc = val_acc
            patience_counter = 0
            output_path.parent.mkdir(parents=True, exist_ok=True)
            torch.save(model.state_dict(), output_path)
            logger.info(f"Epoch {epoch}: val_acc={val_acc:.4f} (new best), saved")
        else:
            patience_counter += 1
            if patience_counter >= patience:
                logger.info(f"Early stopping at epoch {epoch}")
                break

    logger.info(f"Training complete. Best val accuracy: {best_val_acc:.4f}")
    return best_val_acc


def load_camera_predictor(checkpoint_path: Path, device: str = "cpu") -> CameraMotionMLP:
    """Load trained camera predictor for inference."""
    model = CameraMotionMLP()
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    return model


def predict_camera_motion(
    model: CameraMotionMLP,
    sentence_embedding: np.ndarray,
    scene_type_idx: int,
) -> dict:
    """Predict camera motion and magnitude from sentence embedding + scene type."""
    scene_onehot = np.zeros(NUM_SCENE_TYPES, dtype=np.float32)
    if 0 <= scene_type_idx < NUM_SCENE_TYPES:
        scene_onehot[scene_type_idx] = 1.0

    combined = np.concatenate([
        np.array(sentence_embedding, dtype=np.float32),
        scene_onehot,
    ])

    with torch.no_grad():
        inp = torch.tensor(combined).unsqueeze(0)
        motion_logits, magnitude = model(inp)
        probs = torch.softmax(motion_logits, dim=1).squeeze().numpy()

    top_idx = int(probs.argmax())
    return {
        "camera_motion": CAMERA_MOTIONS[top_idx],
        "confidence": float(probs[top_idx]),
        "magnitude": float(magnitude.item()),
        "scores": {m: float(p) for m, p in zip(CAMERA_MOTIONS, probs)},
    }
