"""
preview_render.py — Render a single 5-second scene from each episode for quick QA.

Usage
-----
  # Render one preview per episode (defaults to scene index 1, the first story scene)
  python3 -m src.pipeline.preview_render

  # Render scene index 0 (opening hook) instead
  python3 -m src.pipeline.preview_render --scene 0

  # Only a specific episode
  python3 -m src.pipeline.preview_render --episode ep01

  # Custom duration and output dir
  python3 -m src.pipeline.preview_render --duration 4 --outdir /tmp/previews
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import tempfile
from pathlib import Path

from src.pipeline.scene_mapper import map_script_to_scenes
from src.pipeline.episode_renderer import build_scene_timeline, _ensure_sibling_audio
from src.pipeline.slide_planner import apply_layout_plan
from src.animation.ffmpeg_export import frames_to_video


def render_preview(
    script_path: str,
    output_mp4: str,
    scene_index: int = 1,
    duration: float = 5.0,
    fps: int = 24,
) -> bool:
    """Render a single-scene preview from one episode script."""
    try:
        audio_path = _ensure_sibling_audio(script_path)
        scenes_json = output_mp4.replace(".mp4", "_scenes.json")
        scenes = map_script_to_scenes(script_path, scenes_json)
        if not scenes:
            print(f"  WARN: no scenes parsed from {Path(script_path).name}")
            return False

        idx = min(scene_index, len(scenes) - 1)
        scene = dict(scenes[idx])
        # Cap duration for quick preview
        scene["duration"] = min(duration, float(scene.get("duration", duration)))
        planned_scene = apply_layout_plan(scene)

        frames_dir = output_mp4.replace(".mp4", "_frames")
        os.makedirs(frames_dir, exist_ok=True)

        tl = build_scene_timeline(planned_scene, fps=fps)
        tl.render_all(frames_dir, verbose=False)
        frames_to_video(frames_dir, output_mp4, fps=fps, audio_path=audio_path or None)

        # Clean up frames
        shutil.rmtree(frames_dir, ignore_errors=True)

        template = scene.get("template", "?")
        archetype = (planned_scene.get("layout_plan") or {}).get("archetype", "?")
        audio_flag = " audio" if audio_path else ""
        print(f"  ✓  {Path(output_mp4).name}  [{template} -> {archetype}{audio_flag}  {scene['duration']:.1f}s]")
        return True

    except Exception as exc:
        print(f"  ✗  {Path(script_path).name}: {exc}", file=sys.stderr)
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Render quick scene previews.")
    parser.add_argument("--scene", type=int, default=1,
                        help="Which scene index to preview (default: 1)")
    parser.add_argument("--duration", type=float, default=5.0,
                        help="Max preview duration in seconds (default: 5)")
    parser.add_argument("--episode", default="",
                        help="Filter to episode name substring (e.g. 'ep01')")
    parser.add_argument("--outdir", default="output/previews",
                        help="Output directory for preview MP4s")
    parser.add_argument("--root", default="output/physics",
                        help="Physics output root")
    args = parser.parse_args()

    out_dir = Path(args.outdir)
    out_dir.mkdir(parents=True, exist_ok=True)
    physics_root = Path(args.root)

    if not physics_root.exists():
        sys.exit(f"ERROR: root not found: {physics_root}")

    scripts = sorted(physics_root.rglob("*_youtube_long.md"))
    if args.episode:
        scripts = [s for s in scripts if args.episode.lower() in s.name.lower()]

    print(f"Rendering {len(scripts)} preview(s) → {out_dir}\n")
    ok = 0
    for script in scripts:
        slug = script.parent.parent.name  # episode dir name
        out_mp4 = str(out_dir / f"preview_{slug}.mp4")
        if render_preview(str(script), out_mp4, scene_index=args.scene,
                          duration=args.duration):
            ok += 1

    print(f"\nDone: {ok}/{len(scripts)} previews rendered.")


if __name__ == "__main__":
    main()
