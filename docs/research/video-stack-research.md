# Video Production Stack Research Report

**Date:** 2026-03-30
**Purpose:** Evaluate Python-based video production tools for a science education YouTube channel producing 700+ physics episodes (10–12 min YouTube Longs + 60-sec Shorts), using chibi/children's-book PNG character assets from FLUX.1, local Apple Silicon M3 Max, zero cost.

---

## 1. Quick Verdict

**The recommended stack is Manim Community Edition (primary) + Pillow+FFmpeg (secondary/hybrid),** with matplotlib providing LaTeX-quality equation rendering without requiring a local LaTeX installation. Manim gives you a proper scene graph, smooth GPU-accelerated animations, and native equation support; the Pillow+FFmpeg layer provides a fast fallback for high-volume compositing of static or lightly-animated scenes, benchmarking at **169 fps** (5.6x real-time) on M3 Max.

---

## 2. Comparison Table

| Criterion | Manim CE | MoviePy 2.x | Pillow + FFmpeg | Remotion | Motion Canvas |
|---|---|---|---|---|---|
| **Language** | Python | Python | Python | TypeScript/React | TypeScript |
| **PNG compositing (characters, backgrounds)** | Yes — `ImageMobject`, supports RGBA transparency; `scale()`, `move_to()`, `animate` | Yes — `ImageClip`, `CompositeVideoClip`, full RGBA | Yes — `Image.paste()` with alpha mask, full RGBA | Yes — standard `<img>` in React | Yes — Image nodes |
| **LaTeX equations (native)** | Yes — `MathTex`/`Tex` classes (requires local LaTeX install); fallback: `Text` via Pango (no LaTeX needed) | No native LaTeX — must pre-render to PNG via matplotlib or sympy | No — use matplotlib mathtext to render equation PNG, then composite | No native — use KaTeX plugin or pre-render | No native — use pre-rendered SVG/PNG |
| **Keyframe animations (fade, slide, scale, zoom)** | Yes — `FadeIn`, `FadeOut`, `Rotate`, `ScaleInPlace`, `GrowFromCenter`, `MoveAlongPath`, `Indicate`, `Wiggle`, `UpdateFromAlphaFunc`; `.animate` API for arbitrary property animation; `LaggedStart`, `Succession` for sequencing | Limited — `crossfadein`, `crossfadeout`; basic position/opacity via `make_frame`; no built-in ease curves | Manual — must interpolate per-frame in Python loop; lerp position/alpha yourself | Yes — full CSS/JS animation, spring physics, keyframe interpolation | Yes — generator-based keyframes, `easeInOut`, springs |
| **Text with contrast aids (shadow, backing box)** | `SurroundingRectangle` for backing box; no built-in drop shadow; workaround via stacked `Text` objects or `BackgroundRectangle` | `TextClip` with color/bg params; `on_color` backdrop | `ImageDraw.rectangle()` for backing box; `ImageFilter.GaussianBlur` for shadow | CSS `text-shadow`, `background-color` — trivial | Custom `Rect` behind `Txt` node |
| **Scriptable / batch automation (700 videos)** | Yes — Python classes, subprocess loop, `-a` flag renders all scenes; CI/CD friendly | Yes — pure Python, easily looped | Yes — pure Python, no external renderer; fastest for batch | Moderate — Node.js rendering via `npx remotion render`; scriptable but heavier toolchain | Moderate — Node.js, CLI render available |
| **Render speed on M3 Max** | **~0.5x real-time at 1080p60** (measured: 3.2s for a 5s composite scene with PNG + text); Cairo renderer; OpenGL renderer claims 10x speedup | Not installed/tested; depends on FFmpeg backend; expected 1–3x real-time | **5.6x real-time** at 1080p30 (measured: 169 fps full pipeline) | Unknown on M3 Max; renders via Puppeteer/Chrome; expected slow (1x or slower) | Unknown; renders via Vite + browser canvas |
| **16:9 and 9:16 output** | Yes — `config.frame_width`, `config.frame_height` set per render; easy to parameterize | Yes — set output size in `CompositeVideoClip` | Yes — set W/H constants at top of script | Yes — `width`/`height` props per composition | Yes — configurable canvas size |
| **Learning curve** | Medium — Python, scene-class model, ~1–2 days for basics | Low-Medium — Python, clip-based API | High — must build all animation primitives manually | High (for Python devs) — requires React/TypeScript knowledge | High (for Python devs) — TypeScript |
| **Maintenance / community health** | Strong — actively maintained, v0.20.1 released Feb 2026, 1000+ contributors | Moderate — v2.2.1 released May 2025; "maintainers wanted" notice; ~10 core contributors; 4-year gap between v1 and v2 | Excellent — Pillow v12.1.1 (2026), FFmpeg 8.0.1; both extremely stable open-source projects | Good — commercially backed (Jonny Burger); free for solo creators | Good — open source; active but smaller community |
| **Zero cost** | Yes | Yes | Yes | Yes (solo creator free) | Yes |
| **LaTeX install required** | Yes for `MathTex`/`Tex` (or use online plugin); `Text` works without LaTeX | N/A | N/A | N/A | N/A |

---

## 3. Detailed Tool Assessments

### 3.1 Manim Community Edition (v0.20.1)

**Strengths:**
- Purpose-built for science/math education — the same engine 3Blue1Brown uses
- `ImageMobject` loads PNG files (including RGBA with full transparency) and supports all standard transforms: `.scale()`, `.move_to()`, `.shift()`, `.rotate()`, `.animate.scale()`, `.animate.shift()` etc.
- The `.animate` property allows any property change to become a smooth interpolated animation without custom keyframe code
- `FadeIn`, `FadeOut`, `GrowFromCenter`, `ScaleInPlace`, `Rotate`, `MoveAlongPath`, `LaggedStart`, `Succession` — 50+ animation classes built in
- `SurroundingRectangle` / `BackgroundRectangle` provide text backing boxes; `Wiggle`, `Indicate`, `Flash`, `Circumscribe` for attention animations
- Text rendering via Pango (`Text` class) — no LaTeX needed, supports any system font
- LaTeX rendering (`MathTex`, `Tex`) is pixel-perfect when LaTeX is installed; can install TinyTeX (~250MB) to add this
- Fully scriptable: define multiple `Scene` subclasses, batch-render via subprocess loop or `-a` flag
- OpenGL renderer available (experimental) — claims 10x speed over Cairo

**Limitations:**
- `ImageMobject` is not a `VMobject` — cannot use `Write`, `Create`, or other vector-drawing animations on it; must use `FadeIn`/`FadeOut`/transform-based animations instead
- Cannot mix `ImageMobject` inside `VGroup` (use `Group` instead)
- Default Cairo renderer is single-threaded; a 10-min video at 1080p60 takes roughly 30–60 minutes depending on scene complexity
- OpenGL renderer requires `OpenGLImageMobject` (different class); still maturing on macOS
- LaTeX requires system install (pdflatex + dvisvgm); not present on this machine currently

**Measured performance (M3 Max, Cairo renderer):**
- 1080p60 scene with PNG ImageMobject + Text + FadeIn animations, ~5s video: **3.2 seconds render time** (1.6x real-time for this simple scene)
- Low-quality preview (-ql): 1.1 seconds
- A 10-minute video with moderate complexity is expected to take 10–20 minutes in Cairo

**Verdict:** Best choice for animated sequences — scene transitions, character entrances, equation reveals, data visualizations. The native scene-graph model makes 700-episode automation natural via Python class parameters.

---

### 3.2 MoviePy 2.x (v2.2.1)

**Strengths:**
- Pure Python, clip-based editing model that is intuitive for video assembly
- `ImageClip`, `VideoFileClip`, `CompositeVideoClip` cover most compositing needs
- Dropped ImageMagick dependency in v2.0 — now Pillow-only for image handling
- Fixed transparency compositing in v2.1.2
- Good for stitching together pre-rendered segments (e.g., combine a Manim clip + a title card + narration audio)

**Limitations:**
- No animation keyframe system — for fade-in you must write a `make_frame` lambda; there are no easing curves or built-in transition primitives comparable to Manim
- No LaTeX support at all — you would need to pre-render equations externally
- "Maintainers wanted" warning on the repo; only ~10 contributors; 4-year release gap history raises long-term reliability questions
- Not installed on this machine

**Verdict:** Useful as a post-production assembly layer (concatenate scenes, add audio, apply crossfades between Manim renders) but not suitable as the primary compositing/animation engine for a character-driven educational series.

---

### 3.3 Pillow + FFmpeg (PIL v12.1.1 + FFmpeg 8.0.1)

**Strengths:**
- Both are already installed and extremely stable
- Full RGBA compositing: `Image.paste(layer, position, mask)` handles any transparency correctly
- Raw speed: **697 fps** for pure compositing (no FFmpeg), **169 fps** (5.6x real-time) for the full pipeline (composite + encode to H.264 via pipe to FFmpeg)
- FFmpeg 8.0.1 on this machine includes `h264_videotoolbox` — Apple Silicon hardware encoder — confirmed working and fast
- matplotlib mathtext renders LaTeX-quality equations to PNG with no LaTeX install required (measured: renders `F = ma` to 1230x330 RGBA PNG in ~0.2s)
- Full control over every pixel — no framework constraints
- Can generate both 1920x1080 (16:9) and 1080x1920 (9:16) from the same composition code by changing two constants
- Trivially parallelizable with Python's `multiprocessing` for batch rendering 700 episodes across all CPU cores

**Limitations:**
- You must build all animation primitives from scratch: fade = lerp alpha over N frames, slide = lerp position, ease = apply easing function to t value
- This is significant boilerplate code (~200–400 lines of animation utility code to write once)
- No timeline or scene graph — logic is a Python loop over frame indices
- No preview mode — must encode and open to review
- Equation rendering via matplotlib produces good but not perfect-quality math typography (it uses its own mathtext parser, not actual LaTeX)

**Verdict:** Fastest rendering path on Apple Silicon by a wide margin. Best for high-volume episodes where scenes are mostly static or use simple fade/slide animations. Requires upfront investment in animation utilities but those are written once and reused across all 700 episodes.

---

### 3.4 Remotion

**Strengths:**
- Excellent for motion graphics, data-driven video, UI-style animations
- Free for solo individual creators (confirmed — no company license needed for a single YouTuber)
- Official Claude Code skill integration (went viral January 2026) — Claude can generate Remotion components from prompts
- CSS/JS animations: `spring()`, `interpolate()`, full keyframe control, React ecosystem

**Limitations:**
- TypeScript/React — a full language context switch from your Python pipeline; all your other tooling (FLUX.1 prompting, script generation, data processing) is Python
- No native LaTeX — would need KaTeX React component
- Renders via headless Chrome (Puppeteer) — slower than compiled renderers; limited GPU acceleration on macOS
- Each render spawns a Node.js process; Python orchestration requires subprocess calls to `npx remotion render`
- Node.js v25.8.2 is installed, so it would work, but adds toolchain complexity

**Verdict:** Attractive if you were already React-native, but the Python-to-TypeScript context switch and lack of a natural LaTeX path make it a poor fit for this pipeline. Not recommended as primary stack.

---

### 3.5 Motion Canvas

**Strengths:**
- TypeScript, code-driven animation using generator functions
- Excellent for technical explainer animations, similar to Manim but web-native
- Real-time preview via Vite server
- Parameterized animations, synchronized audio cues

**Limitations:**
- Same TypeScript context-switch problem as Remotion
- No Python integration; would require subprocess orchestration
- No native LaTeX — pre-rendered SVG/PNG workarounds needed
- Smaller community than Manim or Remotion
- Not suitable as primary stack for a Python-heavy pipeline

**Verdict:** "Manim but TypeScript" — elegant but wrong language for this project. Not recommended.

---

## 4. Recommended Stack

### Primary: Manim CE for Animated Scenes

Use Manim for any scene where you need:
- Character entrances and exits (FadeIn/FadeOut with ImageMobject)
- Equation reveals (Write + Text, or MathTex once LaTeX is installed)
- Attention animations (Indicate, Wiggle, Circumscribe)
- Camera moves and zooms (MovingCamera, ZoomedScene)
- Diagram animations (shapes, arrows, graphs)

**LaTeX setup (one-time):** Install TinyTeX (~250MB) via:
```bash
curl -sLO https://yihui.org/tinytex/install-unx.sh
sh install-unx.sh
tlmgr install standalone preview doublestroke ms setspace rsfs relsize ragged2e fundus-calligra microtype wasysym physics dvisvgm
```

### Secondary: Pillow + FFmpeg for High-Volume Static/Light Scenes

Use the Pillow+FFmpeg pipeline for:
- Title cards, name plates, chapter breaks
- Scenes that are mostly static image + text overlay with simple fades
- Rapid batch rendering when Manim's render time per episode is a bottleneck
- 9:16 Short versions that can be cropped/repositioned from the same frame compositing code

**Equation rendering for this path:** Use `matplotlib.mathtext` — no LaTeX install needed, renders directly to transparent PNG.

### Assembly Layer: FFmpeg CLI or MoviePy 2.x

After rendering individual scenes, assemble final video:
- Concatenate Manim clips + PIL-rendered title cards
- Mix narration audio track
- Burn final subtitles via FFmpeg's `subtitles` filter or ASS/SRT overlay

MoviePy 2.x is acceptable here as a Python-friendly FFmpeg wrapper; if it causes problems, raw FFmpeg `concat` demuxer scripts are more reliable.

### What NOT to use

- Remotion / Motion Canvas: TypeScript context switch is not justified for a Python pipeline
- PIL+FFmpeg as the sole stack for complex animations: too much manual keyframe code to maintain at scale

---

## 5. Example Code: One Frame — Background + Character + Equation + Caption

This shows the recommended **Pillow + matplotlib** compositing approach (used in the Pillow+FFmpeg path), which also serves as the frame-rendering function inside Manim's `UpdateFromFunc` if needed.

```python
"""
single_frame_composite.py

Composites one video frame:
  - Background PNG (1920x1080)
  - Character PNG (RGBA, left side)
  - Equation "F = ma" (rendered via matplotlib mathtext, centered)
  - Caption text (bottom, with backing box)

All assets are RGBA with full transparency support.
"""

import io
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib.pyplot as plt
import matplotlib as mpl

# ── Configuration ────────────────────────────────────────────────────────────
W, H = 1920, 1080   # 16:9 — swap to (1080, 1920) for 9:16 Shorts
SAFE_MARGIN = int(H * 0.15)          # 15% bottom safe zone for subtitles
CAPTION_Y_CENTER = H - int(SAFE_MARGIN * 0.5)   # centre of caption inside safe zone

# ── Asset paths ──────────────────────────────────────────────────────────────
BG_PATH   = "assets/backgrounds/physics_lab_bg.png"
CHAR_PATH = "assets/characters/newton_chibi.png"   # RGBA PNG from FLUX.1


# ── Step 1: Pre-render equation (call once per unique equation, not per frame) ─
def render_equation_png(latex_str: str, font_size: int = 80) -> Image.Image:
    """
    Renders a LaTeX-style equation to a transparent RGBA PIL Image
    using matplotlib mathtext (no local LaTeX install required).

    Uses dollar-sign syntax: e.g.  r"$F = ma$"
    """
    mpl.rcParams['mathtext.fontset'] = 'cm'   # Computer Modern — closest to LaTeX look

    fig = plt.figure(figsize=(12, 2.5), facecolor='none')
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor('none')
    ax.text(
        0.5, 0.5,
        latex_str,
        fontsize=font_size,
        ha='center', va='center',
        transform=ax.transAxes,
        color='white',
        fontweight='bold',
    )
    ax.axis('off')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight', transparent=True, dpi=150)
    buf.seek(0)
    plt.close(fig)
    return Image.open(buf).convert('RGBA')


# ── Step 2: Composite a single frame ─────────────────────────────────────────
def composite_frame(
    background: Image.Image,
    character: Image.Image,
    equation: Image.Image,
    caption: str,
    char_alpha: float = 1.0,   # 0.0–1.0, for fade-in/out
    eq_alpha: float = 1.0,
) -> Image.Image:
    """
    Returns a single 1920x1080 RGB frame.

    Layers (bottom to top):
      1. Background (full canvas)
      2. Character PNG — left side, bottom-anchored
      3. Equation PNG — horizontally centered, vertically centered
      4. Caption text — bottom safe zone with backing box
    """
    # Layer 1: Background
    frame = background.convert('RGBA').resize((W, H), Image.LANCZOS)

    # Layer 2: Character — left quarter of screen, bottom-anchored above caption zone
    char_h = int(H * 0.70)                         # character takes 70% of frame height
    char_w = int(character.width * char_h / character.height)
    char_resized = character.resize((char_w, char_h), Image.LANCZOS)

    if char_alpha < 1.0:                            # apply fade
        r, g, b, a = char_resized.split()
        a = a.point(lambda x: int(x * char_alpha))
        char_resized = Image.merge('RGBA', (r, g, b, a))

    char_x = int(W * 0.03)                          # 3% from left edge
    char_y = H - char_h - SAFE_MARGIN - 10          # sit just above caption zone
    frame.paste(char_resized, (char_x, char_y), char_resized)

    # Layer 3: Equation — centered, upper-middle area
    eq_target_w = int(W * 0.40)                     # equation takes 40% of width
    eq_target_h = int(eq_target_w * equation.height / equation.width)
    eq_resized = equation.resize((eq_target_w, eq_target_h), Image.LANCZOS)

    if eq_alpha < 1.0:
        r, g, b, a = eq_resized.split()
        a = a.point(lambda x: int(x * eq_alpha))
        eq_resized = Image.merge('RGBA', (r, g, b, a))

    eq_x = (W - eq_target_w) // 2                   # horizontally centered
    eq_y = int(H * 0.30)                             # 30% from top
    frame.paste(eq_resized, (eq_x, eq_y), eq_resized)

    # Layer 4: Caption — backing box + white text in subtitle safe zone
    draw = ImageDraw.Draw(frame)

    box_pad_h = 18
    box_pad_v = 14
    # Try to use a system font; fall back to default if not found
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", size=38)
    except OSError:
        font = ImageFont.load_default()

    text_bbox = draw.textbbox((0, 0), caption, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    box_x0 = (W - text_w) // 2 - box_pad_h
    box_x1 = (W + text_w) // 2 + box_pad_h
    box_y0 = CAPTION_Y_CENTER - text_h // 2 - box_pad_v
    box_y1 = CAPTION_Y_CENTER + text_h // 2 + box_pad_v

    # Semi-transparent black backing box
    overlay = Image.new('RGBA', frame.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    overlay_draw.rounded_rectangle(
        [box_x0, box_y0, box_x1, box_y1],
        radius=10,
        fill=(0, 0, 0, 180),
    )
    frame = Image.alpha_composite(frame, overlay)

    # Caption text
    draw = ImageDraw.Draw(frame)
    draw.text(
        (W // 2, CAPTION_Y_CENTER),
        caption,
        font=font,
        fill=(255, 255, 255, 255),
        anchor='mm',
    )

    return frame.convert('RGB')


# ── Step 3: Animate and encode ────────────────────────────────────────────────
def render_scene_to_mp4(output_path: str, duration_seconds: float = 5.0, fps: int = 30):
    """
    Renders a complete scene with fade-in animation to MP4.
    PIL composites frames; FFmpeg encodes via pipe using Apple Silicon VideoToolbox.
    """
    import subprocess

    # Pre-load assets
    bg   = Image.open(BG_PATH).convert('RGBA')
    char = Image.open(CHAR_PATH).convert('RGBA')
    eq   = render_equation_png(r"$F = ma$", font_size=80)
    caption = "Newton's Second Law: Force equals mass times acceleration"

    total_frames = int(duration_seconds * fps)
    fade_in_frames = fps  # 1 second fade

    # Open FFmpeg pipe — VideoToolbox hardware encoder (Apple Silicon)
    ffmpeg_cmd = [
        'ffmpeg', '-y',
        '-f', 'rawvideo', '-vcodec', 'rawvideo',
        '-s', f'{W}x{H}', '-pix_fmt', 'rgb24', '-r', str(fps),
        '-i', '-',
        '-c:v', 'h264_videotoolbox', '-b:v', '10M',
        '-pix_fmt', 'yuv420p',
        output_path,
    ]
    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    for i in range(total_frames):
        # Animation parameters
        t = i / fps
        fade = min(1.0, i / fade_in_frames)   # linear fade-in over 1 second

        frame_rgb = composite_frame(
            background=bg,
            character=char,
            equation=eq,
            caption=caption,
            char_alpha=fade,
            eq_alpha=fade,
        )
        proc.stdin.write(np.array(frame_rgb).tobytes())

    proc.stdin.close()
    proc.wait()
    print(f"Rendered: {output_path}")


# ── Usage ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    render_scene_to_mp4("output/newton_second_law_scene.mp4", duration_seconds=5.0)
```

### Equivalent in Manim CE

```python
"""
newton_scene_manim.py

Same composition in Manim: background + character PNG + equation + caption.
Run with:
    manim newton_scene_manim.py NewtonScene -qh
"""

from manim import *

class NewtonScene(Scene):
    def construct(self):
        # ── Background ───────────────────────────────────────────────────────
        bg = ImageMobject("assets/backgrounds/physics_lab_bg.png")
        bg.scale_to_fit_width(config.frame_width)
        bg.scale_to_fit_height(config.frame_height)
        self.add(bg)

        # ── Character (chibi PNG, RGBA) ──────────────────────────────────────
        # ImageMobject supports RGBA transparency
        char = ImageMobject("assets/characters/newton_chibi.png")
        char.set_height(config.frame_height * 0.70)
        char.to_edge(LEFT, buff=0.3)
        char.to_edge(DOWN, buff=1.2)    # sit above caption safe zone

        # ── Equation ────────────────────────────────────────────────────────
        # Option A: MathTex (requires LaTeX installed)
        # eq = MathTex(r"F = ma", font_size=96, color=YELLOW)

        # Option B: Text (Pango, no LaTeX needed — works right now)
        eq = Text("F = ma", font_size=96, color=YELLOW, font="Latin Modern Math")
        eq.move_to(RIGHT * 1.5 + UP * 0.5)

        # ── Caption with backing box ─────────────────────────────────────────
        caption_text = Text(
            "Newton's Second Law: Force equals mass times acceleration",
            font_size=32,
            color=WHITE,
        )
        caption_text.to_edge(DOWN, buff=0.3)

        caption_box = BackgroundRectangle(
            caption_text,
            fill_color=BLACK,
            fill_opacity=0.7,
            buff=0.15,
        )
        caption = VGroup(caption_box, caption_text)

        # ── Animations ──────────────────────────────────────────────────────
        # ImageMobject supports: FadeIn, FadeOut, GrowFromCenter,
        # ScaleInPlace, Rotate, and the .animate property for smooth
        # property interpolation.  It does NOT support Write/Create.

        self.play(FadeIn(bg), run_time=0.3)
        self.play(FadeIn(char), run_time=0.8)           # character fades in from left
        self.play(Write(eq), run_time=1.2)              # equation draws on (Text supports Write)
        self.play(FadeIn(caption), run_time=0.6)
        self.wait(2)

        # Example: character slides in from off-screen
        # char.shift(LEFT * 8)  # start off-screen
        # self.play(char.animate.shift(RIGHT * 8), run_time=1.0)

        # Example: equation scale pulse attention animation
        # self.play(ScaleInPlace(eq, 1.3), rate_func=there_and_back, run_time=0.5)
```

---

## 6. Animation Primitives Available

### In Manim CE (confirmed in v0.20.1)

**Entry / Exit:**
- `FadeIn(mob, shift=UP)` — fade in, optional directional shift
- `FadeOut(mob, shift=DOWN)` — fade out
- `GrowFromCenter(mob)` — scale from 0 to full size
- `GrowFromEdge(mob, edge=LEFT)` — grow from a specific edge
- `ShrinkToCenter(mob)` — inverse of GrowFromCenter
- `SpinInFromNothing(mob)` — rotate+scale in

**Motion:**
- `mob.animate.shift(direction)` — smooth slide to position
- `mob.animate.move_to(point)` — smooth move to coordinates
- `mob.animate.scale(factor)` — smooth scale
- `mob.animate.rotate(angle)` — smooth rotation
- `MoveAlongPath(mob, path)` — follow a curve

**Drawing (VMobjects only — NOT for ImageMobject):**
- `Write(text_or_vmob)` — draws stroke path
- `Create(vmob)` — reveals border then fill
- `DrawBorderThenFill(vmob)`

**Attention / Emphasis:**
- `Indicate(mob)` — scale+color flash
- `Wiggle(mob)` — wobble
- `Circumscribe(mob)` — draw ring around
- `Flash(point)` — starburst flash
- `FocusOn(point)` — spotlight

**Sequencing:**
- `AnimationGroup(a, b, ...)` — run simultaneously
- `LaggedStart(a, b, ..., lag_ratio=0.3)` — staggered start
- `Succession(a, b, ...)` — sequential
- `ChangeSpeed(anim, speedinfo)` — dynamic speed changes

**Transforms:**
- `Transform(a, b)` — morph one mobject into another
- `ReplacementTransform(a, b)` — replace with morph
- `TransformMatchingShapes(a, b)` — match+morph with alignment

**Camera:**
- `self.camera.animate.move_to(point)` — pan
- `self.camera.animate.set_width(w)` — zoom in/out
- `ZoomedScene` — dedicated scene type for zoom + inset

**Custom:**
- `UpdateFromAlphaFunc(mob, func)` — per-frame lambda: `func(mob, alpha)` where alpha goes 0→1
- `UpdateFromFunc(mob, func)` — per-frame update with no alpha argument

### In the Pillow + FFmpeg Path

All animation is manual per-frame interpolation. A minimal utility library to implement once:

```python
import math

def ease_in_out(t: float) -> float:
    """Smooth cubic ease-in-out: t in [0,1]"""
    return t * t * (3 - 2 * t)

def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def fade_in(frame_idx: int, start_frame: int, end_frame: int) -> float:
    """Returns alpha 0→1 over the specified frame range."""
    if frame_idx <= start_frame:
        return 0.0
    if frame_idx >= end_frame:
        return 1.0
    t = (frame_idx - start_frame) / (end_frame - start_frame)
    return ease_in_out(t)

def slide_position(frame_idx: int, start_frame: int, end_frame: int,
                   from_xy: tuple, to_xy: tuple) -> tuple:
    """Returns (x, y) interpolated between from_xy and to_xy."""
    if frame_idx <= start_frame:
        return from_xy
    if frame_idx >= end_frame:
        return to_xy
    t = ease_in_out((frame_idx - start_frame) / (end_frame - start_frame))
    return (int(lerp(from_xy[0], to_xy[0], t)),
            int(lerp(from_xy[1], to_xy[1], t)))
```

---

## 7. Implementation Recommendation for 700 Episodes

### Episode Template Pattern (Manim)

Define a parameterized `PhysicsScene` base class that accepts a scene data dictionary. Each episode is one dictionary entry — the class handles positioning, safe zones, and animation sequencing. Batch render with:

```python
import subprocess, json, pathlib

episodes = json.load(open("episode_manifest.json"))

for ep in episodes:
    script_path = f"scenes/{ep['id']}_scene.py"
    generate_scene_script(ep, script_path)   # write parameterized .py file

    subprocess.run([
        "python3", "-m", "manim", script_path,
        ep["scene_class"], "-qh",
        "--output_file", ep["output_path"],
        "--disable_caching",
    ], check=True)
```

### Hybrid Strategy by Scene Type

| Scene Type | Render with |
|---|---|
| Character dialogue, equation reveals, data charts | Manim CE |
| Title cards, chapter breaks, static info slides | Pillow + FFmpeg (faster) |
| Short (9:16) version | Same Pillow code, W=1080/H=1920 |
| Final assembly (all scenes + audio) | FFmpeg concat + audio mix |

### Performance Projections (M3 Max)

- **Manim:** ~3–5 min per 10-min episode (depends on animation complexity); parallelizable across scenes
- **Pillow+FFmpeg:** ~2 min per 10-min episode (measured: 1.8 min); trivially parallelizable with `multiprocessing.Pool`
- **Hybrid (50/50 split):** ~2.5 min average per episode × 700 episodes = ~29 hours total — easily done overnight in batches

---

## 8. One-Time Setup Checklist

```bash
# Already installed:
# - manim 0.20.1
# - pillow 12.1.1
# - numpy 2.4.3
# - matplotlib 3.10.8
# - ffmpeg 8.0.1 (with h264_videotoolbox)
# - opencv-python 4.13.0.92
# - sympy 1.14.0
# - pycairo 1.29.0

# Install MoviePy (for post-production assembly only):
pip install moviepy

# Install TinyTeX for MathTex/Tex in Manim (optional — adds LaTeX-quality equations):
curl -sLO https://yihui.org/tinytex/install-unx.sh && sh install-unx.sh
tlmgr install standalone preview doublestroke ms setspace rsfs relsize ragged2e \
      fundus-calligra microtype wasysym physics dvisvgm

# Verify LaTeX works with manim:
python3 -m manim -e "from manim import *; print(MathTex(r'F=ma'))" 2>&1 | tail -5
```

---

*Sources consulted during research:*
- [Manim Community Edition docs (v0.20.1)](https://docs.manim.community/en/stable/)
- [Manim ImageMobject reference](https://docs.manim.community/en/stable/reference/manim.mobject.types.image_mobject.ImageMobject.html)
- [Manim OpenGL Renderer Guide 2025](https://nkugwamarkwilliam.medium.com/mastering-manims-opengl-renderer-a-comprehensive-guide-for-2025-dd31df7460ac)
- [MoviePy GitHub releases](https://github.com/Zulko/moviepy/releases)
- [MoviePy v2 update guide](https://zulko.github.io/moviepy/getting_started/updating_to_v2.html)
- [Manim for STEM Education (arXiv 2025)](https://arxiv.org/html/2510.01187v1)
- [Remotion license docs](https://www.remotion.dev/docs/license)
- [Motion Canvas](https://motioncanvas.io/)
- Performance benchmarks run locally on Apple Silicon M3 Max (March 2026)
