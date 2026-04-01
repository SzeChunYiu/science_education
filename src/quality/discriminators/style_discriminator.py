"""Style discriminator: ViT-Small binary classifier for TED-Ed style detection."""
import logging
from pathlib import Path
from typing import Union

import torch
import torch.nn as nn
from PIL import Image
from torchvision import transforms

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


class StyleDiscriminator:
    """ViT-Small fine-tuned as binary classifier (TED-Ed vs non-TED-Ed).

    Architecture: WinKawaks/vit-small-patch16-224 with last 2 transformer
    blocks unfrozen + replaced classification head Linear(384, 2).
    """

    def __init__(self, checkpoint_path: Union[str, Path, None] = None, device: str = "auto"):
        self.device = _get_device(device)
        self.model = None
        self.transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])
        if checkpoint_path is not None:
            self._load_model(checkpoint_path)

    def _build_model(self) -> nn.Module:
        """Build ViT-Small with frozen early layers and replaced head."""
        from transformers import ViTModel

        vit = ViTModel.from_pretrained("WinKawaks/vit-small-patch16-224")

        # Freeze all parameters first
        for param in vit.parameters():
            param.requires_grad = False

        # Unfreeze last 2 transformer blocks
        for block in vit.encoder.layer[-2:]:
            for param in block.parameters():
                param.requires_grad = True

        # Unfreeze layernorm
        if hasattr(vit, "layernorm"):
            for param in vit.layernorm.parameters():
                param.requires_grad = True

        # Build classifier wrapper
        model = _ViTClassifier(vit, hidden_size=384, num_classes=2)
        return model

    def _load_model(self, checkpoint_path: Union[str, Path]):
        """Load model from checkpoint."""
        self.model = self._build_model()
        state_dict = torch.load(str(checkpoint_path), map_location=self.device, weights_only=True)
        self.model.load_state_dict(state_dict)
        self.model.to(self.device)
        self.model.eval()
        logger.info(f"Loaded style discriminator from {checkpoint_path}")

    @torch.no_grad()
    def score(self, image: Union[Image.Image, Path, str]) -> float:
        """Returns 0.0-1.0 probability of being TED-Ed style.

        Args:
            image: PIL Image or path to image file.

        Returns:
            Float probability score.
        """
        if self.model is None:
            raise RuntimeError("No model loaded. Provide checkpoint_path or call train() first.")

        self.model.eval()
        img = _load_image(image)
        tensor = self.transform(img).unsqueeze(0).to(self.device)
        logits = self.model(tensor)
        probs = torch.softmax(logits, dim=1)
        return probs[0, 1].item()  # Positive class probability

    def train(
        self,
        dataset_path: Union[str, Path],
        output_path: Union[str, Path],
        epochs: int = 30,
        batch_size: int = 32,
        lr: float = 1e-4,
        val_split: float = 0.15,
        patience: int = 7,
    ):
        """Train style discriminator with balanced sampling and early stopping.

        Args:
            dataset_path: Path to .pt file containing {'images': tensor, 'labels': tensor}
                or directory with pos/ and neg/ subdirectories.
            output_path: Where to save best checkpoint.
            epochs: Maximum training epochs.
            batch_size: Training batch size.
            lr: Learning rate.
            val_split: Validation split ratio.
            patience: Early stopping patience (by validation F1).
        """
        from torch.utils.data import DataLoader, WeightedRandomSampler, random_split

        self.model = self._build_model().to(self.device)

        dataset_path = Path(dataset_path)
        if dataset_path.suffix == ".pt":
            dataset = _TensorStyleDataset(dataset_path, self.transform)
        else:
            dataset = _DirectoryStyleDataset(dataset_path, self.transform)

        # Train/val split
        val_size = int(len(dataset) * val_split)
        train_size = len(dataset) - val_size
        train_ds, val_ds = random_split(dataset, [train_size, val_size])

        # Balanced sampling for training
        train_labels = [dataset.get_label(i) for i in train_ds.indices]
        class_counts = [train_labels.count(c) for c in range(2)]
        weights = [1.0 / class_counts[l] for l in train_labels]
        sampler = WeightedRandomSampler(weights, len(weights), replacement=True)

        train_loader = DataLoader(train_ds, batch_size=batch_size, sampler=sampler, num_workers=4)
        val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=4)

        # Weighted loss
        class_weights = torch.tensor(
            [len(dataset) / (2 * max(c, 1)) for c in class_counts],
            dtype=torch.float32,
        ).to(self.device)
        criterion = nn.CrossEntropyLoss(weight=class_weights)

        # Only optimize unfrozen params
        optimizer = torch.optim.AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()), lr=lr, weight_decay=0.01
        )
        scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

        best_f1 = 0.0
        no_improve = 0
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Augmentation for training
        aug_transform = transforms.Compose([
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2, hue=0.05),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ])

        for epoch in range(epochs):
            # Train phase
            self.model.train()
            train_loss = 0.0
            for batch_imgs, batch_labels in train_loader:
                batch_imgs = batch_imgs.to(self.device)
                batch_labels = batch_labels.to(self.device)
                optimizer.zero_grad()
                logits = self.model(batch_imgs)
                loss = criterion(logits, batch_labels)
                loss.backward()
                optimizer.step()
                train_loss += loss.item()

            scheduler.step()

            # Validation phase
            val_f1 = self._evaluate(val_loader)
            avg_loss = train_loss / max(len(train_loader), 1)
            logger.info(f"Epoch {epoch+1}/{epochs} - loss: {avg_loss:.4f} - val_f1: {val_f1:.4f}")

            if val_f1 > best_f1:
                best_f1 = val_f1
                torch.save(self.model.state_dict(), str(output_path))
                no_improve = 0
                logger.info(f"  New best F1: {best_f1:.4f} - saved to {output_path}")
            else:
                no_improve += 1
                if no_improve >= patience:
                    logger.info(f"Early stopping at epoch {epoch+1}")
                    break

        # Reload best
        self._load_model(output_path)
        logger.info(f"Training complete. Best val F1: {best_f1:.4f}")

    @torch.no_grad()
    def _evaluate(self, loader) -> float:
        """Evaluate model on a dataloader, return F1 score."""
        self.model.eval()
        all_preds = []
        all_labels = []
        for imgs, labels in loader:
            imgs = imgs.to(self.device)
            logits = self.model(imgs)
            preds = logits.argmax(dim=1).cpu()
            all_preds.extend(preds.tolist())
            all_labels.extend(labels.tolist())

        # Calculate F1 for positive class
        tp = sum(1 for p, l in zip(all_preds, all_labels) if p == 1 and l == 1)
        fp = sum(1 for p, l in zip(all_preds, all_labels) if p == 1 and l == 0)
        fn = sum(1 for p, l in zip(all_preds, all_labels) if p == 0 and l == 1)
        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 1e-8)
        return f1


class _ViTClassifier(nn.Module):
    """Wrapper combining ViT backbone with classification head."""

    def __init__(self, vit: nn.Module, hidden_size: int = 384, num_classes: int = 2):
        super().__init__()
        self.vit = vit
        self.classifier = nn.Linear(hidden_size, num_classes)

    def forward(self, pixel_values: torch.Tensor) -> torch.Tensor:
        outputs = self.vit(pixel_values=pixel_values)
        cls_token = outputs.last_hidden_state[:, 0]  # CLS token
        return self.classifier(cls_token)


class _TensorStyleDataset(torch.utils.data.Dataset):
    """Dataset from a .pt file with images and labels tensors."""

    def __init__(self, pt_path: Path, transform=None):
        data = torch.load(str(pt_path), weights_only=True)
        self.images = data["images"]  # List of image paths or tensors
        self.labels = data["labels"]
        self.transform = transform

    def __len__(self):
        return len(self.labels)

    def get_label(self, idx):
        return int(self.labels[idx])

    def __getitem__(self, idx):
        img = self.images[idx]
        label = int(self.labels[idx])
        if isinstance(img, (str, Path)):
            img = Image.open(img).convert("RGB")
        if isinstance(img, Image.Image) and self.transform:
            img = self.transform(img)
        return img, label


class _DirectoryStyleDataset(torch.utils.data.Dataset):
    """Dataset from directory with pos/ and neg/ subdirectories."""

    def __init__(self, root: Path, transform=None):
        self.transform = transform
        self.samples = []
        pos_dir = root / "pos"
        neg_dir = root / "neg"
        if pos_dir.exists():
            for p in sorted(pos_dir.glob("*.png")) + sorted(pos_dir.glob("*.jpg")):
                self.samples.append((p, 1))
        if neg_dir.exists():
            for p in sorted(neg_dir.glob("*.png")) + sorted(neg_dir.glob("*.jpg")):
                self.samples.append((p, 0))

    def __len__(self):
        return len(self.samples)

    def get_label(self, idx):
        return self.samples[idx][1]

    def __getitem__(self, idx):
        path, label = self.samples[idx]
        img = Image.open(path).convert("RGB")
        if self.transform:
            img = self.transform(img)
        return img, label
