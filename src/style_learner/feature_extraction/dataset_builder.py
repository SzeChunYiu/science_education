"""Dataset builder: assembles all per-video features into dataset.jsonl.

Reads features, quality scores, scene boundaries, camera motion, text layout,
and narration alignment from each video directory and produces a single JSONL
file with one record per scene. Computes sample weights using quality-score
products with softmax normalization across all scenes.
"""

import json
import logging
import random
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)


def build_dataset(data_dir: Path) -> Path:
    """Assemble all video features into a unified dataset.jsonl.

    Reads all video subdirectories in data_dir, combines their extracted
    features into one JSON record per scene, and computes sample weights.

    Args:
        data_dir: Root data directory containing one subdirectory per video.
            Each video directory should contain:
                - features.json (CLIP embeddings + scene types)
                - scenes.json (scene boundaries)
                - quality_scores.json
                - camera_motion.json (optional)
                - text_layout.json (optional)
                - narration_alignment.json (optional)

    Returns:
        Path to the generated dataset.jsonl file.
    """
    video_dirs = sorted(
        d for d in data_dir.iterdir()
        if d.is_dir() and (d / "features.json").exists()
    )

    if not video_dirs:
        logger.error("No video directories with features.json found in %s", data_dir)
        return data_dir / "dataset.jsonl"

    logger.info("Building dataset from %d videos in %s", len(video_dirs), data_dir)

    all_records = []
    quality_products = []

    for video_dir in video_dirs:
        video_id = video_dir.name
        records = _process_video(video_dir, video_id)
        all_records.extend(records)

        # Collect quality product for weight computation
        quality = _load_json(video_dir / "quality_scores.json", {})
        composite = quality.get("composite", 0.5)
        quality_products.extend([composite] * len(records))

    # Compute sample weights via softmax over quality products
    if quality_products:
        qp = np.array(quality_products, dtype=np.float64)
        # Softmax with temperature scaling for smoother distribution
        temperature = 2.0
        qp_scaled = qp / temperature
        qp_exp = np.exp(qp_scaled - np.max(qp_scaled))  # subtract max for numerical stability
        weights = qp_exp / np.sum(qp_exp)

        for record, weight in zip(all_records, weights):
            record["sample_weight"] = round(float(weight), 8)
    else:
        for record in all_records:
            record["sample_weight"] = 1.0 / max(len(all_records), 1)

    # Write dataset.jsonl
    output_path = data_dir / "dataset.jsonl"
    with open(output_path, "w") as f:
        for record in all_records:
            f.write(json.dumps(record) + "\n")

    logger.info("Dataset written: %d records to %s", len(all_records), output_path)
    return output_path


def _process_video(video_dir: Path, video_id: str) -> list[dict]:
    """Process a single video directory into per-scene records."""
    features_data = _load_json(video_dir / "features.json", [])
    scenes_data = _load_json(video_dir / "scenes.json", [])
    quality_data = _load_json(video_dir / "quality_scores.json", {})
    camera_data = _load_json(video_dir / "camera_motion.json", [])
    text_data = _load_json(video_dir / "text_layout.json", [])
    narration_data = _load_json(video_dir / "narration_alignment.json", [])

    # If no explicit scene boundaries, treat each frame as a scene
    if not scenes_data:
        scenes_data = [
            {"scene_id": i, "start_frame": i, "end_frame": i, "start": 0, "end": 0}
            for i in range(len(features_data))
        ]

    # Index features by frame name for lookup
    features_by_frame = {f["frame"]: f for f in features_data}

    # Index auxiliary data by scene_id
    camera_by_scene = {c.get("scene_id", i): c for i, c in enumerate(camera_data)}
    text_by_scene = {t.get("scene_id", i): t for i, t in enumerate(text_data)}
    narration_by_scene = {n.get("scene_id", i): n for i, n in enumerate(narration_data)}

    records = []
    for scene_idx, scene in enumerate(scenes_data):
        scene_id = scene.get("scene_id", scene_idx)

        # Get representative frame embedding (middle frame of scene)
        start_frame = scene.get("start_frame", 0)
        end_frame = scene.get("end_frame", start_frame)
        mid_frame = (start_frame + end_frame) // 2

        # Find the feature entry closest to mid_frame
        embedding = None
        scene_type = None
        if features_data:
            # Try exact match first, then closest by index
            if mid_frame < len(features_data):
                feat = features_data[mid_frame]
            else:
                feat = features_data[min(mid_frame, len(features_data) - 1)]
            embedding = feat.get("embedding")
            scene_type = feat.get("scene_type", {})

        record = {
            "video_id": video_id,
            "scene_id": scene_id,
            "start": scene.get("start", 0),
            "end": scene.get("end", 0),
            "start_frame": start_frame,
            "end_frame": end_frame,
            "clip_embedding": embedding,
            "scene_type": scene_type,
            "quality": quality_data,
        }

        # Camera motion
        if scene_id in camera_by_scene:
            cm = camera_by_scene[scene_id]
            record["camera_motion"] = {
                "motion": cm.get("motion", "static"),
                "magnitude": cm.get("magnitude", "slow"),
                "confidence": cm.get("confidence", 0.0),
            }

        # Text layout
        if scene_id in text_by_scene:
            record["text_layout"] = text_by_scene[scene_id]

        # Narration alignment
        if scene_id in narration_by_scene:
            narr = narration_by_scene[scene_id]
            record["narration"] = {
                "sentences": narr.get("sentences", []),
                "wpm": narr.get("wpm", 0),
                "phase": narr.get("narration_phase", "explaining"),
            }

        records.append(record)

    logger.debug("Processed %d scenes from video %s", len(records), video_id)
    return records


def _load_json(path: Path, default):
    """Load JSON file, returning default if not found or invalid."""
    if not path.exists():
        return default
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning("Failed to load %s: %s", path, e)
        return default


def split_dataset(
    dataset_path: Path,
    train: float = 0.8,
    val: float = 0.1,
    test: float = 0.1,
) -> dict:
    """Split dataset by video_id (not by scene) into train/val/test.

    Args:
        dataset_path: Path to dataset.jsonl.
        train: Fraction for training split.
        val: Fraction for validation split.
        test: Fraction for test split.

    Returns:
        Dict with keys 'train', 'val', 'test', each mapping to a list of
        video_ids. Also saves splits.json alongside dataset.jsonl.
    """
    assert abs(train + val + test - 1.0) < 1e-6, "Split fractions must sum to 1.0"

    # Collect unique video IDs
    video_ids = set()
    with open(dataset_path) as f:
        for line in f:
            if line.strip():
                record = json.loads(line)
                video_ids.add(record["video_id"])

    video_ids = sorted(video_ids)
    random.seed(42)
    random.shuffle(video_ids)

    n = len(video_ids)
    n_train = int(n * train)
    n_val = int(n * val)

    splits = {
        "train": video_ids[:n_train],
        "val": video_ids[n_train : n_train + n_val],
        "test": video_ids[n_train + n_val :],
    }

    # Save splits
    splits_path = dataset_path.parent / "splits.json"
    with open(splits_path, "w") as f:
        json.dump(splits, f, indent=2)

    logger.info(
        "Dataset split: train=%d, val=%d, test=%d videos",
        len(splits["train"]),
        len(splits["val"]),
        len(splits["test"]),
    )
    return splits


def generate_report(dataset_path: Path, splits: dict) -> str:
    """Generate a statistics report for the dataset.

    Args:
        dataset_path: Path to dataset.jsonl.
        splits: Dict from split_dataset with train/val/test video_id lists.

    Returns:
        Formatted report string with dataset statistics.
    """
    # Load all records
    records = []
    with open(dataset_path) as f:
        for line in f:
            if line.strip():
                records.append(json.loads(line))

    if not records:
        return "Empty dataset."

    # Basic counts
    n_records = len(records)
    video_ids = set(r["video_id"] for r in records)
    n_videos = len(video_ids)

    # Scene type distribution
    scene_types: dict[str, int] = {}
    for r in records:
        st = r.get("scene_type", {})
        top = st.get("top", "unknown") if st else "unknown"
        scene_types[top] = scene_types.get(top, 0) + 1

    # Camera motion distribution
    motions: dict[str, int] = {}
    for r in records:
        cm = r.get("camera_motion", {})
        m = cm.get("motion", "unknown")
        motions[m] = motions.get(m, 0) + 1

    # Narration phase distribution
    phases: dict[str, int] = {}
    for r in records:
        narr = r.get("narration", {})
        p = narr.get("phase", "unknown")
        phases[p] = phases.get(p, 0) + 1

    # Quality score statistics
    composites = [
        r.get("quality", {}).get("composite", 0) for r in records
        if r.get("quality", {}).get("composite", 0) > 0
    ]
    q_mean = float(np.mean(composites)) if composites else 0
    q_std = float(np.std(composites)) if composites else 0

    # Sample weight statistics
    weights = [r.get("sample_weight", 0) for r in records]
    w_min = min(weights) if weights else 0
    w_max = max(weights) if weights else 0

    lines = [
        "=" * 60,
        "DATASET STATISTICS REPORT",
        "=" * 60,
        "",
        f"Total scenes:  {n_records}",
        f"Total videos:  {n_videos}",
        f"Scenes/video:  {n_records / max(n_videos, 1):.1f} (avg)",
        "",
        "--- Splits ---",
        f"  Train: {len(splits.get('train', []))} videos",
        f"  Val:   {len(splits.get('val', []))} videos",
        f"  Test:  {len(splits.get('test', []))} videos",
        "",
        "--- Scene Types ---",
    ]
    for st, count in sorted(scene_types.items(), key=lambda x: -x[1]):
        pct = count / n_records * 100
        lines.append(f"  {st[:50]:50s} {count:5d} ({pct:5.1f}%)")

    lines.extend([
        "",
        "--- Camera Motion ---",
    ])
    for m, count in sorted(motions.items(), key=lambda x: -x[1]):
        pct = count / n_records * 100
        lines.append(f"  {m:20s} {count:5d} ({pct:5.1f}%)")

    lines.extend([
        "",
        "--- Narration Phases ---",
    ])
    for p, count in sorted(phases.items(), key=lambda x: -x[1]):
        pct = count / n_records * 100
        lines.append(f"  {p:20s} {count:5d} ({pct:5.1f}%)")

    lines.extend([
        "",
        "--- Quality Scores ---",
        f"  Composite mean: {q_mean:.4f}",
        f"  Composite std:  {q_std:.4f}",
        "",
        "--- Sample Weights ---",
        f"  Min: {w_min:.8f}",
        f"  Max: {w_max:.8f}",
        "=" * 60,
    ])

    report = "\n".join(lines)
    logger.info("Dataset report:\n%s", report)

    # Save report
    report_path = dataset_path.parent / "dataset_report.txt"
    with open(report_path, "w") as f:
        f.write(report)

    return report
