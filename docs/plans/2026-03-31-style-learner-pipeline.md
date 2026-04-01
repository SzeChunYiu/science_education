# TED-Ed Style Learner Pipeline — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a complete ML-powered video production pipeline that produces TED-Ed quality educational videos — from data collection through final MP4 assembly. Training on LUNARC HPC, inference on local Mac mini M4.

**Architecture:** Multi-phase pipeline: (1) collect TED-Ed reference data, (2) extract features + train style models on LUNARC, (3) build local inference pipeline with SDXL illustration generation, parallax animation, F5-TTS narration, quality discriminators, and FFmpeg final assembly. All tools free/open-source.

**Tech Stack:** PyTorch, diffusers (SDXL + LoRA + IP-Adapter + ControlNet), F5-TTS, Kokoro, Whisper, CLIP, MiDaS, python-lottie, Manim CE, MusicGen, PIL, FFmpeg, SLURM

---

## Wave 1: Foundation (Local — no GPU needed)

### Task 1: Create requirements files and project scaffolding

**Files:**
- Create: `requirements.txt` (base dependencies for local M4)
- Create: `requirements-lunarc.txt` (GPU training dependencies for LUNARC)
- Create: `src/quality/__init__.py`
- Create: `src/quality/orchestrator.py`
- Create: `src/quality/discriminators/__init__.py`
- Create: `src/style_learner/__init__.py`
- Create: `src/style_learner/data_collection/__init__.py`
- Create: `src/style_learner/feature_extraction/__init__.py`
- Create: `src/style_learner/training/__init__.py`
- Create: `src/style_learner/inference/__init__.py`
- Create: `src/style_learner/illustration/__init__.py`
- Create: `src/style_learner/animation_layer/__init__.py`
- Create: `src/audio/__init__.py`
- Create: `src/audio/narration/__init__.py`
- Create: `src/audio/music/__init__.py`
- Create: `data/style_reference/playlists.txt`
- Create: `models/.gitkeep`

**Step 1: Create requirements.txt for local M4**

```txt
# Core
Pillow>=10.0
numpy>=1.24

# ML inference (MPS-compatible)
torch>=2.2
torchvision>=0.17
diffusers>=0.28
transformers>=4.40
safetensors>=0.4
accelerate>=0.28
sentence-transformers>=2.7

# Image generation
ip-adapter

# TTS
f5-tts>=0.3
kokoro>=0.3

# Audio
audiocraft>=1.3
librosa>=0.10

# Quality scoring
simple-aesthetics-predictor
easyocr>=1.7

# Animation
lottie>=0.7
midas>=0.1

# Depth estimation
timm>=0.9

# NLI
python-Levenshtein>=0.25

# Video
moviepy>=1.0

# NLP
spacy>=3.7

# Utility
colorthief>=0.2.1
tqdm>=4.66
pyyaml>=6.0
```

**Step 2: Create requirements-lunarc.txt**

```txt
# Everything in requirements.txt plus:
-r requirements.txt

# Data collection
yt-dlp>=2024.1
scenedetect[opencv]>=0.6

# Transcription
openai-whisper>=20231117

# Training
kohya-ss-sd-scripts
tensorboard>=2.15

# Auto-captioning
salesforce-lavis

# Additional
ultralytics>=8.1
aeneas>=1.7
textstat>=0.7.3
```

**Step 3: Create directory scaffolding**

```bash
mkdir -p src/quality/discriminators
mkdir -p src/quality/visual
mkdir -p src/quality/script
mkdir -p src/quality/audio
mkdir -p src/quality/animation
mkdir -p src/style_learner/data_collection
mkdir -p src/style_learner/feature_extraction
mkdir -p src/style_learner/training
mkdir -p src/style_learner/inference
mkdir -p src/style_learner/illustration
mkdir -p src/style_learner/animation_layer
mkdir -p src/audio/narration
mkdir -p src/audio/music
mkdir -p data/style_reference
mkdir -p data/style_negatives
mkdir -p data/discriminator_training/rejected_scenes
mkdir -p models/style_learner/characters
mkdir -p models/discriminators
```

**Step 4: Create playlists.txt with all TED-Ed playlist URLs**

```txt
https://www.youtube.com/playlist?list=PLJicmE8fK0EgJTgTCK7-t-91bdwGm3Nit
https://www.youtube.com/playlist?list=PLJicmE8fK0EinZZ6hY-RzJr8kcgIERWEc
https://www.youtube.com/playlist?list=PLJicmE8fK0EiNFLhSxeXVEo5eOdJ6QM8U
https://www.youtube.com/playlist?list=PLJicmE8fK0Ej2IjNSQf_G7GrKFBcsaCLJ
https://www.youtube.com/playlist?list=PLJicmE8fK0Ege5CYPbAS4QlvZQw7hbm5C
https://www.youtube.com/playlist?list=PLJicmE8fK0EiskDjD7XE9hMTRnwFtWj1Y
https://www.youtube.com/playlist?list=PLJicmE8fK0Ei3dAErHrPBfzRpmFDr4vsy
https://www.youtube.com/playlist?list=PLJicmE8fK0EiSfV8MziPXk2XkwAModA-h
https://www.youtube.com/playlist?list=PL45DD1CA57AA3122A
https://www.youtube.com/watch?v=jDg8DQl7ZeQ&list=PLJicmE8fK0EgBw0FVYiTACRNRaNAtzK-1
```

**Step 5: Create all `__init__.py` files (empty or with docstrings)**

**Step 6: Commit**

```bash
git add requirements.txt requirements-lunarc.txt src/quality/ src/style_learner/ src/audio/ data/style_reference/playlists.txt models/.gitkeep
git commit -m "scaffold: style learner directory structure and requirements"
```

---

### Task 2: Build data collection pipeline

**Files:**
- Create: `src/style_learner/data_collection/playlist_fetcher.py`
- Create: `src/style_learner/data_collection/video_downloader.py`
- Create: `src/style_learner/data_collection/frame_extractor.py`
- Create: `src/style_learner/data_collection/transcript_extractor.py`
- Create: `src/style_learner/data_collection/scene_detector.py`
- Create: `src/style_learner/data_collection/collect_all.py`
- Create: `tests/style_learner/test_data_collection.py`

**Step 1: Write playlist_fetcher.py**

Fetches video metadata from playlists using yt-dlp `--dump-json --flat-playlist`.
Returns list of `{video_id, title, duration, view_count}` dicts.
Saves index to `data/style_reference/index.json`.

```python
"""Fetch playlist metadata without downloading videos."""
import json
import subprocess
from pathlib import Path

DATA_DIR = Path("data/style_reference")


def fetch_playlist_metadata(playlist_url: str) -> list[dict]:
    """Fetch video metadata from a YouTube playlist."""
    result = subprocess.run(
        ["yt-dlp", "--dump-json", "--flat-playlist", playlist_url],
        capture_output=True, text=True, timeout=300,
    )
    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line:
            continue
        meta = json.loads(line)
        videos.append({
            "video_id": meta.get("id", ""),
            "title": meta.get("title", ""),
            "duration": meta.get("duration"),
            "view_count": meta.get("view_count"),
            "url": meta.get("url") or meta.get("webpage_url", ""),
        })
    return videos


def fetch_all_playlists(playlists_file: Path = DATA_DIR / "playlists.txt") -> list[dict]:
    """Fetch metadata for all playlists listed in playlists.txt."""
    all_videos = []
    seen_ids = set()
    for line in playlists_file.read_text().strip().split("\n"):
        url = line.strip()
        if not url or url.startswith("#"):
            continue
        videos = fetch_playlist_metadata(url)
        for v in videos:
            if v["video_id"] not in seen_ids:
                seen_ids.add(v["video_id"])
                all_videos.append(v)
    # Save index
    index_path = DATA_DIR / "index.json"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(all_videos, indent=2))
    return all_videos
```

**Step 2: Write video_downloader.py**

Downloads video + audio + auto-subs in batches of 10 with 30s delay.
Uses archive file for resumability.

```python
"""Download reference videos with rate limiting and resumability."""
import subprocess
import time
from pathlib import Path

DATA_DIR = Path("data/style_reference")


def download_videos(
    videos: list[dict],
    output_dir: Path = DATA_DIR,
    batch_size: int = 10,
    delay: int = 30,
) -> list[str]:
    """Download videos in batches with rate limit handling."""
    archive_file = output_dir / "downloaded.txt"
    downloaded = []

    for i in range(0, len(videos), batch_size):
        batch = videos[i : i + batch_size]
        for video in batch:
            vid = video["video_id"]
            vid_dir = output_dir / vid
            vid_dir.mkdir(parents=True, exist_ok=True)

            cmd = [
                "yt-dlp",
                "--format", "mp4",
                "--extract-audio", "--audio-format", "mp3", "--keep-video",
                "--write-auto-sub", "--sub-lang", "en",
                "--download-archive", str(archive_file),
                "--output", str(vid_dir / "%(title)s.%(ext)s"),
                "--no-overwrites",
                video["url"],
            ]
            try:
                subprocess.run(cmd, timeout=600, check=False)
                downloaded.append(vid)
            except subprocess.TimeoutExpired:
                print(f"Timeout downloading {vid}, skipping")
            except Exception as e:
                print(f"Error downloading {vid}: {e}")

        if i + batch_size < len(videos):
            print(f"Batch complete, waiting {delay}s before next batch...")
            time.sleep(delay)

    return downloaded


def download_negative_channels(
    channels: dict[str, str],
    max_videos: int = 20,
    output_base: Path = Path("data/style_negatives"),
) -> None:
    """Download frames from negative example channels."""
    for name, url in channels.items():
        out_dir = output_base / name
        out_dir.mkdir(parents=True, exist_ok=True)
        archive = out_dir / "downloaded.txt"

        cmd = [
            "yt-dlp",
            "--format", "mp4",
            "--playlist-end", str(max_videos),
            "--download-archive", str(archive),
            "--output", str(out_dir / "%(id)s/video.%(ext)s"),
            "--no-overwrites",
            url,
        ]
        subprocess.run(cmd, timeout=3600, check=False)
```

**Step 3: Write frame_extractor.py**

Extracts frames at 2fps using ffmpeg.

```python
"""Extract frames from downloaded videos at 2fps."""
import subprocess
from pathlib import Path


def extract_frames(video_path: Path, output_dir: Path, fps: int = 2) -> int:
    """Extract frames from a video at given fps. Returns frame count."""
    output_dir.mkdir(parents=True, exist_ok=True)
    pattern = str(output_dir / "frame_%05d.png")

    cmd = [
        "ffmpeg", "-i", str(video_path),
        "-vf", f"fps={fps}",
        "-q:v", "2",
        pattern,
        "-y",
    ]
    subprocess.run(cmd, capture_output=True, check=True)
    return len(list(output_dir.glob("frame_*.png")))


def extract_all_frames(
    data_dir: Path = Path("data/style_reference"),
    fps: int = 2,
) -> dict[str, int]:
    """Extract frames for all downloaded videos."""
    results = {}
    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue
        video_files = list(vid_dir.glob("*.mp4"))
        if not video_files:
            continue

        frames_dir = vid_dir / "frames"
        if frames_dir.exists() and len(list(frames_dir.glob("*.png"))) > 0:
            results[vid_dir.name] = len(list(frames_dir.glob("*.png")))
            continue

        count = extract_frames(video_files[0], frames_dir, fps)
        results[vid_dir.name] = count
    return results
```

**Step 4: Write transcript_extractor.py**

Uses auto-subs if available, falls back to Whisper.

```python
"""Extract transcripts with word-level timestamps."""
import json
import re
from pathlib import Path


def parse_vtt_to_words(vtt_path: Path) -> list[dict]:
    """Parse WebVTT subtitle file to word-level timestamps."""
    text = vtt_path.read_text()
    words = []
    for match in re.finditer(
        r"(\d{2}:\d{2}:\d{2}\.\d{3}) --> (\d{2}:\d{2}:\d{2}\.\d{3})\n(.+?)(?:\n\n|\Z)",
        text, re.DOTALL,
    ):
        start = _vtt_to_seconds(match.group(1))
        end = _vtt_to_seconds(match.group(2))
        line_text = match.group(3).strip()
        line_words = line_text.split()
        if not line_words:
            continue
        word_dur = (end - start) / len(line_words)
        for i, word in enumerate(line_words):
            clean = re.sub(r"<[^>]+>", "", word).strip()
            if clean:
                words.append({
                    "word": clean,
                    "start": round(start + i * word_dur, 3),
                    "end": round(start + (i + 1) * word_dur, 3),
                })
    return words


def extract_transcript_whisper(audio_path: Path) -> list[dict]:
    """Extract transcript using Whisper with word timestamps."""
    import whisper
    model = whisper.load_model("large-v2")
    result = model.transcribe(str(audio_path), word_timestamps=True)
    words = []
    for seg in result["segments"]:
        for w in seg.get("words", []):
            words.append({
                "word": w["word"].strip(),
                "start": round(w["start"], 3),
                "end": round(w["end"], 3),
            })
    return words


def extract_transcript(vid_dir: Path) -> list[dict]:
    """Extract transcript for a video, preferring auto-subs over Whisper."""
    transcript_path = vid_dir / "transcript.json"
    if transcript_path.exists():
        return json.loads(transcript_path.read_text())

    # Try auto-subs first
    vtt_files = list(vid_dir.glob("*.en.vtt"))
    if vtt_files:
        words = parse_vtt_to_words(vtt_files[0])
        if len(words) > 10:  # sanity check
            transcript_path.write_text(json.dumps(words, indent=2))
            return words

    # Fall back to Whisper
    audio_files = list(vid_dir.glob("*.mp3"))
    if audio_files:
        words = extract_transcript_whisper(audio_files[0])
        transcript_path.write_text(json.dumps(words, indent=2))
        return words

    return []


def _vtt_to_seconds(timestamp: str) -> float:
    """Convert VTT timestamp HH:MM:SS.mmm to seconds."""
    parts = timestamp.split(":")
    h, m = int(parts[0]), int(parts[1])
    s = float(parts[2])
    return h * 3600 + m * 60 + s
```

**Step 5: Write scene_detector.py**

Uses PySceneDetect for scene boundary detection.

```python
"""Detect scene boundaries in reference videos."""
import json
from pathlib import Path


def detect_scenes(video_path: Path, threshold: float = 27.0) -> list[dict]:
    """Detect scene boundaries using PySceneDetect ContentDetector."""
    from scenedetect import detect, ContentDetector

    scene_list = detect(str(video_path), ContentDetector(threshold=threshold))
    scenes = []
    for i, (start, end) in enumerate(scene_list):
        scenes.append({
            "scene_id": i + 1,
            "start_time": round(start.get_seconds(), 3),
            "end_time": round(end.get_seconds(), 3),
            "duration": round(end.get_seconds() - start.get_seconds(), 3),
        })
    return scenes


def detect_all_scenes(
    data_dir: Path = Path("data/style_reference"),
    threshold: float = 27.0,
) -> dict[str, int]:
    """Detect scenes for all downloaded videos."""
    results = {}
    for vid_dir in sorted(data_dir.iterdir()):
        if not vid_dir.is_dir():
            continue

        scenes_path = vid_dir / "scenes.json"
        if scenes_path.exists():
            scenes = json.loads(scenes_path.read_text())
            results[vid_dir.name] = len(scenes)
            continue

        video_files = list(vid_dir.glob("*.mp4"))
        if not video_files:
            continue

        scenes = detect_scenes(video_files[0], threshold)
        scenes_path.write_text(json.dumps(scenes, indent=2))
        results[vid_dir.name] = len(scenes)
    return results
```

**Step 6: Write collect_all.py orchestrator**

```python
"""Master data collection orchestrator. Run locally, rsync to LUNARC."""
import argparse
from pathlib import Path
from .playlist_fetcher import fetch_all_playlists
from .video_downloader import download_videos, download_negative_channels
from .frame_extractor import extract_all_frames
from .transcript_extractor import extract_transcript
from .scene_detector import detect_all_scenes

NEGATIVE_CHANNELS = {
    "kurzgesagt": "https://www.youtube.com/@kurzgesagt",
    "primer": "https://www.youtube.com/@PrimerBlobs",
    "crashcourse": "https://www.youtube.com/@crashcourse",
}


def main():
    parser = argparse.ArgumentParser(description="Collect TED-Ed reference data")
    parser.add_argument("--test-mode", action="store_true", help="Process only 3 videos")
    parser.add_argument("--skip-download", action="store_true")
    parser.add_argument("--skip-negatives", action="store_true")
    args = parser.parse_args()

    data_dir = Path("data/style_reference")

    # Step 1: Fetch playlist metadata
    print("=== Fetching playlist metadata ===")
    videos = fetch_all_playlists()
    print(f"Found {len(videos)} unique videos")

    if args.test_mode:
        videos = videos[:3]
        print(f"Test mode: processing only {len(videos)} videos")

    # Step 2: Download videos
    if not args.skip_download:
        print("=== Downloading videos ===")
        download_videos(videos)

    # Step 3: Extract frames
    print("=== Extracting frames ===")
    frame_counts = extract_all_frames(data_dir)
    print(f"Extracted frames for {len(frame_counts)} videos")

    # Step 4: Extract transcripts
    print("=== Extracting transcripts ===")
    for vid_dir in sorted(data_dir.iterdir()):
        if vid_dir.is_dir() and not (vid_dir / "transcript.json").exists():
            extract_transcript(vid_dir)

    # Step 5: Detect scenes
    print("=== Detecting scenes ===")
    scene_counts = detect_all_scenes(data_dir)
    print(f"Detected scenes for {len(scene_counts)} videos")

    # Step 6: Download negative examples
    if not args.skip_negatives:
        print("=== Downloading negative examples ===")
        max_vids = 3 if args.test_mode else 20
        download_negative_channels(NEGATIVE_CHANNELS, max_videos=max_vids)

    print("=== Data collection complete ===")
    print(f"Videos: {len(videos)}")
    print(f"Total frames: {sum(frame_counts.values())}")
    print(f"Total scenes: {sum(scene_counts.values())}")


if __name__ == "__main__":
    main()
```

**Step 7: Commit**

```bash
git add src/style_learner/data_collection/
git commit -m "feat: data collection pipeline for TED-Ed reference videos"
```

---

### Task 3: Build feature extraction pipeline (runs on LUNARC)

**Files:**
- Create: `src/style_learner/feature_extraction/clip_features.py`
- Create: `src/style_learner/feature_extraction/camera_motion.py`
- Create: `src/style_learner/feature_extraction/text_layout.py`
- Create: `src/style_learner/feature_extraction/quality_scores.py`
- Create: `src/style_learner/feature_extraction/narration_alignment.py`
- Create: `src/style_learner/feature_extraction/dataset_builder.py`
- Create: `src/style_learner/feature_extraction/extract_all.py`

**Step 1: Write clip_features.py**

Computes CLIP embeddings + zero-shot scene type classification per keyframe.

**Step 2: Write camera_motion.py**

Farneback optical flow between consecutive frames → classify pan/zoom/static.

**Step 3: Write text_layout.py**

EasyOCR text detection → normalised position, size, role classification.

**Step 4: Write quality_scores.py**

LAION aesthetic predictor + CLIP frame consistency + audio quality proxy.

**Step 5: Write narration_alignment.py**

Align Whisper words to scene boundaries → narration phase classification.

**Step 6: Write dataset_builder.py**

Assemble all features into `dataset.jsonl` with 80/10/10 split.

**Step 7: Write extract_all.py orchestrator + SLURM job script**

```bash
#!/bin/bash
#SBATCH -A lu2025-2-51
#SBATCH -p gpua100
#SBATCH --gres=gpu:1
#SBATCH -N 1
#SBATCH --cpus-per-task=8
#SBATCH --mem=64G
#SBATCH -t 4:00:00
#SBATCH -J feature_extract

python -m src.style_learner.feature_extraction.extract_all
```

**Step 8: Commit**

---

### Task 4: Build style model training (runs on LUNARC)

**Files:**
- Create: `src/style_learner/training/scene_classifier.py`
- Create: `src/style_learner/training/camera_predictor.py`
- Create: `src/style_learner/training/text_placement.py`
- Create: `src/style_learner/training/transition_predictor.py`
- Create: `src/style_learner/training/train_all.py`
- Create: `scripts/lunarc/train_style_models.sh` (SLURM script)

Each model follows the same pattern: load dataset, create DataLoader with WeightedRandomSampler, train MLP, save best checkpoint by validation metric, early stopping patience=10.

**Step 1: Write scene_classifier.py** — 2-layer MLP on CLIP embeddings → 8-class scene types

**Step 2: Write camera_predictor.py** — 3-layer MLP on sentence embeddings + scene type → motion type + magnitude

**Step 3: Write text_placement.py** — 3-layer MLP → x, y, font_size, animation

**Step 4: Write transition_predictor.py** — 3-layer MLP on consecutive CLIP pairs → transition type + duration

**Step 5: Write train_all.py orchestrator**

**Step 6: Write SLURM script**

**Step 7: Commit**

---

### Task 5: Build SDXL LoRA training scripts (runs on LUNARC)

**Files:**
- Create: `scripts/lunarc/train_style_lora.sh`
- Create: `scripts/lunarc/train_character_lora.sh`
- Create: `src/style_learner/training/prepare_lora_dataset.py`

**Step 1: Write prepare_lora_dataset.py**

Extract top-quality TED-Ed keyframes (sorted by aesthetic score), auto-caption with BLIP, format for kohya_ss training (image + caption .txt pairs).

**Step 2: Write SLURM script for style LoRA**

```bash
#SBATCH -p gpua100 --gres=gpu:1 --mem=64G -t 2:00:00
accelerate launch sdxl_train_network.py \
  --pretrained_model_name_or_path="stabilityai/stable-diffusion-xl-base-1.0" \
  --train_data_dir="$BASE/data/lora_training/teded_style/" \
  --network_module=networks.lora --network_dim=32 --network_alpha=16 \
  --resolution=1024 --train_batch_size=4 --max_train_epochs=20 \
  --output_name="teded_style_v1"
```

**Step 3: Write SLURM script for character LoRAs (parameterised)**

**Step 4: Commit**

---

### Task 6: Build discriminator training (runs on LUNARC)

**Files:**
- Create: `src/quality/discriminators/style_discriminator.py`
- Create: `src/quality/discriminators/semantic_discriminator.py`
- Create: `src/quality/discriminators/flow_discriminator.py`
- Create: `src/quality/discriminators/prepare_training_data.py`
- Create: `src/quality/discriminators/retrain.py`
- Create: `scripts/lunarc/train_discriminators.sh`

**Step 1: Write style_discriminator.py**

ViT-Small fine-tuned as binary classifier (TED-Ed vs non-TED-Ed). Fine-tune last 2 transformer blocks + classification head. `score(image) -> float`.

**Step 2: Write semantic_discriminator.py**

3-layer MLP on CLIP image + sentence-transformer embeddings (896-dim → sigmoid). `score(image, narration_text) -> float`.

**Step 3: Write flow_discriminator.py**

3-layer MLP on consecutive CLIP pairs + transition type (1027-dim → sigmoid). `score(frame_a, frame_b, transition_type) -> float`.

**Step 4: Write prepare_training_data.py**

Assembles training data for all 3 discriminators from reference data + negative examples.

**Step 5: Write retrain.py**

Adversarial retraining loop — runs every 10 episodes, fine-tunes from checkpoint, validates before replacing.

**Step 6: Write SLURM script**

**Step 7: Commit**

---

### Task 7: Build F5-TTS voice training (runs on LUNARC)

**Files:**
- Create: `src/audio/narration/voice_trainer.py`
- Create: `src/audio/narration/reference_voice.py`
- Create: `scripts/lunarc/train_voice.sh`
- Create: `scripts/lunarc/batch_narration.sh`

**Step 1: Write voice_trainer.py**

Prepares reference audio, runs F5-TTS fine-tuning on LUNARC.

**Step 2: Write reference_voice.py**

Sources CC0 reference narration audio (LibriVox) for voice design.

**Step 3: Write SLURM scripts for training + batch rendering**

**Step 4: Commit**

---

## Wave 2: Local Inference Pipeline (M4 Mac)

### Task 8: Build quality orchestrator

**Files:**
- Create: `src/quality/orchestrator.py`
- Create: `src/quality/visual/aesthetic_scorer.py`
- Create: `src/quality/visual/semantic_aligner.py`
- Create: `src/quality/visual/style_consistency.py`
- Create: `src/quality/visual/composition_checker.py`
- Create: `tests/quality/test_orchestrator.py`

**Step 1: Write aesthetic_scorer.py**

Wraps LAION Aesthetic Predictor. `score(image_path) -> float`. Threshold: >= 5.0 for scenes, >= 5.5 for titles.

**Step 2: Write semantic_aligner.py**

CLIP cosine similarity between image + text prompt. `score(image, text) -> float`. Threshold: >= 0.22.

**Step 3: Write style_consistency.py**

Maintains running CLIP embedding centroid per episode. `score(image, centroid) -> float`. Threshold: >= 0.85.

**Step 4: Write composition_checker.py**

Rule-of-thirds check via simple heuristic (no YOLO needed locally). Visual balance check.

**Step 5: Write orchestrator.py**

Central quality controller. Accepts generator function + list of scorers + thresholds. Generates N=4 candidates, scores all, picks highest composite passing all thresholds. Max 3 regeneration rounds.

```python
"""Quality orchestrator: generate → score → accept/reject loop."""
from dataclasses import dataclass
from typing import Callable
import logging

logger = logging.getLogger(__name__)


@dataclass
class ScorerConfig:
    name: str
    scorer: Callable
    threshold: float
    weight: float = 1.0


@dataclass
class QualityResult:
    accepted: bool
    candidate: object
    scores: dict[str, float]
    composite_score: float
    attempt: int


class QualityOrchestrator:
    def __init__(
        self,
        scorers: list[ScorerConfig],
        n_candidates: int = 4,
        max_rounds: int = 3,
    ):
        self.scorers = scorers
        self.n_candidates = n_candidates
        self.max_rounds = max_rounds

    def run(self, generator: Callable, **gen_kwargs) -> QualityResult:
        best_result = None
        best_composite = -1.0

        for attempt in range(1, self.max_rounds + 1):
            candidates = [generator(**gen_kwargs) for _ in range(self.n_candidates)]

            for candidate in candidates:
                scores = {}
                all_pass = True
                for sc in self.scorers:
                    score = sc.scorer(candidate)
                    scores[sc.name] = score
                    if score < sc.threshold:
                        all_pass = False

                # Weighted average for ranking
                total_weight = sum(sc.weight for sc in self.scorers)
                composite = sum(
                    sc.weight * scores[sc.name] for sc in self.scorers
                ) / total_weight

                result = QualityResult(
                    accepted=all_pass,
                    candidate=candidate,
                    scores=scores,
                    composite_score=composite,
                    attempt=attempt,
                )

                if composite > best_composite:
                    best_composite = composite
                    best_result = result

                if all_pass:
                    return result

            logger.warning(f"Round {attempt}: no candidate passed all thresholds")

        # Return best available after all rounds
        if best_result:
            best_result.accepted = False
            logger.error(f"Quality gate failed after {self.max_rounds} rounds")
        return best_result
```

**Step 6: Write test_orchestrator.py**

**Step 7: Commit**

---

### Task 9: Build illustration pipeline (SDXL inference on M4)

**Files:**
- Create: `src/style_learner/illustration/sdxl_generator.py`
- Create: `src/style_learner/illustration/prompt_builder.py`
- Create: `src/style_learner/illustration/consistency_memory.py`
- Create: `tests/style_learner/test_illustration.py`

**Step 1: Write prompt_builder.py**

Assembles SD prompts from production plan: scene type + entities + palette + LoRA trigger + character anchors from consistency memory.

**Step 2: Write consistency_memory.py**

Per-episode memory of accepted visual elements. Updates after each accepted scene. Injects anchors into subsequent prompts.

**Step 3: Write sdxl_generator.py**

SDXL inference with LoRA + IP-Adapter on MPS.

```python
"""SDXL illustration generator with LoRA + IP-Adapter on Apple M4 MPS."""
import torch
from pathlib import Path
from PIL import Image


class SDXLGenerator:
    def __init__(
        self,
        style_lora_path: Path = None,
        character_lora_dir: Path = None,
        device: str = "mps",
    ):
        self.device = device
        self.pipe = None
        self.style_lora_path = style_lora_path
        self.character_lora_dir = character_lora_dir

    def load(self):
        """Load SDXL + LoRA. Call once, reuse for many generations."""
        from diffusers import StableDiffusionXLPipeline

        self.pipe = StableDiffusionXLPipeline.from_pretrained(
            "stabilityai/stable-diffusion-xl-base-1.0",
            torch_dtype=torch.float16,
            variant="fp16",
        )
        self.pipe.enable_attention_slicing()
        self.pipe.enable_vae_slicing()

        if self.style_lora_path and self.style_lora_path.exists():
            self.pipe.load_lora_weights(str(self.style_lora_path))

        self.pipe = self.pipe.to(self.device)

    def generate(
        self,
        prompt: str,
        negative_prompt: str = "photorealistic, 3d, dark, blurry, text, watermark",
        width: int = 1024,
        height: int = 1024,
        steps: int = 25,
        guidance_scale: float = 7.5,
        seed: int = None,
    ) -> Image.Image:
        """Generate a single illustration."""
        generator = None
        if seed is not None:
            generator = torch.Generator(self.device).manual_seed(seed)

        result = self.pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance_scale,
            generator=generator,
        )
        return result.images[0]

    def unload(self):
        """Free GPU memory."""
        del self.pipe
        self.pipe = None
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
```

**Step 4: Write test_illustration.py**

**Step 5: Commit**

---

### Task 10: Build animation system (parallax + narration-synced reveals)

**Files:**
- Create: `src/style_learner/animation_layer/parallax.py`
- Create: `src/style_learner/animation_layer/depth_splitter.py`
- Create: `src/style_learner/animation_layer/narration_sync.py`
- Create: `src/style_learner/animation_layer/transition_renderer.py`
- Create: `src/style_learner/animation_layer/lottie_renderer.py`
- Modify: `src/animation/scene_types.py` (add new TED-Ed scene factories)

**Step 1: Write depth_splitter.py**

MiDaS depth estimation → split image into 3 layers (fg/mid/bg).

```python
"""Split illustration into depth layers using MiDaS."""
import torch
import numpy as np
from PIL import Image


class DepthSplitter:
    def __init__(self, device: str = "mps"):
        self.device = device
        self.model = None

    def load(self):
        self.model = torch.hub.load("intel-isl/MiDaS", "MiDaS_small")
        self.model.to(self.device).eval()
        self.transforms = torch.hub.load("intel-isl/MiDaS", "transforms").small_transform

    def estimate_depth(self, image: Image.Image) -> np.ndarray:
        """Estimate depth map from image. Returns normalised 0-1 depth."""
        img_np = np.array(image)
        input_batch = self.transforms(img_np).to(self.device)
        with torch.no_grad():
            depth = self.model(input_batch)
            depth = torch.nn.functional.interpolate(
                depth.unsqueeze(1), size=img_np.shape[:2],
                mode="bicubic", align_corners=False,
            ).squeeze().cpu().numpy()
        # Normalise to 0-1
        depth = (depth - depth.min()) / (depth.max() - depth.min() + 1e-8)
        return depth

    def split_layers(
        self, image: Image.Image, depth: np.ndarray,
        fg_threshold: float = 0.6, bg_threshold: float = 0.3,
    ) -> tuple[Image.Image, Image.Image, Image.Image]:
        """Split image into foreground, midground, background layers."""
        img_np = np.array(image.convert("RGBA"))

        fg_mask = (depth >= fg_threshold).astype(np.uint8) * 255
        bg_mask = (depth <= bg_threshold).astype(np.uint8) * 255
        mid_mask = ((depth > bg_threshold) & (depth < fg_threshold)).astype(np.uint8) * 255

        def apply_mask(mask):
            layer = img_np.copy()
            layer[:, :, 3] = mask
            return Image.fromarray(layer)

        return apply_mask(fg_mask), apply_mask(mid_mask), apply_mask(bg_mask)

    def unload(self):
        del self.model
        self.model = None
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
```

**Step 2: Write parallax.py**

Applies differential motion to depth layers → renders frames.

```python
"""Multi-layer parallax animation renderer."""
import numpy as np
from PIL import Image
from pathlib import Path

MOTION_MULTIPLIERS = {"foreground": 1.0, "midground": 0.6, "background": 0.3}
CAMERA_MOTIONS = {
    "pan_left": (-1, 0), "pan_right": (1, 0),
    "pan_up": (0, -1), "pan_down": (0, 1),
    "zoom_in": (0, 0),  # handled separately
    "zoom_out": (0, 0),
    "static": (0, 0),
}


def render_parallax_frames(
    fg: Image.Image, mid: Image.Image, bg: Image.Image,
    motion: str, magnitude: str, duration: float,
    fps: int = 30, canvas_size: tuple = (1920, 1080),
) -> list[Image.Image]:
    """Render parallax animation frames from depth layers."""
    n_frames = int(duration * fps)
    mag_scale = {"slow": 0.02, "medium": 0.05, "fast": 0.08}.get(magnitude, 0.03)
    direction = CAMERA_MOTIONS.get(motion, (0, 0))

    frames = []
    for i in range(n_frames):
        t = i / max(n_frames - 1, 1)  # 0 to 1
        canvas = Image.new("RGBA", canvas_size, (0, 0, 0, 255))

        for layer, layer_name in [(bg, "background"), (mid, "midground"), (fg, "foreground")]:
            mult = MOTION_MULTIPLIERS[layer_name]
            dx = int(direction[0] * mag_scale * canvas_size[0] * t * mult)
            dy = int(direction[1] * mag_scale * canvas_size[1] * t * mult)

            if motion == "zoom_in":
                scale = 1.0 + mag_scale * t * mult
                w = int(layer.width * scale)
                h = int(layer.height * scale)
                resized = layer.resize((w, h), Image.LANCZOS)
                x = (canvas_size[0] - w) // 2
                y = (canvas_size[1] - h) // 2
                canvas.paste(resized, (x, y), resized)
            elif motion == "zoom_out":
                scale = 1.0 + mag_scale * (1 - t) * mult
                w = int(layer.width * scale)
                h = int(layer.height * scale)
                resized = layer.resize((w, h), Image.LANCZOS)
                x = (canvas_size[0] - w) // 2
                y = (canvas_size[1] - h) // 2
                canvas.paste(resized, (x, y), resized)
            else:
                canvas.paste(layer, (dx, dy), layer)

        frames.append(canvas.convert("RGB"))

    return frames
```

**Step 3: Write narration_sync.py**

Maps text elements to Whisper word timestamps → trigger animations.

**Step 4: Write transition_renderer.py**

FFmpeg-based transitions between scene clips (dissolve, wipe, cut).

**Step 5: Write lottie_renderer.py**

Renders Lottie JSON animations to PIL frames for physics demos.

**Step 6: Commit**

---

### Task 11: Build production plan generator

**Files:**
- Create: `src/style_learner/inference/plan_generator.py`
- Create: `src/style_learner/inference/visual_metaphor.py`
- Modify: `src/pipeline/episode_renderer.py` (integrate production plan)

**Step 1: Write plan_generator.py**

Takes parsed script, runs through all 4 style models, outputs `production_plan.json`.

**Step 2: Write visual_metaphor.py**

Template-based visual metaphor suggestions for abstract concepts (rule-based, no LLM call needed at runtime — use a lookup table built from TED-Ed analysis).

**Step 3: Integrate with episode_renderer.py**

Add production plan as optional input to `render_episode()`. When present, use it for camera motion, text placement, transitions, colour palette instead of defaults.

**Step 4: Commit**

---

### Task 12: Build narration pipeline (local inference)

**Files:**
- Create: `src/audio/narration/f5_narrator.py`
- Create: `src/audio/narration/kokoro_preview.py`
- Create: `src/audio/narration/audio_mixer.py`
- Modify: `src/pipeline/episode_renderer.py` (integrate new TTS)

**Step 1: Write f5_narrator.py**

F5-TTS inference on MPS. Generates narration from script text + reference voice clip.

**Step 2: Write kokoro_preview.py**

Kokoro via mlx-audio for instant local previews.

**Step 3: Write audio_mixer.py**

Mix narration + background music using ffmpeg. Narration at 0dB, music at -18dB.

**Step 4: Commit**

---

### Task 13: Build music generation

**Files:**
- Create: `src/audio/music/musicgen_generator.py`

**Step 1: Write musicgen_generator.py**

MusicGen inference for ambient educational music. ~4GB on MPS.

```python
"""Generate background music using MusicGen."""
import torch
from pathlib import Path


class MusicGenerator:
    def __init__(self, device: str = "mps"):
        self.device = device
        self.model = None

    def load(self):
        from audiocraft.models import MusicGen
        self.model = MusicGen.get_pretrained("facebook/musicgen-small")
        self.model.set_generation_params(duration=30)

    def generate(self, mood: str, duration: int = 60) -> Path:
        """Generate ambient background music."""
        prompt = f"gentle educational ambient music, {mood}, instrumental, no vocals"
        self.model.set_generation_params(duration=min(duration, 30))

        wav = self.model.generate([prompt])
        # Save and return path
        output_path = Path(f"output/temp_music_{mood}.wav")
        import torchaudio
        torchaudio.save(str(output_path), wav[0].cpu(), 32000)
        return output_path

    def unload(self):
        del self.model
        self.model = None
        if torch.backends.mps.is_available():
            torch.mps.empty_cache()
```

**Step 2: Commit**

---

## Wave 3: Integration & Assembly

### Task 14: Build final episode assembler

**Files:**
- Create: `src/style_learner/assembly/episode_assembler.py`
- Create: `src/style_learner/assembly/subtitle_generator.py`
- Modify: `src/pipeline/episode_renderer.py` (wire in full TED-Ed pipeline)

**Step 1: Write episode_assembler.py**

Full pipeline: production plan → illustrations → parallax animation → narration → music → transitions → final MP4.

Coordinates sequential model loading/unloading to stay within 16GB:
1. Load SDXL → generate all scene illustrations → unload
2. Load MiDaS → depth-split all illustrations → unload
3. Render parallax frames (CPU/PIL, no GPU needed)
4. Load F5-TTS → generate narration (or use pre-rendered from LUNARC) → unload
5. Load MusicGen → generate background music → unload
6. Load discriminators → score all scenes → unload
7. FFmpeg assembly: scenes + transitions + audio mix → final MP4

**Step 2: Write subtitle_generator.py**

Generate WebVTT subtitles from Whisper word timestamps.

**Step 3: Wire into episode_renderer.py**

Add `render_episode_teded()` entry point that uses the full TED-Ed pipeline.

**Step 4: Commit**

---

### Task 15: Build discriminator inference (local scoring)

**Files:**
- Create: `src/quality/discriminators/inference.py`
- Create: `src/quality/discriminators/prompt_corrector.py`

**Step 1: Write inference.py**

Loads trained discriminator checkpoints, exposes `score()` methods. Handles sequential model loading to stay within memory.

**Step 2: Write prompt_corrector.py**

When semantic discriminator rejects: diagnose via BLIP caption → NLI contradiction → rewrite prompt → regenerate.

**Step 3: Commit**

---

### Task 16: Build LUNARC deployment scripts

**Files:**
- Create: `scripts/lunarc/setup_env.sh`
- Create: `scripts/lunarc/run_full_pipeline.sh`
- Create: `scripts/lunarc/sync_models_local.sh`
- Create: `scripts/lunarc/batch_narration_render.sh`

**Step 1: Write setup_env.sh** — Creates conda env with all LUNARC dependencies

**Step 2: Write run_full_pipeline.sh** — Runs data collection + feature extraction + all training in sequence

**Step 3: Write sync_models_local.sh** — Rsyncs trained models back to local Mac

**Step 4: Write batch_narration_render.sh** — SLURM array job for batch F5-TTS rendering

**Step 5: Commit**

---

### Task 17: Integration test on sample episode

**Files:**
- Create: `src/test_teded_pipeline.py`

**Step 1: Write end-to-end test**

Pick one episode script, run full pipeline:
- Parse script → production plan
- Generate illustrations (or use placeholder images if SDXL not yet trained)
- Parallax animation
- Narration (edge-tts fallback if F5-TTS not ready)
- Music (skip if MusicGen not installed)
- Quality scoring (skip discriminators if not trained)
- Final assembly → MP4

**Step 2: Run test, verify output**

**Step 3: Commit**

---

## Execution Order Summary

```
Wave 1 (can start immediately, no GPU needed):
  Task 1: Scaffolding + requirements
  Task 2: Data collection pipeline
  Task 3: Feature extraction pipeline
  Task 4: Style model training code
  Task 5: SDXL LoRA training scripts
  Task 6: Discriminator training code
  Task 7: F5-TTS training scripts

Wave 2 (local inference code, can start in parallel with Wave 1):
  Task 8: Quality orchestrator
  Task 9: Illustration pipeline (SDXL inference)
  Task 10: Animation system (parallax + reveals)
  Task 11: Production plan generator
  Task 12: Narration pipeline
  Task 13: Music generation

Wave 3 (integration, needs Wave 1+2):
  Task 14: Episode assembler
  Task 15: Discriminator inference
  Task 16: LUNARC deployment scripts
  Task 17: Integration test
```

**After code is written:**
1. Run data collection locally (Task 2)
2. Rsync data to LUNARC
3. Run LUNARC training pipeline (Tasks 3-7 scripts)
4. Rsync models back to local
5. Run full pipeline on sample episodes (Task 17)
6. Iterate on quality
