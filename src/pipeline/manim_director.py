"""
manim_director.py — Uses Claude CLI to generate Manim scene code from episode scripts.

This is the core of the new production pipeline:
    Script.md → Claude CLI → Manim Python code → Manim renders MP4

Usage:
    # Single episode:
    python3 src/pipeline/manim_director.py <script.md> [--output scene.py]

    # Batch all episodes:
    python3 src/pipeline/manim_director.py --batch

    # Then render with Manim:
    manim -qh <scene.py> EpisodeScene
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
    """List available SVG/PNG character assets for the prompt."""
    assets_dir = ROOT / "data" / "assets" / "physics"
    lines = []
    for subdir in ["characters", "objects", "elements"]:
        d = assets_dir / subdir
        if not d.is_dir():
            continue
        files = sorted(f.stem for f in d.glob("*.png") if not f.stem.startswith("."))
        if files:
            lines.append(f"\n{subdir.upper()} ({len(files)}):")
            lines.append(", ".join(files))
    return "\n".join(lines)


DIRECTOR_PROMPT_TEMPLATE = '''You are a visual director generating Manim Community Edition (v0.20) Python code for an educational physics video.

## STYLE: Black & White Comic Line Art
- Background: cream (#FAFAFA)
- All drawings: black ink (#1A1A1A) on white
- Characters: circle heads, dot eyes, simple stick bodies with distinguishing features
- Objects: clean geometric line drawings
- Comic effects: speech/thought bubbles, motion lines, question marks, arrows
- Equations: use MathTex with LaTeX (black on cream)

## MANIM RULES (follow exactly)
1. Use `from manim import *` only
2. Background: `self.camera.background_color = "#FAFAFA"`
3. Colors: INK = "#1A1A1A", LIGHT = "#666666", RED = "#CC0000"
4. Characters are VGroups of Circle (head) + Lines (body) + distinguishing features
5. Use Write() for text appearing, FadeIn() for objects, Create() for shapes
6. Use `self.play()` for animations, `self.wait()` for pauses
7. VISUAL CHANGE EVERY 2-3 SECONDS — never static for more than 3s
8. Show every concept the narrator mentions — if they say "ball", show a ball
9. Use MathTex for equations: `MathTex(r"F = ma", color=INK)`
10. Use Text for labels: `Text("Newton", color=INK, font_size=24, font="sans-serif")`
11. Scene class must be named `EpisodeScene`
12. Use `self.play(*[FadeOut(m) for m in self.mobjects])` to clear between sections

## CHARACTER DRAWING GUIDE
Each character is a VGroup. Example for Aristotle:
```python
def make_aristotle(self):
    head = Circle(radius=0.5, color=INK, stroke_width=3)
    left_eye = Dot(LEFT * 0.15 + UP * 0.08, radius=0.05, color=INK)
    right_eye = Dot(RIGHT * 0.15 + UP * 0.08, radius=0.05, color=INK)
    smile = Arc(radius=0.2, angle=-PI*0.5, start_angle=-PI*0.25, color=INK, stroke_width=2).shift(DOWN*0.12)
    beard = Arc(radius=0.3, angle=-PI*0.7, start_angle=-PI*0.15, color=INK, stroke_width=2).shift(DOWN*0.5)
    torso = Line(DOWN*0.5, DOWN*1.1, color=INK, stroke_width=3)
    l_arm = Line(DOWN*0.65, DOWN*0.9+LEFT*0.4, color=INK, stroke_width=2)
    r_arm = Line(DOWN*0.65, DOWN*0.9+RIGHT*0.4, color=INK, stroke_width=2)
    l_leg = Line(DOWN*1.1, DOWN*1.6+LEFT*0.25, color=INK, stroke_width=2)
    r_leg = Line(DOWN*1.1, DOWN*1.6+RIGHT*0.25, color=INK, stroke_width=2)
    return VGroup(head, left_eye, right_eye, smile, beard, torso, l_arm, r_arm, l_leg, r_leg)
```

Key features per character:
- Newton: wavy wig bumps around head (VMobject with set_points_smoothly), formal coat lines
- Galileo: bald circle on top, pointed beard triangle, telescope prop
- Aristotle: curly beard arc, toga drape lines
- Einstein: wild spiky lines radiating from head, thick mustache line
- Generic scientist: circle head, lab coat rectangle outline

## COMIC EFFECTS
- Speech bubble: SurroundingRectangle + Triangle pointer
- Thought bubble: Ellipse + trailing Dot circles
- Motion lines: VGroup of Lines behind moving object
- Question mark: Text("?", font_size=72)
- Impact: jagged polygon or Cross()
- Arrow: Arrow(start, end) for force/direction

## SPATIAL PLACEMENT RULES (critical for natural-looking scenes)

Objects must be placed with correct spatial relationships:

1. **ON surfaces**: Use `.next_to(surface, UP, buff=0)` for objects on tables/ground
   ```python
   table = Rectangle(width=5, height=0.1, color=INK).shift(DOWN * 1)
   apple = Circle(radius=0.2, color=INK).next_to(table, UP, buff=0)  # apple ON table
   ```

2. **STANDING on ground**: Characters stand on the ground line
   ```python
   ground = Line(LEFT*7, RIGHT*7, color=INK).shift(DOWN*2.5)
   character.next_to(ground, UP, buff=0)  # feet on ground
   ```

3. **Screen zones** — partition the screen to avoid overlap:
   - TOP (y > 2): titles, section headers
   - CENTER (y -1 to 2): main content, characters, diagrams
   - BOTTOM (y < -1): ground, labels, captions
   - LEFT (x < -2): character 1, narrator
   - RIGHT (x > 2): character 2, diagrams
   - CENTER-X: equations, key reveals

4. **Never overlap text with images**:
   - Equations go in empty space (usually center or right)
   - Characters stand to the side (LEFT or RIGHT edge)
   - Labels use `.next_to(object, DOWN/UP, buff=0.2)`
   - Speech bubbles use `.next_to(character, UR, buff=0.3)`

5. **Subtitle safe zone**: Keep bottom 15% (y < -2.8) clear — subtitles go there

6. **Build scenes in layers**:
   - Layer 1: Ground/surface lines (z=0)
   - Layer 2: Background objects — tables, shelves (z=1)
   - Layer 3: Characters and main props (z=2)
   - Layer 4: Text, equations, labels (z=3)
   - Layer 5: Speech bubbles, effects (z=4)

7. **Character + prop composition**:
   ```python
   # Character at left, looking at prop on right
   aristotle.to_edge(LEFT, buff=1)
   ball = Circle(radius=0.3, color=INK)
   ball.move_to(RIGHT * 2 + DOWN * 1)
   ground = Line(LEFT*7, RIGHT*7, color=INK).shift(DOWN * 1.3)
   # Ball is on ground, aristotle stands to the side
   ```

## STRUCTURE
The scene should follow the script's narrative structure:
1. Title card with episode name (centered, clean)
2. Each script section becomes a visual sequence
3. Characters appear when mentioned, placed at LEFT or RIGHT edge
4. Equations are revealed with Write() animation, placed in CENTER
5. Diagrams are built progressively, placed to avoid character overlap
6. Objects are placed with correct spatial relationships (ON surfaces, not floating)
7. Clear transitions between sections (FadeOut all, then new content)
8. NEVER leave the screen empty — always have at least 2 elements visible

## BACKGROUND COMPOSITION
Don't use background images. Instead, compose the background from simple elements:
```python
# Example: laboratory setting
ground = Line(LEFT*7, RIGHT*7, color=INK, stroke_width=1).shift(DOWN*2.5)
table = Rectangle(width=5, height=0.08, color=INK, stroke_width=2).shift(DOWN*0.5)
table_leg_l = Line(table.get_corner(DL), table.get_corner(DL)+DOWN*2, color=INK, stroke_width=2)
table_leg_r = Line(table.get_corner(DR), table.get_corner(DR)+DOWN*2, color=INK, stroke_width=2)
shelf = Line(LEFT*5, LEFT*2, color=INK, stroke_width=2).shift(UP*2)
# Add as group, keep as background
bg = VGroup(ground, table, table_leg_l, table_leg_r, shelf)
self.add(bg)  # add without animation (instant, background)
```

## OUTPUT FORMAT
Output ONLY valid Python code. No markdown fences, no explanations.
The code must be a complete runnable Manim file starting with imports.

## EPISODE SCRIPT
{script_text}'''


def generate_manim_code(
    script_path: str,
    output_path: Optional[str] = None,
    model: str = "sonnet",
) -> str:
    """
    Generate Manim scene code for one episode using Claude CLI.

    Returns the path to the generated .py file.
    """
    script_path = Path(script_path)
    if not script_path.exists():
        raise FileNotFoundError(f"Script not found: {script_path}")

    script_text = script_path.read_text()
    episode_id = script_path.stem.replace("_youtube_long", "").replace("_youtube_short", "")

    prompt = DIRECTOR_PROMPT_TEMPLATE.format(script_text=script_text)

    if output_path is None:
        output_path = script_path.with_name(f"{episode_id}_manim.py")
    else:
        output_path = Path(output_path)

    print(f"  Directing: {script_path.name} → {output_path.name} (claude {model})...")

    cmd = [
        "claude", "-p", prompt,
        "--output-format", "text",
        "--model", model,
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=600,  # 10 min max
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Claude CLI failed (exit {result.returncode}):\n{result.stderr[:1000]}"
        )

    code = result.stdout.strip()

    # Strip markdown fences if present
    code = re.sub(r'^```python\s*\n?', '', code)
    code = re.sub(r'\n?```\s*$', '', code)

    # Basic validation
    if "from manim import" not in code:
        debug_path = script_path.with_suffix(".manim_raw.txt")
        debug_path.write_text(code)
        raise RuntimeError(
            f"Generated code missing manim import. Raw output saved to: {debug_path}"
        )

    if "class EpisodeScene" not in code and "class " not in code:
        # Try to fix: wrap in a Scene class if Claude forgot
        code = f"from manim import *\n\nclass EpisodeScene(Scene):\n    def setup(self):\n        self.camera.background_color = '#FAFAFA'\n\n    def construct(self):\n        pass  # Claude output was not a valid Scene class\n"

    # Syntax check
    try:
        compile(code, str(output_path), "exec")
    except SyntaxError as e:
        debug_path = script_path.with_suffix(".manim_raw.txt")
        debug_path.write_text(code)
        raise RuntimeError(
            f"Generated code has syntax error at line {e.lineno}: {e.msg}\n"
            f"Raw output saved to: {debug_path}"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(code)

    # Count scenes and animations
    scene_count = code.count("class ")
    play_count = code.count("self.play(")
    print(f"  Saved: {output_path} ({scene_count} class(es), {play_count} animations)")

    return str(output_path)


def render_episode(
    manim_path: str,
    quality: str = "h",
    output_dir: Optional[str] = None,
) -> str:
    """
    Render a Manim scene file to MP4.

    Parameters
    ----------
    manim_path : str
        Path to the generated Manim .py file.
    quality : str
        "l" = 480p15, "m" = 720p30, "h" = 1080p60, "k" = 4K60
    output_dir : str, optional
        Override output directory.

    Returns
    -------
    str
        Path to the rendered MP4.
    """
    manim_path = Path(manim_path)

    cmd = ["manim", f"-q{quality}", "--format=mp4"]
    if output_dir:
        cmd += ["--media_dir", output_dir]
    cmd += [str(manim_path), "EpisodeScene"]

    print(f"  Rendering: {manim_path.name} (quality={quality})...")

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=1800,  # 30 min max
        cwd=str(ROOT),
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"Manim render failed:\n{result.stderr[-2000:]}"
        )

    # Find the output MP4
    # Manim outputs to media/videos/<filename>/<quality>/EpisodeScene.mp4
    quality_map = {"l": "480p15", "m": "720p30", "h": "1080p60", "k": "2160p60"}
    q_dir = quality_map.get(quality, "1080p60")
    stem = manim_path.stem
    mp4_path = ROOT / "media" / "videos" / stem / q_dir / "EpisodeScene.mp4"

    if not mp4_path.exists():
        # Try to find it
        found = list((ROOT / "media" / "videos").rglob("EpisodeScene.mp4"))
        if found:
            mp4_path = found[-1]  # most recent
        else:
            raise FileNotFoundError(f"Rendered MP4 not found. Expected: {mp4_path}")

    print(f"  Output: {mp4_path} ({mp4_path.stat().st_size / 1024 / 1024:.1f} MB)")
    return str(mp4_path)


def batch_generate(
    physics_dir: str = "output/physics",
    model: str = "sonnet",
    resume: bool = True,
) -> list[str]:
    """Generate Manim code for all episodes."""
    physics_dir = ROOT / physics_dir
    scripts = sorted(physics_dir.rglob("*_youtube_long.md"))

    print(f"Found {len(scripts)} episode scripts")
    generated = []

    for i, script in enumerate(scripts):
        episode_id = script.stem.replace("_youtube_long", "")
        manim_path = script.with_name(f"{episode_id}_manim.py")

        if resume and manim_path.exists():
            print(f"  [{i+1}/{len(scripts)}] SKIP (exists): {episode_id}")
            continue

        print(f"  [{i+1}/{len(scripts)}] Directing: {episode_id}")
        try:
            generate_manim_code(str(script), str(manim_path), model=model)
            generated.append(str(manim_path))
        except Exception as e:
            print(f"  FAILED: {episode_id}: {e}")

    print(f"\nDone: {len(generated)} new Manim scripts generated")
    return generated


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Generate Manim code using Claude CLI")
    parser.add_argument("script", nargs="?", help="Path to episode script")
    parser.add_argument("--output", "-o", help="Output .py path")
    parser.add_argument("--batch", action="store_true", help="Generate for all episodes")
    parser.add_argument("--model", default="sonnet", choices=["sonnet", "opus", "haiku"])
    parser.add_argument("--render", action="store_true", help="Also render after generating")
    parser.add_argument("--quality", default="h", choices=["l", "m", "h", "k"])
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()

    if args.batch:
        paths = batch_generate(model=args.model, resume=not args.no_resume)
        if args.render:
            for p in paths:
                try:
                    render_episode(p, quality=args.quality)
                except Exception as e:
                    print(f"  Render failed: {e}")
    elif args.script:
        py_path = generate_manim_code(args.script, args.output, model=args.model)
        if args.render:
            render_episode(py_path, quality=args.quality)
    else:
        parser.print_help()
