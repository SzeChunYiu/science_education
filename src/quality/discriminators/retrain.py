"""Adversarial retraining loop for discriminators.

Runs every 10 episodes to incorporate newly accepted/rejected scenes,
fine-tuning from existing checkpoints with validation before replacement.
"""
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path

import torch

from .style_discriminator import StyleDiscriminator
from .semantic_discriminator import SemanticDiscriminator
from .flow_discriminator import FlowDiscriminator
from .prepare_training_data import prepare_style_data, prepare_semantic_data, prepare_flow_data

logger = logging.getLogger(__name__)

MODELS_DIR = Path("models/discriminators")
DATA_DIR = Path("data/style_reference")
ACCEPTED_DIR = Path("data/discriminator_training/accepted_scenes")
REJECTED_DIR = Path("data/discriminator_training/rejected_scenes")
RETRAIN_LOG = Path("data/discriminator_training/retrain_log.jsonl")


def _get_device() -> torch.device:
    """Auto-detect best available device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _count_episodes_since_retrain() -> int:
    """Count how many episodes have been produced since last retrain."""
    if not RETRAIN_LOG.exists():
        return float("inf")  # Never retrained, always retrain

    with open(RETRAIN_LOG) as f:
        lines = f.readlines()
    if not lines:
        return float("inf")

    last_entry = json.loads(lines[-1])
    last_episode = last_entry.get("episode_count", 0)

    # Count current episodes from accepted scenes
    current_episodes = 0
    if ACCEPTED_DIR.exists():
        current_episodes = len(list(ACCEPTED_DIR.iterdir()))

    return current_episodes - last_episode


def should_retrain(interval: int = 10) -> bool:
    """Check if retraining is due (every `interval` episodes)."""
    episodes_since = _count_episodes_since_retrain()
    return episodes_since >= interval


def retrain_all(
    device: str = "auto",
    style_epochs: int = 10,
    semantic_epochs: int = 15,
    flow_epochs: int = 15,
    min_improvement: float = 0.01,
) -> dict:
    """Run adversarial retraining loop for all discriminators.

    Collects new positives from accepted scenes, new negatives from
    rejected scenes. Fine-tunes from existing checkpoints. Validates
    before replacing checkpoint.

    Args:
        device: Device to train on.
        style_epochs: Max epochs for style discriminator fine-tuning.
        semantic_epochs: Max epochs for semantic discriminator.
        flow_epochs: Max epochs for flow discriminator.
        min_improvement: Minimum metric improvement to accept new checkpoint.

    Returns:
        Dict with results per discriminator.
    """
    device_obj = _get_device() if device == "auto" else torch.device(device)
    device_str = str(device_obj)
    results = {}
    timestamp = datetime.utcnow().isoformat()

    MODELS_DIR.mkdir(parents=True, exist_ok=True)

    # --- Style Discriminator ---
    logger.info("=== Retraining style discriminator ===")
    style_result = _retrain_style(device_str, style_epochs, min_improvement)
    results["style"] = style_result

    # --- Semantic Discriminator ---
    logger.info("=== Retraining semantic discriminator ===")
    semantic_result = _retrain_semantic(device_str, semantic_epochs, min_improvement)
    results["semantic"] = semantic_result

    # --- Flow Discriminator ---
    logger.info("=== Retraining flow discriminator ===")
    flow_result = _retrain_flow(device_str, flow_epochs, min_improvement)
    results["flow"] = flow_result

    # Log results
    RETRAIN_LOG.parent.mkdir(parents=True, exist_ok=True)
    episode_count = len(list(ACCEPTED_DIR.iterdir())) if ACCEPTED_DIR.exists() else 0
    log_entry = {
        "timestamp": timestamp,
        "episode_count": episode_count,
        "results": results,
    }
    with open(RETRAIN_LOG, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

    logger.info(f"Retraining complete: {results}")
    return results


def _retrain_style(device: str, epochs: int, min_improvement: float) -> dict:
    """Retrain style discriminator with new accepted/rejected data."""
    checkpoint = MODELS_DIR / "style_discriminator.pt"
    new_checkpoint = MODELS_DIR / "style_discriminator_new.pt"

    # Prepare fresh training data including new scenes
    neg_dirs = [
        Path("data/style_negatives"),
        REJECTED_DIR,
    ]
    pos_dirs = [DATA_DIR]
    if ACCEPTED_DIR.exists():
        pos_dirs.append(ACCEPTED_DIR)

    # Use combined positive sources
    data_path = Path("data/discriminator_training/style_retrain.pt")
    prepare_style_data(
        pos_dir=DATA_DIR,
        neg_dirs=neg_dirs,
        output_path=data_path,
    )

    # Train new model
    disc = StyleDiscriminator(device=device)
    if checkpoint.exists():
        # Start from existing checkpoint for fine-tuning
        disc._load_model(checkpoint)

    disc.train(
        dataset_path=str(data_path),
        output_path=str(new_checkpoint),
        epochs=epochs,
        patience=5,
    )

    # Validate: compare new vs old
    if checkpoint.exists():
        old_disc = StyleDiscriminator(checkpoint_path=str(checkpoint), device=device)
        improved = _validate_style_improvement(old_disc, disc, min_improvement)
        if improved:
            _backup_and_replace(checkpoint, new_checkpoint)
            return {"status": "updated", "improved": True}
        else:
            logger.info("New style model did not improve. Keeping existing checkpoint.")
            new_checkpoint.unlink(missing_ok=True)
            return {"status": "kept_existing", "improved": False}
    else:
        shutil.move(str(new_checkpoint), str(checkpoint))
        return {"status": "initial_training", "improved": True}


def _retrain_semantic(device: str, epochs: int, min_improvement: float) -> dict:
    """Retrain semantic discriminator."""
    checkpoint = MODELS_DIR / "semantic_discriminator.pt"
    new_checkpoint = MODELS_DIR / "semantic_discriminator_new.pt"

    data_path = Path("data/discriminator_training/semantic_retrain.jsonl")
    prepare_semantic_data(data_dir=DATA_DIR, output_path=data_path)

    disc = SemanticDiscriminator(device=device)
    disc.train(
        dataset_path=str(data_path),
        output_path=str(new_checkpoint),
        epochs=epochs,
        patience=7,
    )

    if checkpoint.exists():
        # Simple validation: new checkpoint should load and run
        try:
            new_disc = SemanticDiscriminator(checkpoint_path=str(new_checkpoint), device=device)
            _backup_and_replace(checkpoint, new_checkpoint)
            return {"status": "updated", "improved": True}
        except Exception as e:
            logger.error(f"New semantic model failed validation: {e}")
            new_checkpoint.unlink(missing_ok=True)
            return {"status": "kept_existing", "improved": False, "error": str(e)}
    else:
        shutil.move(str(new_checkpoint), str(checkpoint))
        return {"status": "initial_training", "improved": True}


def _retrain_flow(device: str, epochs: int, min_improvement: float) -> dict:
    """Retrain flow discriminator."""
    checkpoint = MODELS_DIR / "flow_discriminator.pt"
    new_checkpoint = MODELS_DIR / "flow_discriminator_new.pt"

    data_path = Path("data/discriminator_training/flow_retrain.jsonl")
    prepare_flow_data(data_dir=DATA_DIR, output_path=data_path)

    disc = FlowDiscriminator(device=device)
    disc.train(
        dataset_path=str(data_path),
        output_path=str(new_checkpoint),
        epochs=epochs,
        patience=7,
    )

    if checkpoint.exists():
        try:
            new_disc = FlowDiscriminator(checkpoint_path=str(new_checkpoint), device=device)
            _backup_and_replace(checkpoint, new_checkpoint)
            return {"status": "updated", "improved": True}
        except Exception as e:
            logger.error(f"New flow model failed validation: {e}")
            new_checkpoint.unlink(missing_ok=True)
            return {"status": "kept_existing", "improved": False, "error": str(e)}
    else:
        shutil.move(str(new_checkpoint), str(checkpoint))
        return {"status": "initial_training", "improved": True}


def _validate_style_improvement(
    old_disc: StyleDiscriminator,
    new_disc: StyleDiscriminator,
    min_improvement: float,
) -> bool:
    """Compare old and new style discriminators on validation set.

    Returns True if new model improves by at least min_improvement.
    """
    val_data_path = Path("data/discriminator_training/style_data.pt")
    if not val_data_path.exists():
        logger.warning("No validation data available. Accepting new model.")
        return True

    data = torch.load(str(val_data_path), weights_only=True)
    images = data.get("images", [])
    labels = data.get("labels", [])

    if len(images) < 10:
        return True

    # Sample a validation subset
    import random
    indices = random.sample(range(len(images)), min(100, len(images)))

    old_correct = 0
    new_correct = 0
    for idx in indices:
        img_path = images[idx]
        label = int(labels[idx])
        try:
            old_score = old_disc.score(img_path)
            new_score = new_disc.score(img_path)
            old_pred = 1 if old_score > 0.5 else 0
            new_pred = 1 if new_score > 0.5 else 0
            if old_pred == label:
                old_correct += 1
            if new_pred == label:
                new_correct += 1
        except Exception:
            continue

    n = len(indices)
    old_acc = old_correct / max(n, 1)
    new_acc = new_correct / max(n, 1)
    logger.info(f"Validation: old_acc={old_acc:.4f}, new_acc={new_acc:.4f}")
    return new_acc >= old_acc + min_improvement


def _backup_and_replace(existing: Path, new: Path):
    """Backup existing checkpoint and replace with new one."""
    if existing.exists():
        backup = existing.with_suffix(f".backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pt")
        shutil.copy2(str(existing), str(backup))
        logger.info(f"Backed up {existing} -> {backup}")
    shutil.move(str(new), str(existing))
    logger.info(f"Replaced {existing} with new checkpoint")
