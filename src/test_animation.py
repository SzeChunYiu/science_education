"""
Integration test for the animation system.

Tests:
1. equation_reveal_scene with "F = ma"
2. character_introduction_scene with a coloured-rectangle placeholder
3. Render both to /tmp/test_frames/{scene_01,scene_02}/
4. Stitch each into /tmp/test_animation_01.mp4 and /tmp/test_animation_02.mp4
5. Optionally concatenate into /tmp/test_animation.mp4
6. Report: frames rendered, file size, duration

Run from the project root:
    python -m src.test_animation
or
    python src/test_animation.py
"""

from __future__ import annotations

import os
import sys
import time

# Ensure project root is on sys.path when run directly
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.animation import (
    equation_reveal_scene,
    character_introduction_scene,
    frames_to_video,
    check_ffmpeg,
    get_video_info,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _hr() -> None:
    print("-" * 60)


def _fmt_bytes(n: int) -> str:
    if n < 1024:
        return f"{n} B"
    if n < 1024 ** 2:
        return f"{n / 1024:.1f} KB"
    return f"{n / 1024 ** 2:.2f} MB"


def render_and_export(
    scene,
    frames_dir: str,
    output_mp4: str,
    label: str,
    fps: int = 30,
) -> dict:
    """Render a SceneTimeline to frames and stitch to MP4.  Returns a stats dict."""
    print(f"\n[{label}]")
    print(f"  Canvas   : {scene.canvas_size[0]}×{scene.canvas_size[1]}")
    print(f"  Duration : {scene.total_frames / fps:.2f}s  ({scene.total_frames} frames @ {fps}fps)")
    print(f"  Elements : {len(scene.elements)}")
    print(f"  Frames → : {frames_dir}")

    t0 = time.perf_counter()
    paths = scene.render_all(frames_dir, verbose=True)
    render_elapsed = time.perf_counter() - t0

    print(f"  Rendered {len(paths)} frames in {render_elapsed:.2f}s")

    print(f"  Stitching → {output_mp4}")
    t1 = time.perf_counter()
    frames_to_video(frames_dir, output_mp4, fps=fps)
    stitch_elapsed = time.perf_counter() - t1
    print(f"  FFmpeg done in {stitch_elapsed:.2f}s")

    info = get_video_info(output_mp4)
    print(f"  Output   : {_fmt_bytes(info['file_size_bytes'])}  "
          f"{info['width']}×{info['height']}  "
          f"{info['duration']:.2f}s  "
          f"{info['fps']:.0f}fps  "
          f"codec={info['codec']}")

    return {
        "label": label,
        "frames": len(paths),
        "render_elapsed": render_elapsed,
        "stitch_elapsed": stitch_elapsed,
        "file_size_bytes": info["file_size_bytes"],
        "duration": info["duration"],
        "resolution": f"{info['width']}×{info['height']}",
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    _hr()
    print("Animation system integration test")
    _hr()

    # FFmpeg check
    if not check_ffmpeg():
        print("ERROR: ffmpeg not found on PATH.  Install with:  brew install ffmpeg")
        sys.exit(1)
    print("ffmpeg: OK")

    results = []

    # ------------------------------------------------------------------ #
    # Scene 1: Equation reveal — "F = ma"                                 #
    # ------------------------------------------------------------------ #
    scene1 = equation_reveal_scene(
        equation_text="F = ma",
        narrator_text="Newton's Second Law: force equals mass times acceleration.",
        background="",               # no background PNG — uses flat colour
        duration=5.0,
        aspect_ratio="16:9",
        background_color=(230, 225, 210),
        fps=30,
    )

    stats1 = render_and_export(
        scene=scene1,
        frames_dir="/tmp/test_frames/scene_01",
        output_mp4="/tmp/test_animation_01.mp4",
        label="Scene 1 — equation_reveal_scene (F = ma)",
        fps=30,
    )
    results.append(stats1)

    # ------------------------------------------------------------------ #
    # Scene 2: Character introduction — Newton, coloured-rect placeholder #
    # ------------------------------------------------------------------ #
    # We don't have a real character PNG in this test.  Pass a non-existent
    # path so the fallback compositor draws a coloured rectangle instead.
    placeholder_char = "/tmp/placeholder_char_newton.png"

    # Create a simple coloured rectangle PNG as the placeholder character
    _create_placeholder_png(placeholder_char, width=256, height=384, color=(139, 109, 75))

    scene2 = character_introduction_scene(
        character_asset=placeholder_char,
        character_name="Isaac Newton",
        year="1687",
        quote='"If I have seen further it is by standing on the shoulders of Giants."',
        background="",
        duration=4.0,
        aspect_ratio="16:9",
        background_color=(200, 220, 240),
        fps=30,
    )

    stats2 = render_and_export(
        scene=scene2,
        frames_dir="/tmp/test_frames/scene_02",
        output_mp4="/tmp/test_animation_02.mp4",
        label="Scene 2 — character_introduction_scene (Newton)",
        fps=30,
    )
    results.append(stats2)

    # ------------------------------------------------------------------ #
    # Summary                                                              #
    # ------------------------------------------------------------------ #
    _hr()
    print("SUMMARY")
    _hr()
    total_frames = 0
    for r in results:
        print(f"\n  {r['label']}")
        print(f"    Frames rendered : {r['frames']}")
        print(f"    Render time     : {r['render_elapsed']:.2f}s")
        print(f"    FFmpeg time     : {r['stitch_elapsed']:.2f}s")
        print(f"    File size       : {_fmt_bytes(r['file_size_bytes'])}")
        print(f"    Duration        : {r['duration']:.2f}s")
        print(f"    Resolution      : {r['resolution']}")
        total_frames += r["frames"]

    _hr()
    print(f"Total frames rendered : {total_frames}")
    print(f"Output files:")
    for path in ["/tmp/test_animation_01.mp4", "/tmp/test_animation_02.mp4"]:
        if os.path.exists(path):
            print(f"  {path}  ({_fmt_bytes(os.path.getsize(path))})")
    _hr()
    print("All tests passed.")


def _create_placeholder_png(
    path: str,
    width: int,
    height: int,
    color: tuple,
) -> None:
    """Create a solid-colour PNG for use as a character placeholder."""
    from PIL import Image, ImageDraw
    img = Image.new("RGBA", (width, height), (*color, 255))
    draw = ImageDraw.Draw(img)
    # Draw a simple smiley face so it looks like a chibi placeholder
    # Head outline
    margin = 20
    face_box = [margin, margin, width - margin, int(height * 0.55)]
    head_color = (255, 220, 180, 255)
    draw.ellipse(face_box, fill=head_color, outline=(80, 60, 40, 255), width=3)
    # Eyes
    eye_y = int(height * 0.22)
    draw.ellipse([int(width * 0.32), eye_y, int(width * 0.42), eye_y + 14],
                 fill=(40, 30, 20, 255))
    draw.ellipse([int(width * 0.58), eye_y, int(width * 0.68), eye_y + 14],
                 fill=(40, 30, 20, 255))
    # Mouth
    mouth_box = [int(width * 0.35), int(height * 0.34),
                 int(width * 0.65), int(height * 0.44)]
    draw.arc(mouth_box, start=0, end=180, fill=(180, 80, 80, 255), width=3)
    # Body (rectangle)
    body_top = int(height * 0.56)
    draw.rectangle(
        [int(width * 0.25), body_top, int(width * 0.75), height - 10],
        fill=(*color, 220),
        outline=(60, 40, 20, 255),
        width=2,
    )
    img.save(path, "PNG")
    print(f"  Created placeholder PNG: {path}")


if __name__ == "__main__":
    main()
