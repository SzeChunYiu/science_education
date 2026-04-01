"""Assemble training data for all 3 discriminators from reference data."""
import json
import logging
import random
from pathlib import Path
from typing import Optional

import torch
from PIL import Image

logger = logging.getLogger(__name__)

DATA_DIR = Path("data/style_reference")
NEG_DIRS = [Path("data/style_negatives"), Path("data/discriminator_training/rejected_scenes")]
OUTPUT_DIR = Path("data/discriminator_training")


def _get_device() -> torch.device:
    """Auto-detect best available device."""
    if torch.cuda.is_available():
        return torch.device("cuda")
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return torch.device("mps")
    return torch.device("cpu")


def _collect_frames(directory: Path, extensions: tuple = (".png", ".jpg", ".jpeg")) -> list[Path]:
    """Recursively collect image files from a directory."""
    frames = []
    if not directory.exists():
        return frames
    for ext in extensions:
        frames.extend(directory.rglob(f"*{ext}"))
    return sorted(frames)


def prepare_style_data(
    pos_dir: Path = DATA_DIR,
    neg_dirs: list[Path] = None,
    output_path: Path = OUTPUT_DIR / "style_data.pt",
) -> dict:
    """Prepare balanced dataset for style discriminator.

    Collects positive frames from TED-Ed reference data and negative
    frames from style_negatives and rejected_scenes directories.

    Saves a .pt file with {'images': list[str], 'labels': tensor}.
    Returns stats dict.
    """
    if neg_dirs is None:
        neg_dirs = NEG_DIRS

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Collect positives
    pos_frames = _collect_frames(pos_dir)
    logger.info(f"Found {len(pos_frames)} positive frames from {pos_dir}")

    # Collect negatives from all sources
    neg_frames = []
    for neg_dir in neg_dirs:
        found = _collect_frames(neg_dir)
        logger.info(f"Found {len(found)} negative frames from {neg_dir}")
        neg_frames.extend(found)

    if not pos_frames:
        logger.warning("No positive frames found. Style data preparation skipped.")
        return {"positives": 0, "negatives": 0}

    # Balance dataset: match smaller class count
    min_count = min(len(pos_frames), len(neg_frames)) if neg_frames else len(pos_frames)
    if min_count == 0:
        logger.warning("No negative frames found. Using positives only.")
        min_count = len(pos_frames)

    random.shuffle(pos_frames)
    random.shuffle(neg_frames)
    selected_pos = pos_frames[:min_count]
    selected_neg = neg_frames[:min_count]

    # Build dataset
    all_images = [str(p) for p in selected_pos] + [str(p) for p in selected_neg]
    all_labels = [1] * len(selected_pos) + [0] * len(selected_neg)

    # Shuffle together
    combined = list(zip(all_images, all_labels))
    random.shuffle(combined)
    all_images, all_labels = zip(*combined) if combined else ([], [])

    torch.save(
        {"images": list(all_images), "labels": torch.tensor(list(all_labels), dtype=torch.long)},
        str(output_path),
    )

    stats = {"positives": len(selected_pos), "negatives": len(selected_neg), "output": str(output_path)}
    logger.info(f"Style data: {stats}")
    return stats


def prepare_semantic_data(
    data_dir: Path = DATA_DIR,
    output_path: Path = OUTPUT_DIR / "semantic_pairs.jsonl",
) -> dict:
    """Generate frame-narration pairs with 3 types of negatives for semantic discriminator.

    Positive: real keyframe + aligned narration sentence.
    Negative type 1: same frame + different scene narration (same video).
    Negative type 2: same frame + different video narration.
    Negative type 3: same frame + adjacent scene narration (hardest).

    Pre-computes CLIP image embeddings and sentence-transformer text embeddings
    for efficient training.

    Saves JSONL with fields: image_embedding, text_embedding, label, neg_type.
    Returns stats dict.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    device = _get_device()

    # Lazy-load encoders
    from transformers import CLIPModel, CLIPProcessor
    from sentence_transformers import SentenceTransformer

    logger.info("Loading CLIP and sentence-transformer for data preparation...")
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    clip_model.eval()
    sent_model = SentenceTransformer("all-MiniLM-L6-v2", device=str(device))

    # Collect all video data with frames and narrations
    video_data = []
    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue
        features_path = vid_dir / "features.json"
        if not features_path.exists():
            continue
        features = json.loads(features_path.read_text())
        frames_dir = vid_dir / "frames"

        scenes = []
        for frame_info in features.get("frames", []):
            frame_path = frames_dir / frame_info["filename"]
            narration = frame_info.get("narration", "")
            if frame_path.exists() and narration:
                scenes.append({"path": frame_path, "narration": narration, "info": frame_info})

        if scenes:
            video_data.append({"video_id": vid_dir.name, "scenes": scenes})

    if not video_data:
        logger.warning("No video data with narrations found.")
        return {"positives": 0, "negatives": 0}

    logger.info(f"Processing {sum(len(v['scenes']) for v in video_data)} scenes from {len(video_data)} videos")

    # Pre-encode all images and texts
    all_scenes_flat = []
    for vid in video_data:
        for i, scene in enumerate(vid["scenes"]):
            all_scenes_flat.append({
                "video_id": vid["video_id"],
                "scene_idx": i,
                "path": scene["path"],
                "narration": scene["narration"],
                "total_scenes": len(vid["scenes"]),
            })

    # Batch encode images
    logger.info("Encoding images with CLIP...")
    image_embeddings = []
    batch_size = 32
    for i in range(0, len(all_scenes_flat), batch_size):
        batch_paths = [s["path"] for s in all_scenes_flat[i : i + batch_size]]
        batch_images = [Image.open(p).convert("RGB") for p in batch_paths]
        with torch.no_grad():
            inputs = clip_processor(images=batch_images, return_tensors="pt").to(device)
            features = clip_model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
            image_embeddings.extend(features.cpu().tolist())

    # Batch encode texts
    logger.info("Encoding narrations with sentence-transformer...")
    narrations = [s["narration"] for s in all_scenes_flat]
    text_embeddings = sent_model.encode(narrations, batch_size=64, show_progress_bar=False)
    text_embeddings = [emb.tolist() for emb in text_embeddings]

    # Store embeddings back
    for i, scene in enumerate(all_scenes_flat):
        scene["img_emb"] = image_embeddings[i]
        scene["txt_emb"] = text_embeddings[i]

    # Build index by video for negative sampling
    video_scene_map = {}
    for scene in all_scenes_flat:
        vid_id = scene["video_id"]
        if vid_id not in video_scene_map:
            video_scene_map[vid_id] = []
        video_scene_map[vid_id].append(scene)

    # Generate pairs
    pairs = []
    stats = {"positives": 0, "neg_type_1": 0, "neg_type_2": 0, "neg_type_3": 0}

    for scene in all_scenes_flat:
        vid_id = scene["video_id"]
        scene_idx = scene["scene_idx"]

        # Positive pair
        pairs.append({
            "image_embedding": scene["img_emb"],
            "text_embedding": scene["txt_emb"],
            "label": 1,
            "neg_type": None,
        })
        stats["positives"] += 1

        vid_scenes = video_scene_map[vid_id]

        # Negative type 1: same frame + different scene narration (same video)
        other_scenes = [s for s in vid_scenes if s["scene_idx"] != scene_idx]
        if other_scenes:
            neg_scene = random.choice(other_scenes)
            pairs.append({
                "image_embedding": scene["img_emb"],
                "text_embedding": neg_scene["txt_emb"],
                "label": 0,
                "neg_type": 1,
            })
            stats["neg_type_1"] += 1

        # Negative type 2: same frame + different video narration
        other_vids = [v for v in video_scene_map if v != vid_id]
        if other_vids:
            rand_vid = random.choice(other_vids)
            rand_scene = random.choice(video_scene_map[rand_vid])
            pairs.append({
                "image_embedding": scene["img_emb"],
                "text_embedding": rand_scene["txt_emb"],
                "label": 0,
                "neg_type": 2,
            })
            stats["neg_type_2"] += 1

        # Negative type 3: same frame + adjacent scene narration (hardest)
        adjacent_indices = [scene_idx - 1, scene_idx + 1]
        adjacent = [s for s in vid_scenes if s["scene_idx"] in adjacent_indices]
        if adjacent:
            adj_scene = random.choice(adjacent)
            pairs.append({
                "image_embedding": scene["img_emb"],
                "text_embedding": adj_scene["txt_emb"],
                "label": 0,
                "neg_type": 3,
            })
            stats["neg_type_3"] += 1

    # Shuffle and write
    random.shuffle(pairs)
    with open(output_path, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")

    stats["total"] = len(pairs)
    stats["output"] = str(output_path)
    logger.info(f"Semantic data: {stats}")
    return stats


def prepare_flow_data(
    data_dir: Path = DATA_DIR,
    output_path: Path = OUTPUT_DIR / "flow_pairs.jsonl",
) -> dict:
    """Generate consecutive + shuffled scene pairs for flow discriminator.

    Positive: real consecutive scene pairs from TED-Ed.
    Negative: shuffled same-video pairs (2x oversample), cross-video pairs,
              cross-channel pairs.

    Pre-computes CLIP image embeddings for efficient training.

    Saves JSONL with fields: emb_a, emb_b, transition, label.
    Returns stats dict.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    device = _get_device()

    from transformers import CLIPModel, CLIPProcessor

    logger.info("Loading CLIP for flow data preparation...")
    clip_processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
    clip_model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32").to(device)
    clip_model.eval()

    # Collect all video data
    video_data = []
    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue
        features_path = vid_dir / "features.json"
        if not features_path.exists():
            continue
        features = json.loads(features_path.read_text())
        frames_dir = vid_dir / "frames"

        scenes = []
        for frame_info in features.get("frames", []):
            frame_path = frames_dir / frame_info["filename"]
            if frame_path.exists():
                transition = frame_info.get("transition", "cut")
                scenes.append({"path": frame_path, "transition": transition})

        if len(scenes) >= 2:
            video_data.append({"video_id": vid_dir.name, "scenes": scenes})

    if not video_data:
        logger.warning("No video data with consecutive scenes found.")
        return {"positives": 0, "negatives": 0}

    # Pre-encode all frames
    logger.info("Encoding frames with CLIP...")
    all_frames = []
    for vid in video_data:
        for scene in vid["scenes"]:
            all_frames.append(scene["path"])

    frame_embeddings = {}
    batch_size = 32
    for i in range(0, len(all_frames), batch_size):
        batch_paths = all_frames[i : i + batch_size]
        batch_images = [Image.open(p).convert("RGB") for p in batch_paths]
        with torch.no_grad():
            inputs = clip_processor(images=batch_images, return_tensors="pt").to(device)
            features = clip_model.get_image_features(**inputs)
            features = features / features.norm(dim=-1, keepdim=True)
            for j, path in enumerate(batch_paths):
                frame_embeddings[str(path)] = features[j].cpu().tolist()

    # Attach embeddings
    for vid in video_data:
        for scene in vid["scenes"]:
            scene["emb"] = frame_embeddings[str(scene["path"])]

    # Generate pairs
    pairs = []
    stats = {"positives": 0, "neg_shuffled": 0, "neg_cross_video": 0}

    for vid in video_data:
        scenes = vid["scenes"]

        # Positive: consecutive pairs
        for i in range(len(scenes) - 1):
            transition = scenes[i + 1].get("transition", "cut")
            if transition not in ("cut", "dissolve", "fade"):
                transition = "cut"
            pairs.append({
                "emb_a": scenes[i]["emb"],
                "emb_b": scenes[i + 1]["emb"],
                "transition": transition,
                "label": 1,
            })
            stats["positives"] += 1

        # Negative: shuffled same-video pairs (2x oversample)
        if len(scenes) >= 3:
            for _ in range(stats["positives"] * 2 // max(len(video_data), 1) + 1):
                idx_a = random.randint(0, len(scenes) - 1)
                idx_b = random.randint(0, len(scenes) - 1)
                # Ensure not actually consecutive
                if abs(idx_a - idx_b) <= 1:
                    continue
                pairs.append({
                    "emb_a": scenes[idx_a]["emb"],
                    "emb_b": scenes[idx_b]["emb"],
                    "transition": random.choice(["cut", "dissolve", "fade"]),
                    "label": 0,
                })
                stats["neg_shuffled"] += 1

    # Cross-video negative pairs
    all_scene_embs = []
    for vid in video_data:
        for scene in vid["scenes"]:
            all_scene_embs.append((vid["video_id"], scene["emb"]))

    n_cross = stats["positives"]  # Match positive count
    for _ in range(n_cross):
        idx_a = random.randint(0, len(all_scene_embs) - 1)
        idx_b = random.randint(0, len(all_scene_embs) - 1)
        if all_scene_embs[idx_a][0] == all_scene_embs[idx_b][0]:
            continue  # Skip same-video
        pairs.append({
            "emb_a": all_scene_embs[idx_a][1],
            "emb_b": all_scene_embs[idx_b][1],
            "transition": random.choice(["cut", "dissolve", "fade"]),
            "label": 0,
        })
        stats["neg_cross_video"] += 1

    # Shuffle and write
    random.shuffle(pairs)
    with open(output_path, "w") as f:
        for pair in pairs:
            f.write(json.dumps(pair) + "\n")

    stats["total"] = len(pairs)
    stats["output"] = str(output_path)
    logger.info(f"Flow data: {stats}")
    return stats


def prepare_all(data_dir: Optional[Path] = None):
    """Prepare training data for all 3 discriminators.

    Args:
        data_dir: Override default data directory.
    """
    if data_dir is not None:
        data_dir = Path(data_dir)
    else:
        data_dir = DATA_DIR

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s: %(message)s")

    logger.info("=== Preparing style discriminator data ===")
    style_stats = prepare_style_data(pos_dir=data_dir)

    logger.info("=== Preparing semantic discriminator data ===")
    semantic_stats = prepare_semantic_data(data_dir=data_dir)

    logger.info("=== Preparing flow discriminator data ===")
    flow_stats = prepare_flow_data(data_dir=data_dir)

    logger.info("=== All training data prepared ===")
    logger.info(f"Style: {style_stats}")
    logger.info(f"Semantic: {semantic_stats}")
    logger.info(f"Flow: {flow_stats}")
