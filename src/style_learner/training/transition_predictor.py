"""Transition predictor: consecutive CLIP embeddings + narration phase → transition type + duration."""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import json
import numpy as np
from pathlib import Path
import logging
from typing import Optional

logger = logging.getLogger(__name__)

TRANSITION_TYPES = ["cut", "dissolve", "wipe"]
NARRATION_PHASES = ["introducing", "listing", "concluding", "explaining"]


class TransitionMLP(nn.Module):
    """3-layer MLP with two output heads for transition prediction.

    Input: 512-dim CLIP scene N last frame + 512-dim CLIP scene N+1 first frame
           + 4-dim narration phase one-hot = 1028-dim total.
    Head 1: 3-class transition type (cut/dissolve/wipe).
    Head 2: 1-dim sigmoid duration (0-1 seconds).
    """

    def __init__(
        self,
        input_dim: int = 1028,
        hidden1: int = 512,
        hidden2: int = 128,
        num_transitions: int = 3,
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
        self.transition_head = nn.Linear(hidden2, num_transitions)
        self.duration_head = nn.Sequential(
            nn.Linear(hidden2, 1),
            nn.Sigmoid(),
        )

    def forward(self, x: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        features = self.backbone(x)
        trans_logits = self.transition_head(features)
        duration = self.duration_head(features).squeeze(-1)
        return trans_logits, duration


class TransitionDataset(Dataset):
    """Dataset for transition prediction from consecutive scene pairs."""

    def __init__(self, records: list[dict]):
        self.inputs = []
        self.trans_labels = []
        self.durations = []
        self.weights = []

        for r in records:
            # CLIP embedding of scene N last frame (512-dim)
            clip_prev = np.array(
                r.get("clip_embedding_prev", np.zeros(512)),
                dtype=np.float32,
            )
            if clip_prev.shape[0] != 512:
                clip_prev = np.zeros(512, dtype=np.float32)

            # CLIP embedding of scene N+1 first frame (512-dim)
            clip_next = np.array(
                r.get("clip_embedding_next", np.zeros(512)),
                dtype=np.float32,
            )
            if clip_next.shape[0] != 512:
                clip_next = np.zeros(512, dtype=np.float32)

            # Narration phase one-hot (4-dim)
            phase_onehot = np.zeros(len(NARRATION_PHASES), dtype=np.float32)
            phase = r.get("narration_phase", "explaining")
            if phase in NARRATION_PHASES:
                phase_onehot[NARRATION_PHASES.index(phase)] = 1.0
            else:
                phase_onehot[NARRATION_PHASES.index("explaining")] = 1.0

            combined = np.concatenate([clip_prev, clip_next, phase_onehot])
            self.inputs.append(combined)

            # Transition type label
            trans = r.get("transition_type", "cut")
            self.trans_labels.append(
                TRANSITION_TYPES.index(trans) if trans in TRANSITION_TYPES else 0
            )

            # Duration (0-1 seconds)
            self.durations.append(
                float(np.clip(r.get("transition_duration", 0.0), 0.0, 1.0))
            )

            # Sample weight
            self.weights.append(float(r.get("sample_weight", 1.0)))

    def __len__(self) -> int:
        return len(self.inputs)

    def __getitem__(self, idx: int) -> tuple[torch.Tensor, torch.Tensor, torch.Tensor, float]:
        return (
            torch.tensor(self.inputs[idx]),
            torch.tensor(self.trans_labels[idx], dtype=torch.long),
            torch.tensor(self.durations[idx], dtype=torch.float32),
            self.weights[idx],
        )


def train_transition_predictor(
    dataset_path: Path,
    splits_path: Path,
    output_path: Path,
    epochs: int = 100,
    lr: float = 1e-3,
    patience: int = 10,
    device: str = "cuda",
) -> float:
    """Train transition predictor. Returns best validation accuracy.

    Combined loss: cross-entropy(transition) + MSE(duration).
    """
    records = [json.loads(line) for line in dataset_path.read_text().strip().split("\n")]
    splits = json.loads(splits_path.read_text())

    train_records = [r for r in records if r["video_id"] in splits["train"]]
    val_records = [r for r in records if r["video_id"] in splits["val"]]

    train_ds = TransitionDataset(train_records)
    val_ds = TransitionDataset(val_records)

    if len(train_ds) == 0:
        logger.warning("No transition training data found. Skipping.")
        return 0.0

    sampler = WeightedRandomSampler(
        weights=[d[3] for d in train_ds],
        num_samples=len(train_ds),
        replacement=True,
    )

    train_loader = DataLoader(train_ds, batch_size=64, sampler=sampler)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    model = TransitionMLP().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    ce_loss = nn.CrossEntropyLoss()
    mse_loss = nn.MSELoss()

    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(epochs):
        # Train
        model.train()
        for inputs, trans_labels, durations, _ in train_loader:
            inputs = inputs.to(device)
            trans_labels = trans_labels.to(device)
            durations = durations.to(device)

            trans_logits, dur_pred = model(inputs)
            loss = ce_loss(trans_logits, trans_labels) + mse_loss(dur_pred, durations)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

        # Validate
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for inputs, trans_labels, durations, _ in val_loader:
                inputs = inputs.to(device)
                trans_labels = trans_labels.to(device)

                trans_logits, _ = model(inputs)
                preds = trans_logits.argmax(dim=1)
                correct += (preds == trans_labels).sum().item()
                total += trans_labels.size(0)

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


def load_transition_predictor(checkpoint_path: Path, device: str = "cpu") -> TransitionMLP:
    """Load trained transition predictor for inference."""
    model = TransitionMLP()
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    return model


def predict_transition(
    model: TransitionMLP,
    clip_embedding_prev: np.ndarray,
    clip_embedding_next: np.ndarray,
    narration_phase: str,
) -> dict:
    """Predict transition type and duration from consecutive scene embeddings."""
    phase_onehot = np.zeros(len(NARRATION_PHASES), dtype=np.float32)
    if narration_phase in NARRATION_PHASES:
        phase_onehot[NARRATION_PHASES.index(narration_phase)] = 1.0

    combined = np.concatenate([
        np.array(clip_embedding_prev, dtype=np.float32),
        np.array(clip_embedding_next, dtype=np.float32),
        phase_onehot,
    ])

    with torch.no_grad():
        inp = torch.tensor(combined).unsqueeze(0)
        trans_logits, duration = model(inp)
        probs = torch.softmax(trans_logits, dim=1).squeeze().numpy()

    top_idx = int(probs.argmax())
    return {
        "transition_type": TRANSITION_TYPES[top_idx],
        "confidence": float(probs[top_idx]),
        "duration": float(duration.item()),
        "scores": {t: float(p) for t, p in zip(TRANSITION_TYPES, probs)},
    }
