# Claude-Directed Video Production Pipeline

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the template-matching scene mapper with a Claude CLI-directed storyboard system, add a visual QA review loop, and clean up dead code.

**Architecture:** Claude CLI generates rich storyboard JSONs from scripts (pre-processing). The renderer consumes these storyboards. After rendering, Claude CLI reviews extracted frames and flags issues. Failed reviews trigger storyboard revision and re-render. This is a compile-time AI director, not runtime.

**Tech Stack:** Claude CLI (`claude -p`), PIL/numpy renderer, FFmpeg, edge-tts, existing animation primitives

---

## Phase 1: Clean Up Dead Code & Commit Baseline

### Task 1: Archive dead code

**Files:**
- Move to `src/archive/`: `layout/engine.py`, `layout/compositor.py`, `layout/contrast.py`, `layout/scene_schema.py`, `animation/physics_diagrams.py`, `animation/circuit_diagrams.py`, `pipeline/batch_processor.py`, `pipeline/preview_render.py`, `pipeline/scene_validator.py`, `pipeline/rename_videos.py`, `storybook_animatic_demo.py`
- Edit: `src/animation/__init__.py` — remove imports of archived modules

**Step 1: Move dead files to archive**
```bash
mkdir -p src/archive/layout src/archive/animation src/archive/pipeline
mv src/layout/engine.py src/archive/layout/
mv src/layout/compositor.py src/archive/layout/
mv src/layout/contrast.py src/archive/layout/
mv src/layout/scene_schema.py src/archive/layout/
mv src/animation/physics_diagrams.py src/archive/animation/
mv src/animation/circuit_diagrams.py src/archive/animation/
mv src/pipeline/batch_processor.py src/archive/pipeline/
mv src/pipeline/preview_render.py src/archive/pipeline/
mv src/pipeline/scene_validator.py src/archive/pipeline/
mv src/pipeline/rename_videos.py src/archive/pipeline/
```

**Step 2: Fix animation/__init__.py imports**
Remove any imports of `circuit_diagrams` or `physics_diagrams` from `src/animation/__init__.py`. These cause `ModuleNotFoundError: No module named 'schemdraw'` on LUNARC.

**Step 3: Verify nothing breaks**
```bash
python3 -c "from src.pipeline.episode_renderer import render_episode; print('OK')"
```
Expected: `OK` (no import errors)

**Step 4: Commit**
```bash
git add -A src/archive/ src/animation/__init__.py src/layout/ src/animation/ src/pipeline/
git commit -m "refactor: archive 11 dead code files (layout engine, physics diagrams, batch processor, etc.)"
```

### Task 2: Stage new files and commit current work

**Step 1: Add all new production files**
```bash
git add src/generate_backgrounds_programmatic.py
git add src/extract_visual_asset_candidates.py
git add src/quality/video_qa.py
git add output/asset_reports/
git add scripts/lunarc/generate_assets.py scripts/lunarc/generate_assets_batch2.py scripts/lunarc/generate_assets_batch3.py
git add scripts/lunarc/regen_backgrounds.py scripts/lunarc/regen_objects.py scripts/lunarc/regen_elements.py
git add scripts/lunarc/generate_missing_assets.sh scripts/lunarc/generate_assets_batch2.sh scripts/lunarc/generate_assets_batch3.sh
git add scripts/lunarc/regen_backgrounds.sh scripts/lunarc/regen_objects.sh scripts/lunarc/regen_elements.sh
git add scripts/lunarc/test_render_episode.sh scripts/lunarc/convert_lora.py
git add data/assets/physics/backgrounds/bg_*.png
git add docs/plans/
```

**Step 2: Commit all modified pipeline files**
```bash
git add src/animation/timeline.py src/animation/scene_types.py
git add src/pipeline/episode_renderer.py src/pipeline/scene_mapper.py
git add src/style_learner/feature_extraction/clip_features.py
git add src/style_learner/training/prepare_lora_dataset.py
git commit -m "feat: optimized renderer (20x speedup), programmatic backgrounds, context-aware scene mapping, video QA checker, 292 assets"
```

---

## Phase 2: Claude CLI Storyboard Generator

### Task 3: Define storyboard JSON schema

**Files:**
- Create: `src/pipeline/storyboard_schema.py`

**Step 1: Write the schema definition**

The storyboard is a list of "beats" — each beat is a timed visual state change. This replaces the flat `scenes.json` format.

```python
"""
Storyboard schema — the contract between Claude CLI (director) and the renderer.

A storyboard is a list of scenes. Each scene has:
- A background
- A list of timed visual beats (element enter/exit/transform events)
- Subtitle text synced to narration

This schema is what Claude CLI outputs and the renderer consumes.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class Beat:
    """A single visual event — an element entering, exiting, or changing."""
    time: float                    # seconds from scene start
    action: str                    # "enter", "exit", "move", "highlight", "transform"
    element_id: str                # unique ID within the scene
    role: str                      # "character", "prop", "equation", "label", "diagram", "accent"
    asset: Optional[str] = None    # asset filename (e.g. "char_newton.png", "obj_ball_red.png")
    text: Optional[str] = None     # text content (for equations, labels, captions)
    x: float = 0.5                 # x position as fraction of canvas width (0.0-1.0)
    y: float = 0.5                 # y position as fraction of canvas height (0.0-1.0)
    w: float = 0.2                 # width as fraction of canvas
    h: float = 0.2                 # height as fraction of canvas
    animation: str = "fade_in"     # animation type: fade_in, slide_left, scale_up, pop, typewriter, none
    duration: float = 0.5          # animation duration in seconds
    font_size: int = 48            # for text elements

@dataclass
class StoryboardScene:
    """One continuous scene with a fixed background."""
    scene_id: str
    background: str                # background asset filename
    duration: float                # total scene duration in seconds
    beats: list[Beat] = field(default_factory=list)
    narrator_text: str = ""        # full narrator text for this scene (used for subtitles)

@dataclass
class Storyboard:
    """Complete episode storyboard — the output of Claude CLI direction."""
    episode_id: str
    title: str
    scenes: list[StoryboardScene] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Serialize to JSON-compatible dict."""
        import dataclasses
        return dataclasses.asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Storyboard":
        """Deserialize from JSON dict."""
        scenes = []
        for s in data.get("scenes", []):
            beats = [Beat(**b) for b in s.pop("beats", [])]
            scenes.append(StoryboardScene(**s, beats=beats))
        return cls(
            episode_id=data["episode_id"],
            title=data.get("title", ""),
            scenes=scenes,
        )
```

**Step 2: Verify syntax**
```bash
python3 -c "import ast; ast.parse(open('src/pipeline/storyboard_schema.py').read()); print('OK')"
```

**Step 3: Commit**
```bash
git add src/pipeline/storyboard_schema.py
git commit -m "feat: add storyboard schema — contract between Claude CLI director and renderer"
```

### Task 4: Build the Claude CLI storyboard generator

**Files:**
- Create: `src/pipeline/storyboard_director.py`

**Step 1: Write the director script**

This script reads an episode script, sends it to `claude -p` with a detailed system prompt, and parses the JSON storyboard output. It runs as a pre-processing step before rendering.

The director prompt must include:
- The full asset library (character names, object names, background names)
- Visual storytelling rules (change every 2-3s, show don't tell, progressive reveal)
- The storyboard JSON schema
- The episode script text

```python
"""
storyboard_director.py — Uses Claude CLI to generate rich visual storyboards.

Usage:
    python3 src/pipeline/storyboard_director.py <script.md> [--output storyboard.json]

    # Batch all episodes:
    python3 src/pipeline/storyboard_director.py --batch output/physics/

This is a PRE-PROCESSING step. Run once per episode, then render from the storyboard.
The storyboard is saved alongside the script as <episode>_storyboard.json.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parents[2]

def _get_asset_inventory() -> str:
    """Scan the asset library and return a formatted list for the prompt."""
    assets_dir = ROOT / "data" / "assets" / "physics"
    inventory = []

    for subdir in ["characters", "backgrounds", "objects", "elements"]:
        d = assets_dir / subdir
        if not d.is_dir():
            continue
        files = sorted(f.stem for f in d.glob("*.png"))
        inventory.append(f"\n### {subdir.title()} ({len(files)} assets)")
        for f in files:
            inventory.append(f"  - {f}")

    return "\n".join(inventory)


def _build_director_prompt(script_text: str, episode_id: str) -> str:
    """Build the full prompt for Claude CLI."""
    asset_inventory = _get_asset_inventory()

    return f"""You are a visual director for an educational YouTube channel producing TED-Ed/Kurzgesagt quality animated videos about physics.

Your job: read this episode script and generate a detailed STORYBOARD in JSON format that tells the renderer exactly what to show on screen at every moment.

## VISUAL STORYTELLING RULES (follow strictly)

1. VISUAL CHANGE EVERY 2-3 SECONDS — never leave the screen static for more than 3s
2. SHOW DON'T TELL — every noun/concept the narrator mentions should have a visual element
3. PROGRESSIVE BUILD — information layers in gradually, not all at once
4. 3-5 ELEMENTS PER SCENE — background + character + 1-3 props/labels minimum
5. MATCH NARRATION — when narrator says "ball rolls", a ball should appear and move
6. USE CORRECT BACKGROUNDS — match the setting described in the script
7. ELEMENT SIZING — characters: w=0.18-0.25, props: w=0.10-0.20, equations: w=0.40-0.60, labels: w=0.25-0.40
8. SAFE ZONES — keep important elements between y=0.08 and y=0.75 (bottom 25% is for subtitles)
9. SCENE BREAKS — start a new scene when the setting/topic changes significantly (every 30-90 seconds)

## AVAILABLE ASSETS
{asset_inventory}

## ANIMATION TYPES
- fade_in: smooth opacity 0→1
- slide_left: enters from right side
- slide_right: enters from left side
- slide_up: enters from bottom
- scale_up: grows from center (good for equations, reveals)
- pop: bouncy scale effect (good for characters, emphasis)
- typewriter: text appears character by character
- none: instant appear (for backgrounds, held elements)

## STORYBOARD JSON FORMAT

Output a JSON object with this exact structure:
```json
{{
  "episode_id": "{episode_id}",
  "title": "Episode Title",
  "scenes": [
    {{
      "scene_id": "scene_01",
      "background": "bg_grass_field",
      "duration": 30.0,
      "narrator_text": "Full narrator text for this scene...",
      "beats": [
        {{
          "time": 0.0,
          "action": "enter",
          "element_id": "ball_1",
          "role": "prop",
          "asset": "obj_ball_red",
          "x": 0.2, "y": 0.5, "w": 0.10, "h": 0.10,
          "animation": "pop",
          "duration": 0.5
        }},
        {{
          "time": 2.0,
          "action": "enter",
          "element_id": "eq_force",
          "role": "equation",
          "text": "F = ma",
          "x": 0.5, "y": 0.3, "w": 0.40, "h": 0.12,
          "animation": "scale_up",
          "duration": 0.8,
          "font_size": 64
        }},
        {{
          "time": 5.0,
          "action": "exit",
          "element_id": "ball_1",
          "animation": "fade_in",
          "duration": 0.3
        }}
      ]
    }}
  ]
}}
```

IMPORTANT:
- Output ONLY the JSON object, no markdown fences, no explanations
- Use ONLY assets from the inventory above (use exact stem names without .png)
- Every scene MUST have at least 3 beats (elements appearing)
- Time values are seconds from the START of that scene
- Background names: use the stem without path (e.g. "bg_study" not "data/assets/.../bg_study.png")

## EPISODE SCRIPT

{script_text}"""


def generate_storyboard(
    script_path: str,
    output_path: Optional[str] = None,
    model: str = "sonnet",
) -> dict:
    """
    Generate a storyboard for one episode using Claude CLI.

    Parameters
    ----------
    script_path : str
        Path to the episode markdown script.
    output_path : str, optional
        Where to save the storyboard JSON. Defaults to <script_dir>/<ep>_storyboard.json.
    model : str
        Claude model to use: "sonnet" (fast, cheap) or "opus" (best quality).

    Returns
    -------
    dict
        The parsed storyboard dictionary.
    """
    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    script_text = script_path.read_text()

    # Extract episode ID from filename
    episode_id = script_path.stem.replace("_youtube_long", "").replace("_youtube_short", "")

    prompt = _build_director_prompt(script_text, episode_id)

    # Call Claude CLI
    print(f"  Directing: {script_path.name} (using claude {model})...")

    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--model", model,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=300,  # 5 min max per episode
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed (exit {result.returncode}):\n{result.stderr[:1000]}"
        )

    # Parse JSON from output (strip any markdown fences if present)
    raw = result.stdout.strip()
    raw = re.sub(r'^```json\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        storyboard = json.loads(raw)
    except json.JSONDecodeError as e:
        # Save raw output for debugging
        debug_path = script_path.with_suffix(".storyboard_raw.txt")
        debug_path.write_text(raw)
        raise RuntimeError(
            f"Failed to parse storyboard JSON: {e}\nRaw output saved to: {debug_path}"
        )

    # Validate basic structure
    if "scenes" not in storyboard:
        raise ValueError("Storyboard missing 'scenes' key")

    # Save storyboard
    if output_path is None:
        output_path = script_path.with_name(f"{episode_id}_storyboard.json")
    else:
        output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(storyboard, indent=2))
    print(f"  Saved: {output_path} ({len(storyboard['scenes'])} scenes, "
          f"{sum(len(s.get('beats', [])) for s in storyboard['scenes'])} beats)")

    return storyboard


def batch_generate(
    physics_dir: str = "output/physics",
    model: str = "sonnet",
    resume: bool = True,
) -> list[str]:
    """Generate storyboards for all episodes."""
    physics_dir = ROOT / physics_dir
    scripts = sorted(physics_dir.rglob("*_youtube_long.md"))

    print(f"Found {len(scripts)} episode scripts")
    generated = []

    for i, script in enumerate(scripts):
        episode_id = script.stem.replace("_youtube_long", "")
        storyboard_path = script.with_name(f"{episode_id}_storyboard.json")

        if resume and storyboard_path.exists():
            print(f"  [{i+1}/{len(scripts)}] SKIP (exists): {episode_id}")
            continue

        print(f"  [{i+1}/{len(scripts)}] Directing: {episode_id}")
        try:
            generate_storyboard(str(script), str(storyboard_path), model=model)
            generated.append(str(storyboard_path))
        except Exception as e:
            print(f"  FAILED: {episode_id}: {e}")

    print(f"\nDone: {len(generated)} new storyboards generated")
    return generated


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate storyboards using Claude CLI")
    parser.add_argument("script", nargs="?", help="Path to episode script (or --batch)")
    parser.add_argument("--output", "-o", help="Output storyboard JSON path")
    parser.add_argument("--batch", action="store_true", help="Generate for all episodes")
    parser.add_argument("--model", default="sonnet", choices=["sonnet", "opus", "haiku"])
    parser.add_argument("--no-resume", action="store_true", help="Regenerate existing storyboards")
    args = parser.parse_args()

    if args.batch:
        batch_generate(model=args.model, resume=not args.no_resume)
    elif args.script:
        generate_storyboard(args.script, args.output, model=args.model)
    else:
        parser.print_help()
```

**Step 2: Verify syntax**
```bash
python3 -c "import ast; ast.parse(open('src/pipeline/storyboard_director.py').read()); print('OK')"
```

**Step 3: Commit**
```bash
git add src/pipeline/storyboard_director.py
git commit -m "feat: Claude CLI storyboard director — AI-driven scene composition from scripts"
```

### Task 5: Build storyboard-to-timeline renderer

**Files:**
- Create: `src/pipeline/storyboard_renderer.py`
- Modify: `src/pipeline/episode_renderer.py` — add storyboard rendering path

**Step 1: Write the storyboard renderer**

This module converts a storyboard JSON (with beats) into SceneTimeline objects that the existing renderer can handle. It bridges the new storyboard format with the existing animation system.

Key logic:
- Each `StoryboardScene` becomes one `SceneTimeline`
- Each `Beat` with action="enter" creates an `ElementTimeline` with the specified animation
- Each `Beat` with action="exit" sets the exit_frame on the matching element
- Asset stems are resolved to full paths via the asset registry
- Text beats become text LayoutElements with specified font_size

**Step 2: Modify episode_renderer.py to prefer storyboard**

In `render_episode()`, before calling `map_script_to_scenes()`:
1. Check if `<episode>_storyboard.json` exists next to the script
2. If yes, load it and use `storyboard_to_timelines()` instead of the template mapper
3. If no, fall back to the existing `map_script_to_scenes()` path

This makes the storyboard opt-in — episodes without storyboards still render with the old pipeline.

**Step 3: Commit**
```bash
git add src/pipeline/storyboard_renderer.py src/pipeline/episode_renderer.py
git commit -m "feat: storyboard renderer — bridges Claude storyboards to animation timeline"
```

### Task 6: Build the Claude CLI QA reviewer

**Files:**
- Create: `src/quality/frame_reviewer.py`

**Step 1: Write the frame reviewer**

This script extracts frames from a rendered video, sends them to Claude CLI for visual review, and outputs a structured QA report.

Key design:
- Extract 1 frame per scene transition + 1 per 15 seconds
- Send frames to `claude -p` with a review prompt asking for scores on: visual richness, context match, readability, scientific accuracy, professional quality
- Parse the JSON response into a QA report
- Return pass/fail + specific issues with timestamps

The review prompt includes:
- The original script text (for context matching)
- The storyboard (for checking if beats were rendered correctly)
- The frames as images

```bash
# Usage:
python3 src/quality/frame_reviewer.py output/test_renders/ep01_v3.mp4 \
    --script output/physics/.../ep01_youtube_long.md \
    --storyboard output/physics/.../ep01_storyboard.json
```

**Step 2: Commit**
```bash
git add src/quality/frame_reviewer.py
git commit -m "feat: Claude CLI frame reviewer — AI quality gate for rendered videos"
```

### Task 7: Build the revision loop orchestrator

**Files:**
- Create: `src/pipeline/production_loop.py`

**Step 1: Write the production loop**

This is the top-level orchestrator that ties everything together:

```
for each episode:
    1. Generate storyboard (Claude CLI) — if not exists
    2. Render episode (existing renderer + storyboard)
    3. Review frames (Claude CLI) — extract + score
    4. If QA passes → mark as done
    5. If QA fails → feed issues back to Claude CLI
       → regenerate storyboard with fixes
       → re-render → re-review (max 3 iterations)
```

```bash
# Usage:
# Single episode:
python3 src/pipeline/production_loop.py output/physics/.../ep01_youtube_long.md

# All episodes:
python3 src/pipeline/production_loop.py --batch --workers 4
```

**Step 2: Commit**
```bash
git add src/pipeline/production_loop.py
git commit -m "feat: production loop — direct → render → review → revise cycle"
```

---

## Phase 3: Integration & Testing

### Task 8: Test storyboard generation on ep01

**Step 1: Generate storyboard for ep01**
```bash
python3 src/pipeline/storyboard_director.py \
    output/physics/01_classical_mechanics/01_newtons_laws/ep01_why_things_stop/scripts/ep01_youtube_long.md
```
Expected: Creates `ep01_storyboard.json` with 8-15 scenes, 40+ beats

**Step 2: Review the storyboard quality**
```bash
python3 -c "
import json
sb = json.load(open('output/physics/01_classical_mechanics/01_newtons_laws/ep01_why_things_stop/scripts/ep01_storyboard.json'))
for s in sb['scenes']:
    print(f\"{s['scene_id']}: {s['background']} ({s['duration']}s, {len(s['beats'])} beats)\")
    for b in s['beats'][:3]:
        print(f\"  {b['time']}s: {b['action']} {b.get('asset', b.get('text', ''))[:40]}\")
"
```

**Step 3: Render from storyboard**
Submit as SLURM job on LUNARC (sync files first).

**Step 4: Extract frames and compare v3 (template) vs v4 (storyboard)**
Visual side-by-side comparison of the same episode.

**Step 5: Commit test results**
```bash
git commit -m "test: ep01 storyboard generation and rendering verified"
```

### Task 9: Run QA review loop on ep01

**Step 1: Run frame reviewer on rendered ep01**
```bash
python3 src/quality/frame_reviewer.py output/test_renders/ep01_v4.mp4 \
    --script output/physics/.../ep01_youtube_long.md
```

**Step 2: If QA fails, run revision**
```bash
python3 src/pipeline/production_loop.py output/physics/.../ep01_youtube_long.md --max-revisions 2
```

**Step 3: Compare final output**
Download and screenshot the revised video.

### Task 10: Sync everything to LUNARC and final commit

**Step 1: Sync all code**
```bash
rsync -avz --exclude='__pycache__' --exclude='.git' --exclude='output/' \
    src/ lunarc:/projects/hep/fs10/shared/nnbar/billy/science_education/src/
```

**Step 2: Final commit with all changes**
```bash
git add -A
git commit -m "feat: Claude-directed production pipeline — storyboard generation, rendering, QA review loop

- Claude CLI generates rich storyboards (3-5 elements per scene, timed beats)
- Storyboard renderer bridges to existing animation system
- Frame reviewer provides AI quality gate
- Production loop orchestrates direct → render → review → revise cycle
- Archived 11 dead code files
- 292 assets (51 characters, 38 backgrounds, 110 objects, 38 elements)
- Programmatic backgrounds (PIL-generated, consistent style)
- 20x render speedup (FFmpeg pipe, parallel scenes, duplicate frame skip)
- Context-aware background selection using narrator text"
```

---

## File Summary

| Action | File | Purpose |
|--------|------|---------|
| CREATE | `src/pipeline/storyboard_schema.py` | Storyboard JSON data classes |
| CREATE | `src/pipeline/storyboard_director.py` | Claude CLI storyboard generation |
| CREATE | `src/pipeline/storyboard_renderer.py` | Storyboard → SceneTimeline conversion |
| CREATE | `src/quality/frame_reviewer.py` | Claude CLI frame review & QA scoring |
| CREATE | `src/pipeline/production_loop.py` | Orchestrator: direct → render → review → revise |
| MODIFY | `src/pipeline/episode_renderer.py` | Add storyboard rendering path |
| MODIFY | `src/animation/__init__.py` | Remove dead imports |
| MOVE   | 11 files → `src/archive/` | Dead code cleanup |
| COMMIT | All modified + new files | Clean git history |
