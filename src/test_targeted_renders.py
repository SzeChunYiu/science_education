"""
test_targeted_renders.py — Render one canonical scene per template type.

Purpose: verify each scene type renders correctly without hunting through
         189 episode scripts. Each test case is a hand-crafted scene dict
         that exercises the template's key visual elements.

Usage:
    python3 src/test_targeted_renders.py

Output:
    output/test_renders/scene_<template>.mp4   (one per test case)
    output/test_renders/test_report.txt
"""

import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.pipeline.episode_renderer import build_scene_timeline, render_episode
from src.pipeline.slide_planner import apply_layout_plan
from src.animation.ffmpeg_export import frames_to_video

# ---------------------------------------------------------------------------
# Output dir
# ---------------------------------------------------------------------------
OUT = ROOT / "output" / "test_renders"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Test scene definitions — one per template
# ---------------------------------------------------------------------------

ASSET_ROOT = ROOT / "data" / "assets" / "physics"

SCENES = [
    # -----------------------------------------------------------------------
    # 1. Equation reveal — tests Manim integration + PIL fallback
    # -----------------------------------------------------------------------
    {
        "scene_id":  "test_equation_reveal",
        "template":  "equation_reveal",
        "duration":  5.0,
        "background": str(ASSET_ROOT / "backgrounds" / "bg_outer_space.png"),
        "elements": [
            {"role": "equation_center", "text": "p = mv",
             "font_size": 72, "color": [255, 255, 255], "scale": 1.0, "padding": 16},
            {"role": "caption", "text": "Momentum equals mass times velocity",
             "font_size": 32, "color": [200, 200, 200], "scale": 1.0, "padding": 8},
        ],
    },

    # -----------------------------------------------------------------------
    # 2. Derivation step — tests multi-line equation build
    # -----------------------------------------------------------------------
    {
        "scene_id":  "test_derivation_step",
        "template":  "derivation_step",
        "duration":  6.0,
        "background": str(ASSET_ROOT / "backgrounds" / "bg_outer_space.png"),
        "elements": [
            {"role": "headline", "text": "F = ma",
             "font_size": 44, "color": [180, 180, 180], "scale": 1.0, "padding": 8},
            {"role": "timeline", "text": "a = F / m",
             "font_size": 60, "color": [255, 255, 255], "scale": 1.0, "padding": 12},
            {"role": "caption", "text": "Rearranging Newton's second law",
             "font_size": 28, "color": [160, 160, 160], "scale": 1.0, "padding": 8},
        ],
    },

    # -----------------------------------------------------------------------
    # 3. Character scene — tests character image + name label exit sync
    #    (the bug: name label must exit with the character, not persist)
    # -----------------------------------------------------------------------
    {
        "scene_id":  "test_character_scene",
        "template":  "character_scene",
        "duration":  5.0,
        "background": str(ASSET_ROOT / "backgrounds" / "bg_grass_field.png"),
        "elements": [
            {"role": "character_center",
             "asset_path": str(ASSET_ROOT / "characters" / "char_newton.png"),
             "text": None, "font_size": 0, "color": [0, 0, 0], "scale": 0.85, "padding": 8},
            {"role": "lower_third", "text": "Isaac Newton · 1687",
             "font_size": 28, "color": [26, 26, 26], "scale": 1.0, "padding": 8},
        ],
    },

    # -----------------------------------------------------------------------
    # 4. Two-element comparison — tests split layout
    # -----------------------------------------------------------------------
    {
        "scene_id":  "test_two_element_comparison",
        "template":  "two_element_comparison",
        "duration":  5.0,
        "background": str(ASSET_ROOT / "backgrounds" / "bg_grass_field.png"),
        "elements": [
            {"role": "character_left",  "text": "High Mass\nSlow velocity",
             "font_size": 34, "color": [26, 26, 26], "scale": 1.0, "padding": 10},
            {"role": "character_right", "text": "Low Mass\nHigh velocity",
             "font_size": 34, "color": [26, 26, 26], "scale": 1.0, "padding": 10},
        ],
    },

    # -----------------------------------------------------------------------
    # 5. Diagram explanation — tests headline + diagram zone + caption
    # -----------------------------------------------------------------------
    {
        "scene_id":  "test_diagram_explanation",
        "template":  "diagram_explanation",
        "duration":  5.0,
        "background": str(ASSET_ROOT / "backgrounds" / "bg_grass_field.png"),
        "elements": [
            {"role": "diagram",
             "asset_path": str(ASSET_ROOT / "objects" / "obj_pendulum.png"),
             "text": "Pendulum in motion",
             "font_size": 28, "color": [40, 40, 40], "scale": 0.9, "padding": 12},
            {"role": "caption", "text": "The pendulum swings with constant period T = 2π√(L/g)",
             "font_size": 30, "color": [60, 60, 60], "scale": 1.0, "padding": 8},
        ],
    },

    # -----------------------------------------------------------------------
    # 6. Narration with caption — tests rolling text / TypeWriter overflow
    # -----------------------------------------------------------------------
    {
        "scene_id":  "test_narration_caption",
        "template":  "narration_with_caption",
        "duration":  5.0,
        "background": str(ASSET_ROOT / "backgrounds" / "bg_ancient_greek_courtyard.png"),
        "elements": [
            {"role": "headline", "text": "Why does anything move at all?",
             "font_size": 40, "color": [26, 26, 26], "scale": 1.0, "padding": 10},
            {"role": "body_text",
             "text": "Aristotle believed that objects needed a constant force to keep moving. "
                     "He had no way to remove friction, so rest seemed like the natural state.",
             "font_size": 30, "color": [60, 60, 60], "scale": 1.0, "padding": 8},
        ],
    },

    # -----------------------------------------------------------------------
    # 7. Animation scene — tests prop asset + motion profile
    # -----------------------------------------------------------------------
    {
        "scene_id":  "test_animation_scene",
        "template":  "animation_scene",
        "duration":  5.0,
        "background": str(ASSET_ROOT / "backgrounds" / "bg_grass_field.png"),
        "elements": [
            {"role": "diagram",
             "asset_path": str(ASSET_ROOT / "objects" / "obj_ball_red.png"),
             "text": "Ball rolling down a ramp",
             "font_size": 28, "color": [40, 40, 40], "scale": 0.8, "padding": 12},
            {"role": "caption", "text": "Acceleration increases as the slope steepens",
             "font_size": 30, "color": [60, 60, 60], "scale": 1.0, "padding": 8},
        ],
    },
]


# ---------------------------------------------------------------------------
# Renderer
# ---------------------------------------------------------------------------

def render_test_scene(scene_dict: dict, aspect_ratio: str = "16:9", fps: int = 24) -> dict:
    name = scene_dict["scene_id"]
    out_mp4 = str(OUT / f"{name}.mp4")
    t0 = time.time()

    try:
        planned = apply_layout_plan(dict(scene_dict), aspect_ratio=aspect_ratio)
        tl = build_scene_timeline(planned, aspect_ratio=aspect_ratio, fps=fps)

        frames_dir = str(OUT / f"{name}_frames")
        os.makedirs(frames_dir, exist_ok=True)
        tl.render_all(frames_dir, verbose=False)
        frames_to_video(frames_dir, out_mp4, fps=fps, crf=23)
        shutil.rmtree(frames_dir, ignore_errors=True)

        size_kb = os.path.getsize(out_mp4) / 1024
        elapsed = time.time() - t0
        print(f"  ✓  {name:<40}  {elapsed:.1f}s  {size_kb:.0f}KB  →  {out_mp4}")
        return {"name": name, "status": "ok", "path": out_mp4,
                "elapsed": elapsed, "size_kb": size_kb}
    except Exception as exc:
        elapsed = time.time() - t0
        print(f"  ✗  {name:<40}  {elapsed:.1f}s  ERROR: {exc}")
        return {"name": name, "status": "error", "error": str(exc), "elapsed": elapsed}


def main():
    print(f"\nTargeted scene render test — {len(SCENES)} scenes → {OUT}\n")
    results = []
    for scene in SCENES:
        r = render_test_scene(scene)
        results.append(r)

    ok  = sum(1 for r in results if r["status"] == "ok")
    err = sum(1 for r in results if r["status"] == "error")
    print(f"\nDone: {ok} passed, {err} failed")

    report = OUT / "test_report.json"
    with open(report, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Report: {report}")


if __name__ == "__main__":
    main()
