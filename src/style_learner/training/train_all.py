"""Orchestrator: train all 4 style models in sequence.

Usage:
    python -m src.style_learner.training.train_all
    python -m src.style_learner.training.train_all --test-mode
"""
import argparse
import logging
import time
from pathlib import Path

import torch

from src.style_learner.training.scene_classifier import train_scene_classifier
from src.style_learner.training.camera_predictor import train_camera_predictor
from src.style_learner.training.text_placement import train_text_placement
from src.style_learner.training.transition_predictor import train_transition_predictor

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parents[3]  # project root
DATA_DIR = BASE_DIR / "data" / "style_learner"
MODEL_DIR = BASE_DIR / "models" / "style_learner"


def detect_device() -> str:
    """Auto-detect best available device: cuda > mps > cpu."""
    if torch.cuda.is_available():
        device = "cuda"
    elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        device = "mps"
    else:
        device = "cpu"
    logger.info(f"Using device: {device}")
    return device


def main():
    parser = argparse.ArgumentParser(description="Train all style learner models")
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Quick validation run with reduced epochs",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Directory containing dataset.jsonl and splits.json",
    )
    parser.add_argument(
        "--model-dir",
        type=Path,
        default=MODEL_DIR,
        help="Directory to save model checkpoints",
    )
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="Device override (cuda/mps/cpu)",
    )
    args = parser.parse_args()

    device = args.device or detect_device()
    data_dir = args.data_dir
    model_dir = args.model_dir
    model_dir.mkdir(parents=True, exist_ok=True)

    epochs = 5 if args.test_mode else 100
    patience = 2 if args.test_mode else 10

    results = {}
    total_start = time.time()

    # --- 1. Scene Classifier ---
    logger.info("=" * 60)
    logger.info("Training Scene Classifier")
    logger.info("=" * 60)
    t0 = time.time()
    try:
        scene_acc = train_scene_classifier(
            dataset_path=data_dir / "scene_dataset.jsonl",
            splits_path=data_dir / "splits.json",
            output_path=model_dir / "scene_classifier.pt",
            epochs=epochs,
            patience=patience,
            device=device,
        )
        results["scene_classifier"] = {
            "status": "success",
            "metric": f"val_acc={scene_acc:.4f}",
            "time": f"{time.time() - t0:.1f}s",
        }
    except Exception as e:
        logger.error(f"Scene classifier training failed: {e}")
        results["scene_classifier"] = {"status": "failed", "error": str(e)}

    # --- 2. Camera Predictor ---
    logger.info("=" * 60)
    logger.info("Training Camera Predictor")
    logger.info("=" * 60)
    t0 = time.time()
    try:
        camera_acc = train_camera_predictor(
            dataset_path=data_dir / "camera_dataset.jsonl",
            splits_path=data_dir / "splits.json",
            output_path=model_dir / "camera_predictor.pt",
            epochs=epochs,
            patience=patience,
            device=device,
        )
        results["camera_predictor"] = {
            "status": "success",
            "metric": f"val_acc={camera_acc:.4f}",
            "time": f"{time.time() - t0:.1f}s",
        }
    except Exception as e:
        logger.error(f"Camera predictor training failed: {e}")
        results["camera_predictor"] = {"status": "failed", "error": str(e)}

    # --- 3. Text Placement ---
    logger.info("=" * 60)
    logger.info("Training Text Placement Predictor")
    logger.info("=" * 60)
    t0 = time.time()
    try:
        text_loss = train_text_placement(
            dataset_path=data_dir / "text_dataset.jsonl",
            splits_path=data_dir / "splits.json",
            output_path=model_dir / "text_placement.pt",
            epochs=epochs,
            patience=patience,
            device=device,
        )
        results["text_placement"] = {
            "status": "success",
            "metric": f"val_loss={text_loss:.4f}",
            "time": f"{time.time() - t0:.1f}s",
        }
    except Exception as e:
        logger.error(f"Text placement training failed: {e}")
        results["text_placement"] = {"status": "failed", "error": str(e)}

    # --- 4. Transition Predictor ---
    logger.info("=" * 60)
    logger.info("Training Transition Predictor")
    logger.info("=" * 60)
    t0 = time.time()
    try:
        trans_acc = train_transition_predictor(
            dataset_path=data_dir / "transition_dataset.jsonl",
            splits_path=data_dir / "splits.json",
            output_path=model_dir / "transition_predictor.pt",
            epochs=epochs,
            patience=patience,
            device=device,
        )
        results["transition_predictor"] = {
            "status": "success",
            "metric": f"val_acc={trans_acc:.4f}",
            "time": f"{time.time() - t0:.1f}s",
        }
    except Exception as e:
        logger.error(f"Transition predictor training failed: {e}")
        results["transition_predictor"] = {"status": "failed", "error": str(e)}

    # --- Summary ---
    total_time = time.time() - total_start
    logger.info("=" * 60)
    logger.info("TRAINING SUMMARY")
    logger.info("=" * 60)
    for name, info in results.items():
        status = info["status"]
        if status == "success":
            logger.info(f"  {name}: {info['metric']} ({info['time']})")
        else:
            logger.info(f"  {name}: FAILED - {info.get('error', 'unknown')}")
    logger.info(f"  Total time: {total_time:.1f}s")

    # Exit with error if any model failed
    failed = [n for n, r in results.items() if r["status"] == "failed"]
    if failed:
        logger.error(f"Failed models: {failed}")
        raise SystemExit(1)

    logger.info("All models trained successfully.")


if __name__ == "__main__":
    main()
