# Style Learner: TED-Ed Quality Video Production Pipeline

## Design Document — v2.0 (Research-Backed Architecture)

> **Core insight from research:** Most TED-Ed animation is NOT complex character
> animation. It is **motion graphics on static illustrations** — pan, zoom,
> parallax layering, and narration-synced reveals. Characters have 2-5 static
> poses, not walk cycles. This is highly automatable.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     LUNARC HPC (A100 80GB)                  │
│                                                             │
│  Training:                    Batch Rendering:              │
│  ├── SDXL Style LoRA         ├── F5-TTS narration (all eps)│
│  ├── Character LoRAs         ├── Manim equation clips      │
│  ├── 3 Discriminators        └── Heavy feature extraction   │
│  └── F5-TTS voice fine-tune                                │
│                                                             │
│  Data Collection:                                           │
│  └── yt-dlp + Whisper + SceneDetect + CLIP features        │
└──────────────────────┬──────────────────────────────────────┘
                       │ rsync models + renders
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  Mac mini M4 16GB (MPS)                     │
│                                                             │
│  Inference:                   Rendering:                    │
│  ├── SDXL + LoRA (~10GB)     ├── PIL compositor (existing) │
│  ├── IP-Adapter (+2GB)       ├── Manim CE (existing)       │
│  ├── Discriminator scoring   ├── Lottie → frames           │
│  ├── F5-TTS preview (~3GB)   ├── FFmpeg assembly           │
│  └── CLIP/ViT scoring        └── MusicGen (~4GB)           │
│                                                             │
│  Note: Models loaded sequentially, not simultaneously      │
└─────────────────────────────────────────────────────────────┘
```

---

## Hardware Constraints

| Resource | LUNARC | Mac mini M4 |
|----------|--------|-------------|
| GPU | A100 80GB (CUDA) | 10-core Apple GPU (MPS) |
| RAM | 512 GB | 16 GB unified |
| Storage | Multi-TB project space | **Limited — 11GB free** |
| Network | No internet on compute nodes | Full internet |
| Role | Training, batch rendering, data collection (login node) | Inference, compositing, final assembly |

**Critical:** All heavy models run sequentially on M4, never simultaneously.
Load SDXL → generate → unload → load discriminators → score → unload → etc.
Use `diffusers` `enable_model_cpu_offload()` for memory management.

---

## Phase 0 — Data Collection (LUNARC login node + local)

### 0a. Download reference videos (local Mac, then rsync)

Download from playlists in `data/style_reference/playlists.txt`:

```
yt-dlp --format mp4 --extract-audio --audio-format mp3 \
  --write-auto-sub --sub-lang en \
  --download-archive data/style_reference/downloaded.txt \
  --output "data/style_reference/%(id)s/video.%(ext)s" \
  --sleep-interval 30 --max-sleep-interval 60 \
  --batch-file data/style_reference/playlists.txt
```

Also download negative examples for discriminator training:
- Kurzgesagt: 20 videos
- Primer: 20 videos
- Crash Course: 20 videos
Store under `data/style_negatives/{channel}/`.

Rsync everything to LUNARC project space for feature extraction.

### 0b. Feature extraction (LUNARC SLURM jobs)

Run as array jobs on GPU nodes:
- **Frame extraction**: ffmpeg at 2fps → `{video_id}/frames/`
- **Scene detection**: PySceneDetect ContentDetector (threshold 27) → `scenes.json`
- **Transcription**: Whisper large-v2 with word timestamps → `transcript.json`
- **CLIP embeddings**: Per-keyframe 512-dim embeddings → `features.json`
- **Colour palettes**: colorthief 4 dominant colours per keyframe
- **Camera motion**: Farneback optical flow → per-scene classification
- **Text detection**: EasyOCR on keyframes → text regions with positions
- **Scene type**: CLIP zero-shot classification against 8 scene descriptions
- **Quality scores**: LAION aesthetic predictor on every 10th frame

### 0c. Assemble training dataset

Aggregate into `data/style_reference/dataset/dataset.jsonl` — one JSON per scene.
Split 80/10/10 by video ID. Save to `splits.json`.

**Tools (all free, all open-source):**
yt-dlp, ffmpeg, PySceneDetect, openai-whisper, CLIP (HuggingFace),
colorthief, EasyOCR, OpenCV (Farneback), simple-aesthetics-predictor

---

## Phase 1 — Style Model Training (LUNARC A100)

### Model 1 — Scene Type Classifier
- Architecture: 2-layer MLP (512→256→8) on frozen CLIP embeddings
- Input: 512-dim CLIP embedding of keyframe
- Output: 8-class softmax (scene types)
- Training: ~5 minutes on A100

### Model 2 — Camera Motion Predictor
- Architecture: 3-layer MLP, two heads (motion type + magnitude)
- Input: 384-dim sentence embedding + 8-dim scene type one-hot
- Output: 8-class motion + 1-dim magnitude
- Training: ~5 minutes on A100

### Model 3 — Text Placement Predictor
- Architecture: 3-layer MLP, four heads (x, y, size, animation)
- Input: scene type + text role + text length + narration phase
- Output: positions + font size + animation style
- Training: ~5 minutes on A100

### Model 4 — Transition Predictor
- Architecture: 3-layer MLP, two heads (type + duration)
- Input: CLIP embeddings of adjacent keyframes + narration phase
- Output: transition type (cut/dissolve/wipe) + duration
- Training: ~5 minutes on A100

**All models save to `models/style_learner/`. Total training: ~20 minutes.**
**All models run inference on CPU in <5 seconds for a 60-scene episode.**

---

## Phase 2 — Illustration System (LUNARC train, M4 infer)

### 2a. Style LoRA training (LUNARC)

Extract 150-200 high-quality TED-Ed keyframes. Auto-caption with CogVLM.
Train SDXL LoRA using kohya_ss/sd-scripts:

```bash
#SBATCH -p gpua100 --gres=gpu:1 --mem=64G -t 2:00:00
accelerate launch sdxl_train_network.py \
  --pretrained_model_name_or_path="stabilityai/stable-diffusion-xl-base-1.0" \
  --network_module=networks.lora --network_dim=32 --network_alpha=16 \
  --resolution=1024 --train_batch_size=4 --max_train_epochs=20 \
  --output_name="teded_style_v1"
```

Training time: **15-25 minutes on A100 80GB**.
Output: `models/style_learner/teded_style_v1.safetensors` (~100-200MB)

### 2b. Character LoRAs (LUNARC)

For each recurring character (Newton, Galileo, Aristotle, etc.):
- 10-30 images per character in various poses
- Train separate LoRA (rank 16-32) per character
- Output: `models/style_learner/characters/{name}.safetensors` (~50-100MB each)

### 2c. Illustration inference (M4 local)

**Stack:** SDXL base + style LoRA (weight 0.8) + character LoRA (weight 0.6)
+ IP-Adapter Plus (for character consistency across scenes)
+ ControlNet lineart (for composition from storyboard sketches)

Memory: ~10-13GB with sequential loading. Fits M4 16GB.
Speed: ~30-60 seconds per 1024x1024 image.

**Generate 4 candidates per scene, score with quality system, accept best.**

### 2d. Prompt assembly

For each scene in the production plan:
1. LLM (Claude) generates visual metaphor description for the concept
2. spaCy NER extracts entities from narration
3. Combine: scene type + entities + colour palette + LoRA trigger + negative prompt

```
teded_style, educational illustration of [concept],
[character] in [pose], [setting],
flat color style, bold outlines, limited palette [hex codes]
Negative: photorealistic, 3d render, dark, blurry, text, watermark
```

---

## Phase 3 — Animation System (M4 local, CPU-based)

### The TED-Ed animation recipe (research-validated)

TED-Ed uses **limited animation** — not full character animation:
- Characters have 2-5 static poses (not walk cycles)
- Motion comes from camera (pan, zoom, parallax)
- Visual reveals are synced to narration timestamps
- Transitions are simple (cut, dissolve, wipe)
- Scene duration: 10-20 seconds each, visual change every 3-5 seconds

### 3a. Multi-layer parallax (extend existing pipeline)

For each scene illustration:
1. Run MiDaS depth estimation → depth map
2. Split into 3 layers (foreground/mid/background) by depth thresholds
3. Apply camera motion from production plan as differential transforms:
   - Foreground: 1.0x motion
   - Midground: 0.6x motion
   - Background: 0.3x motion
4. Render at 30fps using PIL compositor (existing)

### 3b. Narration-synced reveals

Using Whisper word timestamps from narration audio:
- Map each text element to its trigger word in the narration
- Start visual reveal animation 0.1s before the word is spoken
- Use existing primitives: FadeIn, SlideIn, ScaleIn, Pop

### 3c. Character pose system (new)

Build SVG character templates with predefined poses:
- `standing` — default neutral
- `pointing` — arm extended toward something
- `thinking` — hand on chin
- `explaining` — gesturing with both hands
- `reacting` — surprise/eureka expression

Render poses as separate PNG layers. Composite with PIL.
Switch poses at scene boundaries or key narration moments.

### 3d. SVG/Lottie animation for complex motions (new)

For physics demonstrations (pendulum, projectile, wave):
- Define motion as Lottie JSON keyframes
- Use `python-lottie` to render to PIL frames
- Integrate with existing compositor pipeline

For equation animations:
- Continue using Manim CE (already working)

### 3e. Transition library

Implement as FFmpeg filter chains:
- `cut` — hard cut (0ms)
- `dissolve` — crossfade (0.3-0.8s) via `xfade=transition=fade`
- `wipe_left` — directional wipe via `xfade=transition=wipeleft`
- `zoom_in` — scale transition into next scene

---

## Phase 4 — Narration Audio

### 4a. Voice design and fine-tuning (LUNARC)

**Primary TTS: F5-TTS** (~300M params, MPS native, ~3GB memory)

1. Source 15-30 minutes of reference narration audio
   (CC0 voice from LibriVox or record custom)
2. Fine-tune F5-TTS on LUNARC using documented pipeline
3. Batch-render all episode narration as SLURM array job
4. Cache at `output/assets/narration_clips/`

**Local preview: Kokoro** via mlx-audio (~2GB, sub-0.3s, Apache 2.0)
- Use for instant local previews during script iteration
- 82M params, runs natively on Apple Silicon via MLX

**Fallback: edge-tts** (existing, zero-setup, decent quality)

### 4b. Prosody control

F5-TTS uses reference audio for prosody, not SSML. Strategy:
- Control pacing through punctuation and sentence structure in scripts
- Use different reference clips for different emotional tones
- Post-process with ffmpeg for fine speed/pitch adjustments

### 4c. Target specifications (from TED-Ed research)

- Speaking rate: **130-150 WPM** (warm, conversational)
- Script length: **800-900 words** for 4-7 minute videos
- Natural pauses at paragraph boundaries
- Emphasis on key scientific terms

---

## Phase 5 — Music and Sound (M4 local)

### 5a. Background music

**MusicGen** (Meta, MIT license, ~4GB):
```
"gentle educational ambient music, {mood}, instrumental, no vocals, {duration}s"
```
- Generate per-episode music track
- Mix at -18dB under narration
- Check with librosa for silence/clipping

### 5b. Sound effects

Build a local library from **Freesound** (free registration, CC0 clips):
- `whoosh_soft` — for dissolve transitions
- `click` — for text reveals
- `pop` — for element appearances
- `ambient_room` — subtle background

Mix SFX at -12dB. Narration at 0dB (reference).

---

## Phase 6 — Quality System

### 6a. Existing quality checks (keep all)

- Aesthetic scorer (LAION) — threshold >= 5.0 for scenes, >= 5.5 for titles
- Semantic aligner (CLIP cosine) — threshold >= 0.22
- Style consistency (CLIP centroid) — threshold >= 0.85
- Composition checker (rule of thirds, visual balance)
- OCR legibility (for title cards)
- Text contrast (WCAG AA/AAA) — already in layout engine

### 6b. Three discriminators (new, trained on LUNARC)

**Discriminator 1 — Style Judge**
- ViT-Small fine-tuned as binary classifier (TED-Ed vs non-TED-Ed)
- Positive: TED-Ed keyframes. Negative: Kurzgesagt/Primer/CrashCourse + rejected SD outputs
- **Use as post-generation scorer only** (not classifier guidance — too complex for MPS)
- Episode coherence via CLIP centroid (existing), not per-episode fine-tuning
- Threshold: reject below 0.65

**Discriminator 2 — Semantic Coherence Judge**
- 3-layer MLP on CLIP image + sentence-transformer narration embeddings (896-dim → sigmoid)
- Trained on real frame-narration pairs (positive) vs shuffled pairs (negative)
- Supplemented by BLIP caption contradiction check using lightweight
  `blip-image-captioning-base` (~1GB, fits alongside other models)
- Threshold: reject below 0.60 or contradiction > 0.50
- On rejection: prompt self-correction loop (diagnose → rewrite prompt → regenerate)

**Discriminator 3 — Narrative Flow Judge**
- 3-layer MLP on consecutive scene CLIP embeddings + transition type (1027-dim → sigmoid)
- Trained on real consecutive pairs vs shuffled/cross-video pairs
- Runs after all scenes generated — sliding window check
- Cascade limit: max 3 targeted regenerations per episode
- Threshold: flag below 0.60

### 6c. Episode consistency memory

`output/{episode_id}/consistency_memory.json` — updated after each accepted scene:
- Dominant colour palette
- Named visual entities (YOLO)
- Character descriptions (BLIP caption)
- Scene type labels

Injected into SD prompts for subsequent scenes to maintain visual coherence.

### 6d. Quality orchestrator integration

Score aggregation: **minimum threshold per scorer + weighted average for ranking**
(not multiplicative — avoids the compound penalty problem).

```python
# Each scorer has a hard reject threshold
if any(score < threshold for score, threshold in scorer_results):
    reject()

# Rank passing candidates by weighted average
composite = sum(w * s for w, s in zip(weights, scores)) / sum(weights)
accept(best_composite_candidate)
```

Generate 4 candidates per scene. Max 3 regeneration rounds.
If all fail: accept best available, log to `quality_failures.log`.

### 6e. Adversarial retraining (LUNARC, every 10 episodes)

- Collect new positives (accepted scenes) and negatives (rejected scenes)
- Fine-tune from existing checkpoint (not from scratch)
- Only replace checkpoint if validation score improves
- Minimum new examples before retraining triggers

---

## Phase 7 — Production Plan Generator

**Input:** Script from `src/generation/` (markdown format)
**Output:** `output/{topic}/production_plan.json`

For each scene:
```json
{
  "scene_id": 1,
  "narration": "Newton watched an apple fall...",
  "narration_phase": "introducing",
  "visual_metaphor": "Apple falling in slow motion, light rays highlighting trajectory",
  "scene_type": "close-up illustrated object",
  "camera": {"motion": "zoom_in", "magnitude": "slow", "duration": 4.2},
  "character": {"name": "newton", "pose": "thinking"},
  "colour_palette": ["#C4813A", "#6B3A2A", "#F2E4C4"],
  "text_elements": [
    {"content": "1666", "role": "caption", "x": 0.14, "y": 0.87,
     "animation": "fade_in", "trigger_word": "apple"}
  ],
  "sd_prompt": "",
  "transition_out": {"type": "dissolve", "duration": 0.5}
}
```

The `visual_metaphor` field is generated by Claude during script processing.
This is the **creative intelligence layer** — maps abstract concepts to
concrete visual representations.

---

## Phase 8 — Final Assembly (M4 local)

1. Join all scene clips with transitions from production plan (FFmpeg)
2. Sync to narration audio using Whisper timestamps
3. Mix narration + music + SFX (FFmpeg audio mixing)
4. Run flow discriminator check on assembled episode
5. Targeted regeneration of flagged scenes (max 3)
6. Burn in subtitles (WebVTT → SRT → ffmpeg subtitles filter)
7. Output `output/{episode_id}/final_episode.mp4`
8. Generate `output/{episode_id}/quality_report.json`

---

## LUNARC SLURM Workflow Summary

### Conda environment setup
```bash
module load Anaconda3/2024.06-1
conda create -p /projects/hep/fs10/shared/nnbar/billy/packages/style_learner \
  python=3.11 -c conda-forge -y
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
pip install accelerate transformers diffusers safetensors kohya-ss-sd-scripts
pip install f5-tts sentence-transformers easyocr scenedetect[opencv]
pip install openai-whisper colorthief simple-aesthetics-predictor
```

### Job types
| Job | Partition | GPU | Time | Frequency |
|-----|-----------|-----|------|-----------|
| Feature extraction | gpua100 | 1x A100 | 4h | Once (initial data collection) |
| SDXL style LoRA | gpua100 | 1x A100 | 30min | Once + retrain periodically |
| Character LoRAs | gpua100 | 1x A100 | 15min each | Per character |
| Style MLP models (1-4) | gpua100 | 1x A100 | 20min total | Once + retrain |
| 3 Discriminators | gpua100 | 1x A100 | 1-2h total | Once + retrain every 10 eps |
| F5-TTS fine-tune | gpua100 | 1x A100 | 2-4h | Once |
| Batch narration render | gpua100 | 1x A100 | Array job | Per episode batch |
| Manim equation renders | gpua100 | 1x A100 | Array job | Per episode batch |

### Data transfer
```bash
# Local → LUNARC (training data)
rsync -avz data/style_reference/ lunarc:$PROJECT/data/style_reference/

# LUNARC → Local (trained models, ~500MB total)
rsync -avz lunarc:$PROJECT/models/ models/
rsync -avz lunarc:$PROJECT/output/assets/narration_clips/ output/assets/narration_clips/
```

---

## Local Mac mini Disk Strategy

With only 11GB free, the M4 stores only:
- SDXL base model: ~6.5GB (cached in `~/.cache/huggingface/`)
- LoRA weights: ~500MB total (all characters + style)
- Discriminator checkpoints: ~200MB total
- Current episode working files: ~2-3GB
- Episode outputs moved to external storage after completion

**Completed episodes and raw training data live on LUNARC only.**

---

## Technology Stack (All Free, All Open-Source)

| Component | Tool | License | Where |
|-----------|------|---------|-------|
| Image generation | SDXL 1.0 + LoRA | OpenRAIL-M | M4 infer, LUNARC train |
| Character consistency | IP-Adapter Plus | Apache 2.0 | M4 infer |
| Composition control | ControlNet (lineart) | Apache 2.0 | M4 infer |
| Style LoRA training | kohya_ss/sd-scripts | Apache 2.0 | LUNARC |
| Primary TTS | F5-TTS | CC-BY-NC-4.0 | M4 infer, LUNARC train+batch |
| Preview TTS | Kokoro (mlx-audio) | Apache 2.0 | M4 only |
| Fallback TTS | edge-tts | Free (cloud) | M4 only |
| Equation animation | Manim CE | MIT | Both |
| Character animation | python-lottie + SVG rigs | Apache 2.0 | M4 only |
| Music generation | MusicGen (audiocraft) | MIT | M4 infer |
| Depth estimation | MiDaS | MIT | M4 infer |
| Feature extraction | CLIP, Whisper, EasyOCR | Various OSS | LUNARC |
| Scene detection | PySceneDetect | BSD-3 | LUNARC |
| Quality scoring | LAION aesthetic, CLIP | MIT | M4 infer |
| Discriminators | ViT-Small, MLPs (custom) | Custom (yours) | LUNARC train, M4 infer |
| Caption generation | BLIP (base) | BSD-3 | M4 infer |
| NLI checking | DeBERTa-v3-small | MIT | M4 infer |
| Video compositing | FFmpeg | LGPL | Both |
| Image compositing | Pillow | HPND | Both |
| Layout engine | Custom (existing) | Yours | M4 |
| Animation primitives | Custom (existing) | Yours | M4 |

**Total cost: $0** beyond existing LUNARC allocation and Claude Code subscription.

---

## The 80/20: What Creates TED-Ed Feel

From our TED-Ed production analysis, these 5 elements account for ~80% of
perceived quality. Prioritize them above everything else:

1. **Consistent illustration style** — SDXL + style LoRA + IP-Adapter
2. **Professional narration at 130-150 WPM** — F5-TTS fine-tuned voice
3. **Multi-layer parallax motion** — MiDaS depth → 3 layers → differential pan/zoom
4. **Narration-synced visual reveals** — Whisper timestamps → animation triggers
5. **Strong opening hook** — First 10 seconds: question, scenario, or surprising fact

What we can defer without noticeable quality loss:
- Complex character walk cycles (use static pose switches instead)
- Custom music composition (MusicGen ambient is sufficient)
- Full lip sync (no characters need to talk on screen)
- 3D elements or particle effects
- Per-episode LoRA training (single style LoRA is sufficient)

---

## Implementation Order

```
Phase 0: Data collection + feature extraction          [LUNARC]  ~1 day
Phase 1: Train style models (4 MLPs)                   [LUNARC]  ~30 min
Phase 2: Train SDXL style LoRA + character LoRAs        [LUNARC]  ~2 hours
Phase 3: Train discriminators                           [LUNARC]  ~2 hours
Phase 4: Fine-tune F5-TTS voice                         [LUNARC]  ~4 hours
Phase 5: Build illustration pipeline (local inference)  [M4]      ~2 days code
Phase 6: Build animation system (parallax + reveals)    [M4]      ~2 days code
Phase 7: Build quality orchestrator + discriminators    [M4]      ~1 day code
Phase 8: Build production plan generator                [M4]      ~1 day code
Phase 9: Build narration + music pipeline               [M4]      ~1 day code
Phase 10: Build final assembly pipeline                 [M4]      ~1 day code
Phase 11: Integration testing on 3 sample episodes      [Both]    ~1 day
Phase 12: Batch production of all 189 episodes          [Both]    ~ongoing
```
