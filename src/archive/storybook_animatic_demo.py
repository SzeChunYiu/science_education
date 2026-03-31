from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.animation import (
    check_ffmpeg,
    equation_reveal_scene,
    character_introduction_scene,
    derivation_step_scene,
    diagram_explanation_scene,
    two_character_debate_scene,
    worked_example_scene,
    limits_breakdown_scene,
    historical_moment_scene,
    frames_to_video,
    get_video_info,
)


OUTPUT_ROOT = PROJECT_ROOT / "output" / "_storybook_animatic_demo"
DEFAULT_OUTPUT = OUTPUT_ROOT / "storybook_animatic_reel.mp4"


PALETTE = {
    "cream": (255, 247, 231),
    "butter": (246, 231, 139),
    "teal": (99, 198, 197),
    "sky": (169, 216, 242),
    "peach": (243, 176, 110),
    "coral": (242, 141, 121),
    "pink": (232, 162, 185),
    "lavender": (185, 174, 220),
    "ink": (52, 42, 37),
    "paper": (220, 199, 157),
    "sage": (184, 217, 122),
    "dust": (232, 221, 194),
}


def _ensure_clean_dir(path: Path, force: bool) -> None:
    if path.exists() and force:
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _create_character(
    path: Path,
    *,
    body_color: tuple[int, int, int],
    hair_color: tuple[int, int, int],
    accent_color: tuple[int, int, int],
    style: str,
) -> Path:
    img = Image.new("RGBA", (768, 1024), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Body
    draw.rounded_rectangle([250, 520, 520, 920], radius=56, fill=body_color, outline=PALETTE["ink"], width=8)
    draw.rectangle([310, 610, 460, 920], fill=(*body_color, 255))

    # Head
    draw.ellipse([230, 120, 540, 430], fill=(246, 216, 181), outline=PALETTE["ink"], width=8)

    # Hair / signature shape
    if style == "galileo":
        draw.pieslice([220, 90, 550, 460], 180, 360, fill=hair_color, outline=PALETTE["ink"], width=6)
        draw.arc([245, 165, 525, 430], 210, 330, fill=PALETTE["ink"], width=18)
        draw.line([390, 380, 390, 510], fill=accent_color, width=10)
        draw.line([390, 470, 430, 520], fill=accent_color, width=10)
    elif style == "newton":
        draw.ellipse([170, 110, 600, 430], fill=hair_color, outline=PALETTE["ink"], width=6)
        draw.ellipse([150, 130, 620, 360], fill=hair_color)
        draw.pieslice([155, 80, 615, 450], 180, 360, fill=hair_color, outline=PALETTE["ink"], width=6)
        draw.line([360, 450, 430, 580], fill=body_color, width=18)
        draw.line([430, 580, 500, 650], fill=accent_color, width=14)
    elif style == "aristotle":
        draw.arc([180, 110, 590, 430], 0, 180, fill=hair_color, width=34)
        draw.arc([180, 140, 590, 500], 10, 170, fill=hair_color, width=30)
        draw.ellipse([205, 200, 565, 430], outline=None, fill=(246, 216, 181))
        draw.line([330, 445, 300, 540], fill=accent_color, width=14)
        draw.line([450, 445, 480, 540], fill=accent_color, width=14)
    else:
        draw.ellipse([180, 100, 590, 430], fill=hair_color, outline=PALETTE["ink"], width=6)

    # Eyes
    draw.ellipse([305, 260, 335, 290], fill=PALETTE["ink"])
    draw.ellipse([430, 260, 460, 290], fill=PALETTE["ink"])

    # Cheeks / mouth
    draw.ellipse([270, 310, 300, 340], fill=PALETTE["coral"])
    draw.ellipse([470, 310, 500, 340], fill=PALETTE["coral"])
    draw.arc([330, 300, 440, 360], 10, 170, fill=PALETTE["ink"], width=5)

    # Arms / prop
    draw.line([250, 610, 170, 760], fill=body_color, width=24)
    draw.line([520, 620, 610, 770], fill=body_color, width=24)

    if style == "galileo":
        draw.rectangle([560, 730, 710, 760], fill=(160, 110, 60), outline=PALETTE["ink"], width=4)
        draw.polygon([(700, 700), (730, 720), (720, 780), (690, 760)], fill=(200, 180, 150), outline=PALETTE["ink"])
    elif style == "newton":
        draw.ellipse([540, 700, 620, 780], fill=(122, 182, 85), outline=PALETTE["ink"], width=4)
    elif style == "aristotle":
        draw.polygon([(560, 760), (630, 720), (700, 740), (660, 810)], fill=(232, 220, 190), outline=PALETTE["ink"])

    img.save(path)
    return path


def _create_studio_background(path: Path) -> Path:
    img = Image.new("RGBA", (1920, 1080), PALETTE["cream"] + (255,))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([70, 120, 1850, 980], radius=48, fill=PALETTE["dust"], outline=PALETTE["ink"], width=6)
    draw.rectangle([120, 760, 1800, 930], fill=PALETTE["butter"])
    draw.rectangle([170, 250, 340, 760], fill=PALETTE["sky"], outline=PALETTE["ink"], width=5)
    draw.rectangle([420, 260, 600, 780], fill=PALETTE["teal"], outline=PALETTE["ink"], width=5)
    draw.rectangle([1320, 250, 1680, 760], fill=PALETTE["paper"], outline=PALETTE["ink"], width=5)
    draw.arc([520, 620, 1120, 940], 200, 340, fill=PALETTE["coral"], width=16)
    draw.arc([560, 650, 1180, 980], 200, 350, fill=PALETTE["teal"], width=10)
    draw.polygon([(1220, 790), (1440, 790), (1560, 930), (1100, 930)], fill=PALETTE["sage"], outline=PALETTE["ink"])
    draw.ellipse([760, 220, 1180, 620], fill=PALETTE["cream"], outline=PALETTE["ink"], width=8)
    draw.line([970, 350, 970, 560], fill=PALETTE["ink"], width=8)
    draw.line([870, 460, 1070, 460], fill=PALETTE["ink"], width=8)
    img.save(path)
    return path


def _create_force_diagram(path: Path) -> Path:
    img = Image.new("RGBA", (1600, 900), PALETTE["cream"] + (255,))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([90, 90, 1510, 810], radius=42, fill=(255, 252, 245), outline=PALETTE["ink"], width=6)
    draw.line([250, 640, 1350, 640], fill=PALETTE["ink"], width=12)
    draw.rounded_rectangle([560, 500, 980, 620], radius=24, fill=PALETTE["sky"], outline=PALETTE["ink"], width=6)
    draw.ellipse([650, 390, 890, 630], fill=PALETTE["peach"], outline=PALETTE["ink"], width=6)
    draw.polygon([(760, 450), (1080, 450), (1080, 490), (760, 490)], fill=PALETTE["coral"], outline=PALETTE["ink"])
    draw.polygon([(1080, 470), (1180, 470), (1130, 430)], fill=PALETTE["coral"], outline=PALETTE["ink"])
    draw.line([690, 350, 920, 250], fill=PALETTE["teal"], width=14)
    draw.polygon([(920, 250), (950, 250), (935, 218)], fill=PALETTE["teal"])
    draw.text((660, 300), "F", fill=PALETTE["ink"])
    draw.text((980, 220), "a", fill=PALETTE["ink"])
    draw.text((180, 150), "Force Diagram", fill=PALETTE["ink"])
    draw.text((180, 210), "net force -> acceleration", fill=PALETTE["ink"])
    img.save(path)
    return path


def _create_demo_assets(asset_dir: Path) -> dict[str, Path]:
    asset_dir.mkdir(parents=True, exist_ok=True)
    assets = {
        "galileo": _create_character(
            asset_dir / "char_galileo.png",
            body_color=(220, 202, 176),
            hair_color=(96, 70, 48),
            accent_color=(160, 120, 80),
            style="galileo",
        ),
        "newton": _create_character(
            asset_dir / "char_newton.png",
            body_color=(123, 105, 81),
            hair_color=(240, 238, 230),
            accent_color=(122, 182, 85),
            style="newton",
        ),
        "aristotle": _create_character(
            asset_dir / "char_aristotle.png",
            body_color=(232, 229, 220),
            hair_color=(140, 120, 92),
            accent_color=(170, 132, 92),
            style="aristotle",
        ),
        "studio_bg": _create_studio_background(asset_dir / "bg_studio.png"),
        "force_diagram": _create_force_diagram(asset_dir / "diagram_force.png"),
    }
    return assets


def _build_scenes(assets: dict[str, Path], aspect_ratio: str) -> list[tuple[str, object]]:
    return [
        (
            "01_hook",
            historical_moment_scene(
                character_asset=str(assets["galileo"]),
                setting_background=str(assets["studio_bg"]),
                year_text="Board-book production",
                location_text="Scene design kickoff",
                narration="Warm motion. Clear science. Reusable templates.",
                duration=4.5,
                aspect_ratio=aspect_ratio,
                background_color=PALETTE["cream"],
            ),
        ),
        (
            "02_equation",
            equation_reveal_scene(
                equation_text="F = ma",
                narrator_text="One clean equation reveal can carry a whole lesson.",
                duration=4.0,
                aspect_ratio=aspect_ratio,
                background_color=PALETTE["cream"],
            ),
        ),
        (
            "03_derivation",
            derivation_step_scene(
                previous_line="p = mv",
                new_line="F = dp/dt",
                annotation="A derivation should show the transition, not hide it.",
                duration=4.0,
                aspect_ratio=aspect_ratio,
                background_color=PALETTE["dust"],
            ),
        ),
        (
            "04_diagram",
            diagram_explanation_scene(
                diagram_asset=str(assets["force_diagram"]),
                headline="Simple diagrams beat clutter.",
                caption="Keep the causal arrows readable and the labels close.",
                duration=4.5,
                aspect_ratio=aspect_ratio,
                background_color=PALETTE["cream"],
            ),
        ),
        (
            "05_debate",
            two_character_debate_scene(
                char_left_asset=str(assets["aristotle"]),
                char_left_name="Aristotle",
                char_left_says="Motion needs a cause.",
                char_right_asset=str(assets["newton"]),
                char_right_name="Newton",
                char_right_says="Change in motion needs a cause.",
                duration=5.5,
                aspect_ratio=aspect_ratio,
                background_color=PALETTE["sky"],
            ),
        ),
        (
            "06_example",
            worked_example_scene(
                setup_text="A 2 kg cart accelerates. Find the force.",
                equation_text="F = ma",
                numbers_substituted="F = 2 × 3",
                result_text="F = 6 N",
                duration=6.0,
                aspect_ratio=aspect_ratio,
                background_color=PALETTE["cream"],
            ),
        ),
        (
            "07_limit",
            limits_breakdown_scene(
                equation_text="F = ma",
                limit_text="Useful in the classical limit.",
                warning_text="This is an idealized model, not every case.",
                duration=4.0,
                aspect_ratio=aspect_ratio,
                background_color=PALETTE["paper"],
            ),
        ),
    ]


def _render_clip(scene, clip_dir: Path, fps: int, label: str) -> tuple[Path, dict]:
    frame_dir = clip_dir / "frames"
    clip_path = clip_dir / f"{label}.mp4"
    frame_dir.mkdir(parents=True, exist_ok=True)
    scene.render_all(str(frame_dir), verbose=True)
    frames_to_video(str(frame_dir), str(clip_path), fps=fps)
    info = get_video_info(str(clip_path))
    return clip_path, info


def _concat_clips(clip_paths: list[Path], output_path: Path) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
        list_path = Path(handle.name)
        for clip in clip_paths:
            handle.write(f"file '{clip.as_posix()}'\n")

    cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(list_path),
        "-c",
        "copy",
        str(output_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        fallback = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(list_path),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-crf",
            "18",
            "-preset",
            "medium",
            str(output_path),
        ]
        result = subprocess.run(fallback, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                "ffmpeg concat failed.\n"
                f"stderr:\n{result.stderr[-3000:]}"
            )

    try:
        list_path.unlink(missing_ok=True)
    except TypeError:
        if list_path.exists():
            list_path.unlink()


def main() -> None:
    parser = argparse.ArgumentParser(description="Render a storybook-style animatic reel.")
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--fps", type=int, default=30)
    parser.add_argument("--aspect-ratio", choices=("16:9", "9:16"), default="16:9")
    parser.add_argument("--force", action="store_true", help="Delete the output directory before rendering.")
    args = parser.parse_args()

    if not check_ffmpeg():
        raise RuntimeError("ffmpeg not found on PATH. Install it first.")

    output_dir = args.output_dir.expanduser().resolve()
    output_file = args.output.expanduser().resolve()
    asset_root = output_dir / "assets"
    clip_root = output_dir / "clips"
    frame_root = output_dir / "frames"

    _ensure_clean_dir(output_dir, force=args.force)
    _ensure_clean_dir(asset_root, force=False)
    _ensure_clean_dir(clip_root, force=False)
    _ensure_clean_dir(frame_root, force=False)

    assets = _create_demo_assets(asset_root)
    scenes = _build_scenes(assets, args.aspect_ratio)

    scene_index = []
    clip_paths: list[Path] = []

    for idx, (label, scene) in enumerate(scenes, start=1):
        clip_dir = clip_root / f"{idx:02d}_{label}"
        _ensure_clean_dir(clip_dir, force=True)
        print(f"Rendering {label} -> {clip_dir}")
        clip_path, info = _render_clip(scene, clip_dir, args.fps, label)
        clip_paths.append(clip_path)
        scene_index.append(
            {
                "label": label,
                "clip": str(clip_path),
                "duration": info["duration"],
                "resolution": f"{info['width']}x{info['height']}",
            }
        )

    _concat_clips(clip_paths, output_file)
    final_info = get_video_info(str(output_file))

    manifest = {
        "output": str(output_file),
        "fps": args.fps,
        "aspect_ratio": args.aspect_ratio,
        "scenes": scene_index,
        "final": {
            "duration": final_info["duration"],
            "resolution": f"{final_info['width']}x{final_info['height']}",
            "file_size_bytes": final_info["file_size_bytes"],
        },
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(f"Output: {output_file}")
    print(f"Manifest: {output_dir / 'manifest.json'}")
    print(
        f"Final video: {final_info['width']}x{final_info['height']} "
        f"{final_info['duration']:.2f}s {final_info['file_size_bytes']} bytes"
    )


if __name__ == "__main__":
    main()
