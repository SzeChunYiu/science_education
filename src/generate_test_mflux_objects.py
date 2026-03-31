"""
Generate non-character test objects locally with mflux using a conservative
memory profile for Apple Silicon laptops.

Design goals:
- fully local, no API usage
- low-RAM mode enabled
- capped MLX cache
- quantized Flux2 Klein 4B
- one image at a time to avoid memory spikes
"""

import argparse
from pathlib import Path
import subprocess
import time


OUT_DIR = Path("data/assets/physics/test_mflux")

OBJECT_STYLE = (
    "children's board-book scene element, simple rounded geometric cutout shapes, "
    "flat matte solid color fills, almost no shading, no glossy highlights, no texture, "
    "no realistic rendering, no 3D look, minimal detail, only 1 to 3 major shape masses, "
    "not a sticker icon, not polished clipart, centered on plain white background"
)

NO_FACE_RULES = (
    "absolutely no face, no eyes, no mouth, no smile, no cheeks, no expression, "
    "no mascot features, not anthropomorphic, no text, no letters, no numbers"
)

OBJECTS = {
    "ball_red_v1.png": (
        f"{OBJECT_STYLE}, simple red rubber ball, one perfect red circle, "
        f"single isolated inanimate object, {NO_FACE_RULES}"
    ),
    "wooden_ramp_v1.png": (
        f"{OBJECT_STYLE}, simple wooden inclined plane ramp, one clean triangular ramp shape, "
        f"single isolated inanimate object, {NO_FACE_RULES}"
    ),
    "telescope_v1.png": (
        f"{OBJECT_STYLE}, simple historical brass telescope on very simple tripod, "
        f"single isolated inanimate object, {NO_FACE_RULES}"
    ),
    "apple_green_v1.png": (
        f"{OBJECT_STYLE}, simple green apple with one leaf and small brown stem, one rounded apple shape, "
        f"single isolated inanimate object, {NO_FACE_RULES}"
    ),
    "tree_round_v1.png": (
        f"{OBJECT_STYLE}, simple tree with one round green canopy and one brown trunk, "
        f"single isolated scene element, {NO_FACE_RULES}"
    ),
    "cloud_fluffy_v1.png": (
        f"{OBJECT_STYLE}, simple fluffy white cloud made of rounded puff shapes, "
        f"single isolated scene element, {NO_FACE_RULES}"
    ),
    "greek_column_v1.png": (
        f"{OBJECT_STYLE}, ancient Greek white marble column, very simple geometric shape, "
        f"single isolated scene element, {NO_FACE_RULES}"
    ),
    "olive_tree_v1.png": (
        f"{OBJECT_STYLE}, simple olive tree with rounded green canopy and brown trunk, "
        f"single isolated scene element, {NO_FACE_RULES}"
    ),
}


def generate_object(filename: str, prompt: str) -> None:
    path = OUT_DIR / filename
    cmd = [
        "mflux-generate-flux2",
        "--base-model",
        "flux2-klein-4b",
        "--lora-style",
        "illustration",
        "--low-ram",
        "--mlx-cache-limit-gb",
        "5",
        "--quantize",
        "4",
        "--steps",
        "4",
        "--guidance",
        "1.0",
        "--width",
        "640",
        "--height",
        "640",
        "--prompt",
        prompt,
        "--output",
        str(path),
    ]
    subprocess.run(cmd, check=True)
    print(f"OK  {filename}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("names", nargs="*", help="Optional filenames to generate")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print("Using local mflux with low-RAM profile:", flush=True)
    print("  model=flux2-klein-4b q4", flush=True)
    print("  low_ram=true", flush=True)
    print("  mlx_cache_limit_gb=5", flush=True)
    print("  steps=4", flush=True)
    print("  size=640x640", flush=True)

    selected = set(args.names) if args.names else None

    for filename, prompt in OBJECTS.items():
        if selected and filename not in selected:
            continue
        path = OUT_DIR / filename
        if path.exists():
            print(f"SKIP {filename}", flush=True)
            continue
        generate_object(filename, prompt)
        time.sleep(1)


if __name__ == "__main__":
    main()
