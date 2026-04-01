"""Flow discriminator: MLP for narrative flow coherence between consecutive scenes."""
import json
import logging
from pathlib import Path
from typing import Union

import torch
import torch.nn as nn
from PIL import Image

logger = logging.getLogger(__name__)

TRANSITION_TYPES = ["cut", "dissolve", "fade"]


def _get_device(preferred: str = "auto") -> torch.device:
    """Auto-detect best available device."""
    if preferred != "auto":
        return torch.device(preferred)
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _load_image(image: Union[Image.Image, Path, str]) -> Image.Image:
    """Load image from PIL Image or file path."""
    if isinstance(image, (str, Path)):
        image = Image.open(image).convert("RGB")
    elif isinstance(image, Image.Image):
        image = image.convert("RGB")
    return image


def _transition_one_hot(transition_type: str) -> torch.Tensor:
    """Convert transition type string to 3-dim one-hot tensor."""
    idx = TRANSITION_TYPES.index(transition_type) if transition_type in TRANSITION_TYPES else 0
    one_hot = torch.zeros(len(TRANSITION_TYPES))
    one_hot[idx] = 1.0
    return one_hot


class _FlowMLP(nn.Module):
    """3-layer MLP for narrative flow scoring.

    Input: 512-dim CLIP(frame_A) + 512-dim CLIP(frame_B) + 3-dim transition one-hot = 1027-dim.
    Output: sigmoid flow coherence score 0-1.
    """

    def __init__(self, input_dim: int = 1027, hidden_dim: int = 512):
        super().__init__()
        self.net = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(hidden_dim, hidden_dim // 2),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(hidden_dim // 2, 1),
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.net(x).squeeze(-1)


class FlowDiscriminator:
    """Narrative flow discriminator for consecutive scene coherence.

    Scores whether two consecutive scenes form a natural visual narrative flow.
    Uses CLIP embeddings of the last frame of scene N and first frame of scene N+1,
    plus the transition type between them.

    Training data:
    - Positive: real consecutive scene pairs from TED-Ed
    - Negative: shuffled same-video pairs (2x oversample), cross-video pairs,
                cross-channel pairs
    """

    def __init__(self, checkpoint_path: Union[str, Path, None] = None, device: str = "auto"):
        self.device = _get_device(device)
        self.model = None
        self._clip_model = None
        self._clip_processor = None
        if checkpoint_path is not None:
            self._load_model(checkpoint_path)

    def _ensure_clip(self):
        """Lazy-load CLIP model."""
        if self._clip_model is None:
            from transformers import CLIPModel, CLIPProcessor

            logger.info("Loading CLIP model (lazy)...")
            self._clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
            self._clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(self.device)
            self._clip_model.eval()

    @torch.no_grad()
    def _encode_image(self, image: Image.Image) -> torch.Tensor:
        """Encode image to 512-dim CLIP embedding."""
        self._ensure_clip()
        inputs = self._clip_processor(images=image, return_tensors="pt").to(self.device)
        features = self._clip_model.get_image_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze(0)  # (512,)

    def _build_model(self) -> _FlowMLP:
        """Build the 3-layer MLP."""
        return _FlowMLP(input_dim=1027, hidden_dim=512)

    def _load_model(self, checkpoint_path: Union[str, Path]):
        """Load MLP from checkpoint."""
        self.model = self._build_model()
        state_dict = torch.load(str(checkpoint_path), map_location=self.device, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Loaded flow discriminator from {checkpoint_path}")

    @torch.no_grad()
    def score(
        self,
        frame_a: Union[Image.Image, Path, str],
        frame_b: Union[Image.Image, Path, str],
        transition_type: str = "cut",
    ) -> float:
        """Returns 0.0-1.0 flow coherence score between two consecutive frames.

        Args:
            frame_a: Last frame of scene N (PIL Image or path).
            frame_b: First frame of scene N+1 (PIL Image or path).
            transition_type: One of 'cut', 'dissolve', 'fade'.

        Returns:
            Float coherence score (higher = more natural flow).
        """
        if self.model is None:
            raise RuntimeError("No model loaded. Provide checkpoint_path or call train() first.")

        self.model.eval()
        img_a = _load_image(frame_a)
        img_b = _load_image(frame_b)
        emb_a = self._encode_image(img_a)
        emb_b = self._encode_image(img_b)
        trans = _transition_one_hot(transition_type).to(self.device)
        combined = torch.cat([emb_a, emb_b, trans], dim=0).unsqueeze(0)
        logit = self.model(combined)
        return torch.sigmoid(logit).item()

    @torch.no_grad()
    def check_episode_flow(
        self,
        scene_frames: list[Union[Image.Image, Path, str]],
        transitions: list[str],
    ) -> list[dict]:
        """Sliding window flow check across a full episode.

        Args:
            scene_frames: List of representative frames per scene (one per scene).
            transitions: List of transition types between consecutive scenes.
                Must have len(scene_frames) - 1 elements.

        Returns:
            List of dicts with keys: scene_pair, transition, score, flagged.
        """
        if len(transitions) != len(scene_frames) - 1:
            raise ValueError(
                f"Expected {len(scene_frames)-1} transitions, got {len(transitions)}"
            )

        results = []
        for i in range(len(scene_frames) - 1):
            s = self.score(scene_frames[i], scene_frames[i + 1], transitions[i])
            results.append({
                "scene_pair": (i, i + 1),
                "transition": transitions[i],
                "score": round(s, 4),
                "flagged": s < 0.5,
            })
        return results

    def train(
        self,
        dataset_path: Union[str, Path],
        output_path: Union[str, Path],
        epochs: int = 50,
        batch_size: int = 64,
        lr: float = 1e-3,
        val_split: float = 0.15,
        patience: int = 10,
    ):
        """Train flow discriminator.

        Args:
            dataset_path: Path to JSONL file with fields:
                emb_a (list[float]), emb_b (list[float]), transition (str), label (0/1)
            output_path: Where to save best checkpoint.
            epochs: Maximum training epochs.
            batch_size: Training batch size.
            lr: Learning rate.
            val_split: Validation split ratio.
            patience: Early stopping patience (by AUC).
        """
        from torch.utils.data import DataLoader, random_split

        self.model = self._build_model().to(self.device)

        dataset = _FlowPairDataset(Path(dataset_path))
        val_size = int(len(dataset) * val_split)
        train_size = len(dataset) - val_size
        train_ds, val_ds = random_split(dataset, [train_size, val_size])

        train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4)

        criterion = nn.BCEWithLogitsLoss()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=0.01)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        best_auc = 0.0
        no_improve = 0
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        for epoch in range(epochs):
            # Train phase
            self.model.train()
            train_loss = 0.0
            for batch_features, batch_labels in train_loader:
                batch_features = batch_features.to(self.device)
                batch_labels = batch_labels.to(self.device).float()
                optimizer.zero_grad()
                logits = self.model(batch_features)
                loss = criterion(logits, batch_labels)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            scheduler.step()

            # Validation phase
            val_auc = self._evaluate_auc(val_loader)
            avg_loss = train_loss / max(len(train_loader), 1)
            logger.info(f"Epoch {epoch+1}/{epochs} - loss: {avg_loss:.4f} - val_auc: {val_auc:.4f}")

            if val_auc > best_auc:
                best_auc = val_auc
                torch.save(self.model.state_dict(), str(output_path))
                no_improve = 0
                logger.info(f"  New best AUC: {best_auc:.4f} - saved to {output_path}")
            else:
                no_improve += 1
                if no_improve >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break

        # Reload best
        self._load_model(output_path)
        logger.info(f"Training complete. Best val AUC: {best_auc:.4f}")

    @torch.no_grad()
    def _evaluate_auc(self, loader) -> float:
        """Evaluate model on a dataloader, return AUC score."""
        self.model.eval()
        all_probs = []
        all_labels = []
        for features, labels in loader:
            features = features.to(self.device)
            logits = self.model(features)
            probs = torch.sigmoid(logits).cpu()
            all_probs.extend(probs.tolist())
            all_labels.extend(labels.tolist())
        return _compute_auc(all_labels, all_probs)


class _FlowPairDataset(torch.utils.data.Dataset):
    """Dataset of pre-computed flow pairs from JSONL file.

    Each line: {"emb_a": [...], "emb_b": [...], "transition": "cut", "label": 0/1}
    """

    def __init__(self, jsonl_path: Path):
        self.samples = []
        with open(jsonl_path) as f:
            for line in f:
                if line.strip():
                    self.samples.append(json.loads(line))

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        s = self.samples[idx]
        emb_a = torch.tensor(s["emb_a"], dtype=torch.float32)
        emb_b = torch.tensor(s["emb_b"], dtype=torch.float32)
        trans = _transition_one_hot(s.get("transition", "cut"))
        features = torch.cat([emb_a, emb_b, trans], dim=0)  # (1027,)
        label = s["label"]
        return features, label


def _compute_auc(labels: list, scores: list) -> float:
    """Compute AUC-ROC via trapezoidal approximation."""
    if not labels or len(set(labels)) < 2:
        return 0.5

    pairs = sorted(zip(scores, labels), key=lambda x: -x[0])
    n_pos = sum(labels)
    n_neg = len(labels) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5

    tp = 0
    fp = 0
    auc = 0.0
    prev_fpr = 0.0

    for score, label in pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
            tpr = tp / n_pos
            fpr = fp / n_neg
            auc += tpr * (fpr - prev_fpr)
            prev_fpr = fpr

    return auc
