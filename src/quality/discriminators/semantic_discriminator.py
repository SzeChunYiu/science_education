"""Semantic discriminator: MLP cross-modal classifier for image-narration matching."""
import json
import logging
import random
from pathlib import Path
from typing import Union

import torch
import torch.nn as nn
from PIL import Image

logger = logging.getLogger(__name__)


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


class _SemanticMLP(nn.Module):
    """3-layer MLP for cross-modal semantic matching.

    Input: 512-dim CLIP image embedding + 384-dim sentence-transformer text embedding = 896-dim.
    Output: sigmoid match score 0-1.
    """

    def __init__(self, input_dim: int = 896, hidden_dim: int = 512):
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


class SemanticDiscriminator:
    """Cross-modal classifier scoring image-narration semantic alignment.

    Uses CLIP for image encoding (512-dim) and sentence-transformers for
    text encoding (384-dim). Combined 896-dim input fed through 3-layer MLP.

    Training data types:
    - Positive: real keyframe + aligned narration sentence
    - Negative type 1: same frame + different scene narration (same video)
    - Negative type 2: same frame + different video narration
    - Negative type 3: same frame + adjacent scene narration (hardest)
    """

    def __init__(self, checkpoint_path: Union[str, Path, None] = None, device: str = "auto"):
        self.device = _get_device(device)
        self.model = None
        self._clip_model = None
        self._clip_processor = None
        self._sentence_model = None
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

    def _ensure_sentence_model(self):
        """Lazy-load sentence-transformer model."""
        if self._sentence_model is None:
            from sentence_transformers import SentenceTransformer

            logger.info("Loading sentence-transformer model (lazy)...")
            self._sentence_model = SentenceTransformer("all-MiniLM-L6-v2", device=str(self.device))

    @torch.no_grad()
    def _encode_image(self, image: Image.Image) -> torch.Tensor:
        """Encode image to 512-dim CLIP embedding."""
        self._ensure_clip()
        inputs = self._clip_processor(images=image, return_tensors="pt").to(self.device)
        features = self._clip_model.get_image_features(**inputs)
        features = features / features.norm(dim=-1, keepdim=True)
        return features.squeeze(0)  # (512,)

    @torch.no_grad()
    def _encode_text(self, text: str) -> torch.Tensor:
        """Encode text to 384-dim sentence-transformer embedding."""
        self._ensure_sentence_model()
        embedding = self._sentence_model.encode(text, convert_to_tensor=True)
        if embedding.device != self.device:
            embedding = embedding.to(self.device)
        return embedding  # (384,)

    def _build_model(self) -> _SemanticMLP:
        """Build the 3-layer MLP."""
        return _SemanticMLP(input_dim=896, hidden_dim=512)

    def _load_model(self, checkpoint_path: Union[str, Path]):
        """Load MLP from checkpoint."""
        self.model = self._build_model()
        state_dict = torch.load(str(checkpoint_path), map_location=self.device, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Loaded semantic discriminator from {checkpoint_path}")

    @torch.no_grad()
    def score(self, image: Union[Image.Image, Path, str], narration_text: str) -> float:
        """Returns 0.0-1.0 semantic match score between image and narration.

        Args:
            image: PIL Image or path to image file.
            narration_text: Narration sentence to match against image.

        Returns:
            Float match score (higher = better match).
        """
        if self.model is None:
            raise RuntimeError("No model loaded. Provide checkpoint_path or call train() first.")

        self.model.eval()
        img = _load_image(image)
        img_emb = self._encode_image(img)
        txt_emb = self._encode_text(narration_text)
        combined = torch.cat([img_emb, txt_emb], dim=0).unsqueeze(0)
        logit = self.model(combined)
        return torch.sigmoid(logit).item()

    def train(
        self,
        dataset_path: Union[str, Path],
        output_path: Union[str, Path],
        epochs: int = 50,
        batch_size: int = 64,
        lr: float = 1e-3,
        val_split: float = 0.15,
        patience: int = 10,
        hard_negative_ratio: float = 0.3,
    ):
        """Train semantic discriminator with hard negative mining.

        Args:
            dataset_path: Path to JSONL file with fields:
                image_embedding (list[float]), text_embedding (list[float]), label (0 or 1)
            output_path: Where to save best checkpoint.
            epochs: Maximum training epochs.
            batch_size: Training batch size.
            lr: Learning rate.
            val_split: Validation split ratio.
            patience: Early stopping patience (by AUC).
            hard_negative_ratio: Fraction of hard negatives to oversample.
        """
        from torch.utils.data import DataLoader, random_split

        self.model = self._build_model().to(self.device)

        dataset = _SemanticPairDataset(Path(dataset_path))
        val_size = int(len(dataset) * val_split)
        train_size = len(dataset) - val_size
        train_ds, val_ds = random_split(dataset, [train_size, val_size])

        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4)

        criterion = nn.BCEWithLogitsLoss()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=lr, weight_decay=0.01)
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        best_auc = 0.0
        no_improve = 0
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Track hard negatives for mining
        hard_negative_indices = []

        for epoch in range(epochs):
            # Build train loader with optional hard negative oversampling
            if hard_negative_indices and epoch > 0:
                train_indices = list(train_ds.indices)
                n_hard = int(len(train_indices) * hard_negative_ratio)
                oversample = random.choices(hard_negative_indices, k=min(n_hard, len(hard_negative_indices)))
                train_indices.extend(oversample)
                subset = torch.utils.data.Subset(dataset, train_indices)
                train_loader = DataLoader(subset, batch_size=batch_size, shuffle=True, num_workers=4)
            else:
                train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=4)

            # Train phase
            self.model.train()
            train_loss = 0.0
            epoch_hard_negatives = []

            for batch_features, batch_labels in train_loader:
                batch_features = batch_features.to(self.device)
                batch_labels = batch_labels.to(self.device).float()
                optimizer.zero_grad()
                logits = self.model(batch_features)
                loss = criterion(logits, batch_labels)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

                # Identify hard negatives: high confidence false negatives
                with torch.no_grad():
                    probs = torch.sigmoid(logits)
                    false_neg_mask = (batch_labels == 0) & (probs > 0.5)
                    if false_neg_mask.any():
                        # These are negatives the model thinks are positive
                        epoch_hard_negatives.extend(
                            probs[false_neg_mask].cpu().tolist()
                        )

            scheduler.step()

            # Update hard negative indices from training set
            hard_negative_indices = self._find_hard_negatives(dataset, train_ds.indices)

            # Validation phase
            val_auc = self._evaluate_auc(val_loader)
            avg_loss = train_loss / max(len(train_loader), 1)
            logger.info(
                f"Epoch {epoch+1}/{epochs} - loss: {avg_loss:.4f} - "
                f"val_auc: {val_auc:.4f} - hard_negs: {len(hard_negative_indices)}"
            )

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
    def _find_hard_negatives(self, dataset, train_indices: list) -> list:
        """Find negative samples that the model scores highly (hard negatives)."""
        self.model.eval()
        hard_indices = []
        for idx in train_indices:
            features, label = dataset[idx]
            if label == 1:
                continue  # Only look at negatives
            features = features.unsqueeze(0).to(self.device)
            logit = self.model(features)
            prob = torch.sigmoid(logit).item()
            if prob > 0.4:  # Model thinks this negative might be positive
                hard_indices.append(idx)
        return hard_indices

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

        # Simple AUC approximation via trapezoidal rule
        return _compute_auc(all_labels, all_probs)


class _SemanticPairDataset(torch.utils.data.Dataset):
    """Dataset of pre-computed embedding pairs from JSONL file.

    Each line: {"image_embedding": [...], "text_embedding": [...], "label": 0/1}
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
        img_emb = torch.tensor(s["image_embedding"], dtype=torch.float32)
        txt_emb = torch.tensor(s["text_embedding"], dtype=torch.float32)
        features = torch.cat([img_emb, txt_emb], dim=0)  # (896,)
        label = s["label"]
        return features, label


def _compute_auc(labels: list, scores: list) -> float:
    """Compute AUC-ROC via trapezoidal approximation."""
    if not labels or len(set(labels)) < 2:
        return 0.5

    # Sort by score descending
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
