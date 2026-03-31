"""
Generate all v3 test assets locally with mflux (FLUX.1-schnell).
Covers: objects, characters (v3 flatter style), and backgrounds.

Uses quantized 4-bit schnell + illustration LoRA for flat board-book style.
Low-RAM mode for 16GB Mac.
"""

import argparse
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from style_config import (
    STYLE_PREFIX, STYLE_SUFFIX, BG_RULES, OBJECT_RULES, CHARACTER_RULES,
    BACKGROUNDS,
)

OUT_DIR = Path("data/assets/physics/test_v3")

# ── Separate style prefixes to avoid character contamination in objects ──

# For OBJECTS: no mention of characters at all
OBJ_STYLE = (
    "Flat vector board-book illustration, paper cutout style. "
    "Ultra simplified geometric shape. Bold flat solid color fills. "
    "No shading, no gradients, no texture, no 3D, no realistic rendering. "
    "Clean simple rounded forms. "
    "No text no words no letters no writing anywhere in the image. "
    "CRITICAL: absolutely NO people, NO characters, NO humans, NO figures anywhere. "
    "Just the single object alone."
)

OBJ_NEGATIVE = (
    "person, people, human, man, woman, child, character, figure, face, eyes, mouth, "
    "anthropomorphic, mascot, text, letters, numbers, logo, watermark, realistic, "
    "glossy, shiny, 3d, photo, complex detail, cluttered, gradient, texture, background scene"
)

# For BACKGROUNDS: no people
BG_NEGATIVE = (
    "person, people, human, man, woman, child, character, figure, face, eyes, "
    "text, letters, numbers, logo, watermark, realistic, photo, 3d render"
)

# For CHARACTERS: full style prefix is fine
CHAR_NEGATIVE = (
    "realistic, photo, 3d render, gradient shading, complex detail, "
    "text, letters, numbers, multiple characters, extra people, "
    "eye highlights, eye shine, eye reflections, glossy eyes"
)

# ── Object prompts — NO STYLE_PREFIX, use OBJ_STYLE instead ──
OBJECTS = {
    "obj_ball_red.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple red rubber ball. One perfect solid red circle shape. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
    "obj_wooden_ramp.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple wooden inclined plane ramp. One clean triangular wedge shape in flat brown. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
    "obj_telescope.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple historical brass telescope. One tube shape in flat gold-brown on a tiny tripod. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
    "obj_apple_green.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple green apple with one tiny leaf and short brown stem. One rounded apple shape. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
    "obj_tree_round.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple tree. One solid green circle for canopy on one solid brown rectangle trunk. "
            "Ultra simplified lollipop tree shape. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
    "obj_cloud.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple white fluffy cloud. Three overlapping rounded white puff circle shapes. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
    "obj_greek_column.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple ancient Greek white column. One flat white rectangle with simple rectangular capital on top. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
    "obj_scroll.png": {
        "prompt": (
            f"{OBJ_STYLE} "
            "A single simple rolled parchment scroll. One flat cream-colored cylinder shape with two rolled ends. "
            "Isolated on pure white background with nothing else in the image. "
            f"{OBJECT_RULES}"
        ),
        "w": 512, "h": 512,
    },
}

# ── Character v3 — wooden peg doll, historically recognizable faces ──
CHAR_V3 = {
    "char_aristotle_v3.png": {
        "prompt": (
            "Cute kawaii chibi cartoon of Aristotle the ancient Greek philosopher, full body standing pose. "
            "Very big round head, very small simple body, short stubby arms and legs. "
            "Simple black dot eyes, round pink cheek blush circles, tiny smile. "
            "MUST HAVE: gray curly hair on sides of head, balding on top, full gray beard. "
            "MUST WEAR: white Greek toga chiton draped cloth in flat white cream color. "
            "Brown leather sandals on tiny feet. Holding a rolled parchment scroll. "
            "Flat vector illustration, bold solid color fills, no shading, no gradient, no texture. "
            "Single character only, centered, full body visible from head to feet. "
            "Plain pure white background, isolated character cutout. "
            "No text, no words, no letters anywhere. "
            f"{CHARACTER_RULES}"
        ),
        "w": 512, "h": 768,
    },
    "char_galileo_v3.png": {
        "prompt": (
            "Cute kawaii chibi cartoon of Galileo Galilei the Italian astronomer, full body standing pose. "
            "Very big round head, very small simple body, short stubby arms and legs. "
            "Simple black dot eyes, round pink cheek blush circles, tiny smile. "
            "MUST HAVE: high balding forehead, brown pointed goatee beard, brown mustache, brown hair at sides. "
            "MUST WEAR: dark black Renaissance era scholar robe with wide flat white lace collar. "
            "Black shoes on tiny feet. A small golden telescope on tripod beside him. "
            "Flat vector illustration, bold solid color fills, no shading, no gradient, no texture. "
            "Single character only, centered, full body visible from head to feet. "
            "Plain pure white background, isolated character cutout. "
            "No text, no words, no letters anywhere. "
            f"{CHARACTER_RULES}"
        ),
        "w": 512, "h": 768,
    },
    "char_newton_v3.png": {
        "prompt": (
            "Cute kawaii chibi cartoon of Isaac Newton the English scientist, full body standing pose. "
            "Very big round head, very small simple body, short stubby arms and legs. "
            "Simple black dot eyes, round pink cheek blush circles, tiny smile. "
            "MUST HAVE: large fluffy WHITE curly wig, the wig must be clearly WHITE colored. "
            "MUST WEAR: long brown coat over gold waistcoat, white cravat neck cloth. "
            "Brown shoes on tiny feet. Holding a small bright green apple in one hand. "
            "Flat vector illustration, bold solid color fills, no shading, no gradient, no texture. "
            "Single character only, centered, full body visible from head to feet. "
            "Plain pure white background, isolated character cutout. "
            "No text, no words, no letters anywhere. "
            f"{CHARACTER_RULES}"
        ),
        "w": 512, "h": 768,
    },
}

# ── Separate style for backgrounds — NO character mention at all ──
BG_STYLE = (
    "Flat vector board-book illustration, paper cutout style. "
    "Ultra simplified geometric landscape shapes. Bold flat solid color fills. "
    "No shading, no gradients, no texture, no 3D, no realistic rendering. "
    "Clean simple rounded forms for hills, clouds, and environmental elements. "
    "No text no words no letters no writing anywhere in the image. "
    "CRITICAL: absolutely NO people, NO characters, NO humans, NO figures, NO children, "
    "NO animals, NO creatures, NO silhouettes anywhere in the scene. "
    "This is an EMPTY environment with ZERO living beings."
)

BG_ASSETS = {}
for name, cfg in BACKGROUNDS.items():
    BG_ASSETS[f"bg_{name}.png"] = {
        "prompt": f"{BG_STYLE} {cfg['prompt']} {BG_RULES}",
        "w": cfg["width"],
        "h": cfg["height"],
    }


def get_negative(section: str) -> str:
    if section == "OBJECTS":
        return OBJ_NEGATIVE
    elif section == "BACKGROUNDS":
        return BG_NEGATIVE
    else:
        return CHAR_NEGATIVE


def generate_local(filename: str, prompt: str, w: int, h: int,
                   negative: str = "", use_lora: bool = True) -> bool:
    """Generate one image with local mflux."""
    path = OUT_DIR / filename
    cmd = [
        "mflux-generate",
        "--model", "schnell",
        "--quantize", "4",
        "--low-ram",
        "--steps", "4",
        "--guidance", "1.0",
        "--width", str(w),
        "--height", str(h),
        "--prompt", prompt,
        "--negative-prompt", negative,
        "--output", str(path),
    ]
    if use_lora:
        cmd.extend(["--lora-style", "illustration"])

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
        size_kb = path.stat().st_size / 1024 if path.exists() else 0
        print(f"  OK   {filename} ({size_kb:.0f} KB)")
        return True
    except subprocess.TimeoutExpired:
        print(f"  FAIL {filename}: timeout (>300s)")
        return False
    except subprocess.CalledProcessError as exc:
        print(f"  FAIL {filename}: {exc.stderr[:200] if exc.stderr else exc}")
        return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--only", choices=["objects", "characters", "backgrounds"],
                        help="Only generate one section")
    parser.add_argument("--no-lora", action="store_true",
                        help="Skip illustration LoRA")
    parser.add_argument("--names", nargs="*", help="Only generate specific filenames")
    parser.add_argument("--force", action="store_true", help="Overwrite existing files")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    sections = []
    if not args.only or args.only == "objects":
        sections.append(("OBJECTS", OBJECTS))
    if not args.only or args.only == "characters":
        sections.append(("CHARACTERS v3", CHAR_V3))
    if not args.only or args.only == "backgrounds":
        sections.append(("BACKGROUNDS", BG_ASSETS))

    total = sum(len(s[1]) for s in sections)
    print(f"Local mflux generation: schnell q4 + illustration LoRA")
    print(f"Low-RAM mode, {total} assets into {OUT_DIR}\n")

    stats = {"ok": 0, "skip": 0, "fail": 0}

    for section_name, assets in sections:
        print(f"\n── {section_name} ──")
        negative = get_negative(section_name)
        for filename, cfg in assets.items():
            if args.names and filename not in args.names:
                continue
            path = OUT_DIR / filename
            if path.exists() and not args.force:
                print(f"  SKIP {filename}")
                stats["skip"] += 1
                continue
            if path.exists() and args.force:
                path.unlink()

            success = generate_local(
                filename, cfg["prompt"],
                cfg["w"], cfg["h"],
                negative=negative,
                use_lora=not args.no_lora,
            )
            stats["ok" if success else "fail"] += 1
            time.sleep(2)

    print(f"\n── DONE ──")
    print(f"  Generated: {stats['ok']}")
    print(f"  Skipped:   {stats['skip']}")
    print(f"  Failed:    {stats['fail']}")
    print(f"  Output:    {OUT_DIR}")


if __name__ == "__main__":
    main()
