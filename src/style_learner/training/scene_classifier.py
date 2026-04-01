"""Scene type classifier: CLIP embedding → 8-class scene type."""
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader, WeightedRandomSampler
import json
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

SCENE_TYPES = [
    "close-up illustrated object",
    "wide scene with characters",
    "historical map",
    "scientific diagram",
    "microscopic visualization",
    "horizontal timeline",
    "text title card",
    "abstract pattern",
]


class SceneClassifierMLP(nn.Module):
    def __init__(self, input_dim=512, hidden_dim=256, num_classes=8):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim, num_classes),
        )

    def forward(self, x):
        return self.net(x)


class SceneDataset(Dataset):
    """Dataset loading CLIP embeddings + scene type labels from dataset.jsonl."""
    def __init__(self, records: list[dict]):
        self.embeddings = []
        self.labels = []
        self.soft_labels = []
        self.weights = []
        for r in records:
            # Load precomputed CLIP embedding
            emb = np.array(r["clip_embedding"], dtype=np.float32)
            self.embeddings.append(emb)
            self.labels.append(SCENE_TYPES.index(r["scene_type"]) if r["scene_type"] in SCENE_TYPES else 0)
            # Soft labels for label smoothing
            soft = np.zeros(len(SCENE_TYPES), dtype=np.float32)
            for st, score in r.get("scene_type_soft", {}).items():
                if st in SCENE_TYPES:
                    soft[SCENE_TYPES.index(st)] = score
            if soft.sum() > 0:
                soft /= soft.sum()
            else:
                soft[self.labels[-1]] = 1.0
            self.soft_labels.append(soft)
            self.weights.append(r.get("sample_weight", 1.0))

    def __len__(self):
        return len(self.embeddings)

    def __getitem__(self, idx):
        return (
            torch.tensor(self.embeddings[idx]),
            torch.tensor(self.labels[idx], dtype=torch.long),
            torch.tensor(self.soft_labels[idx]),
            self.weights[idx],
        )


def train_scene_classifier(
    dataset_path: Path,
    splits_path: Path,
    output_path: Path,
    epochs: int = 100,
    lr: float = 1e-3,
    patience: int = 10,
    device: str = "cuda",
):
    """Train scene type classifier. Returns best validation accuracy."""
    # Load data
    records = [json.loads(line) for line in dataset_path.read_text().strip().split("\n")]
    splits = json.loads(splits_path.read_text())

    train_records = [r for r in records if r["video_id"] in splits["train"]]
    val_records = [r for r in records if r["video_id"] in splits["val"]]

    train_ds = SceneDataset(train_records)
    val_ds = SceneDataset(val_records)

    # Weighted sampler
    sampler = WeightedRandomSampler(
        weights=[d[3] for d in train_ds],
        num_samples=len(train_ds),
        replacement=True,
    )

    train_loader = DataLoader(train_ds, batch_size=64, sampler=sampler)
    val_loader = DataLoader(val_ds, batch_size=64, shuffle=False)

    model = SceneClassifierMLP().to(device)
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    criterion = nn.CrossEntropyLoss()

    best_val_acc = 0.0
    patience_counter = 0

    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        for emb, labels, soft_labels, _ in train_loader:
            emb, soft_labels = emb.to(device), soft_labels.to(device)
            logits = model(emb)
            loss = -(soft_labels * torch.log_softmax(logits, dim=1)).sum(dim=1).mean()
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validate
        model.eval()
        correct = 0
        total = 0
        with torch.no_grad():
            for emb, labels, _, _ in val_loader:
                emb, labels = emb.to(device), labels.to(device)
                logits = model(emb)
                preds = logits.argmax(dim=1)
                correct += (preds == labels).sum().item()
                total += labels.size(0)

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


def load_scene_classifier(checkpoint_path: Path, device: str = "cpu") -> SceneClassifierMLP:
    """Load trained scene classifier for inference."""
    model = SceneClassifierMLP()
    model.load_state_dict(torch.load(checkpoint_path, map_location=device))
    model.eval()
    return model


def predict_scene_type(model: SceneClassifierMLP, clip_embedding: np.ndarray) -> dict:
    """Predict scene type from CLIP embedding."""
    with torch.no_grad():
        logits = model(torch.tensor(clip_embedding).unsqueeze(0))
        probs = torch.softmax(logits, dim=1).squeeze().numpy()
    top_idx = probs.argmax()
    return {
        "scene_type": SCENE_TYPES[top_idx],
        "confidence": float(probs[top_idx]),
        "scores": {st: float(p) for st, p in zip(SCENE_TYPES, probs)},
    }
