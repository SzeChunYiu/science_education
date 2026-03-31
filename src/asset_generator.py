"""
Automated Asset Generator for Science Education Videos
Uses Hugging Face Inference API (FLUX.1-schnell) — free, zero cost.

Style: Clean flat educational illustration
- Warm colors, simple shapes, bold outlines
- Solid fills, no gradients or 3D
- Consistent across all assets via locked style prefix
"""

import os
import sys
import json
from pathlib import Path
from huggingface_hub import InferenceClient

# ── Style Configuration ──
# This prefix is prepended to EVERY prompt to ensure visual consistency
STYLE_PREFIX = (
    "flat 2D board book illustration, clean vector art style, "
    "simple rounded shapes, solid warm colors, minimal detail, "
    "cute friendly historical character aesthetic, "
    "pastel background, no text, no watermark, high quality"
)

MODEL = "black-forest-labs/FLUX.1-schnell"


def generate_asset(prompt: str, output_path: str, width: int = 1280, height: int = 720):
    """Generate a single illustration asset."""
    full_prompt = f"{STYLE_PREFIX}, {prompt}"
    print(f"  Generating: {os.path.basename(output_path)}")
    print(f"  Prompt: {prompt[:80]}...")

    client = InferenceClient()
    image = client.text_to_image(
        full_prompt,
        model=MODEL,
        width=width,
        height=height,
    )
    image.save(output_path)
    print(f"  ✓ Saved: {output_path}")
    return output_path


def generate_episode_assets(episode_dir: str, asset_list: list[dict]):
    """Generate all assets for an episode."""
    assets_dir = Path(episode_dir) / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    results = []
    for asset in asset_list:
        output_path = str(assets_dir / asset["filename"])
        if os.path.exists(output_path):
            print(f"  ⏭ Already exists: {asset['filename']}")
            results.append(output_path)
            continue

        try:
            path = generate_asset(
                prompt=asset["prompt"],
                output_path=output_path,
                width=asset.get("width", 1280),
                height=asset.get("height", 720),
            )
            results.append(path)
        except Exception as e:
            print(f"  ✗ Failed: {asset['filename']} — {e}")
            results.append(None)

    return results


# ── Episode 1 Asset Definitions ──
EP01_ASSETS = [
    # Characters
    {
        "filename": "aristotle.png",
        "prompt": "cute flat board book character of Aristotle, canonical classical bust likeness, balding crown, curled gray beard, off white Greek chiton and himation, brown sandals, holding clay tablet, full body, centered on plain light background",
        "width": 512,
        "height": 768,
    },
    {
        "filename": "galileo.png",
        "prompt": "cute flat board book character of Galileo Galilei, recognizable portrait likeness, high forehead, pointed brown beard, dark late Renaissance scholar robe, broad white collar, holding a small brass telescope, full body, centered on plain light background",
        "width": 512,
        "height": 768,
    },
    {
        "filename": "newton.png",
        "prompt": "cute flat board book character of Isaac Newton, recognizable portrait likeness, long white curled wig, brown late 17th century coat, waistcoat, white cravat, holding green apple, full body, centered on plain light background",
        "width": 512,
        "height": 768,
    },
    # Scene Backgrounds (16:9)
    {
        "filename": "bg_grass_field.png",
        "prompt": "simple cartoon grass field landscape, green rolling hills, blue sky with soft white clouds, warm sunny day, no characters, wide landscape view, educational video background",
        "width": 1280,
        "height": 720,
    },
    {
        "filename": "bg_ice_rink.png",
        "prompt": "simple cartoon frozen ice lake surface, smooth blue-white ice, snowy mountains in distance, cold winter scene, no characters, wide landscape view, educational video background",
        "width": 1280,
        "height": 720,
    },
    {
        "filename": "bg_outer_space.png",
        "prompt": "simple cartoon outer space scene, dark black-blue background with colorful stars and distant galaxies, no planets close up, calm peaceful space, educational video background",
        "width": 1280,
        "height": 720,
    },
    {
        "filename": "bg_ancient_greece.png",
        "prompt": "simple cartoon ancient Greek scene, white marble columns and steps, olive trees, Mediterranean blue sky, warm sunlight, no characters, educational video background",
        "width": 1280,
        "height": 720,
    },
    # Scene Backgrounds (9:16 vertical)
    {
        "filename": "bg_grass_field_vertical.png",
        "prompt": "simple cartoon grass field landscape, green rolling hills, blue sky with soft white clouds, warm sunny day, no characters, vertical portrait composition, educational video background",
        "width": 720,
        "height": 1280,
    },
    {
        "filename": "bg_ice_rink_vertical.png",
        "prompt": "simple cartoon frozen ice lake surface, smooth blue-white ice, snowy mountains in distance, cold winter scene, no characters, vertical portrait composition, educational video background",
        "width": 720,
        "height": 1280,
    },
    {
        "filename": "bg_outer_space_vertical.png",
        "prompt": "simple cartoon outer space scene, dark background with colorful stars, no planets close up, calm peaceful space, vertical portrait composition, educational video background",
        "width": 720,
        "height": 1280,
    },
    # Objects
    {
        "filename": "ball_red.png",
        "prompt": "cute cartoon red rubber ball, simple round ball with highlight shine, slight shadow underneath, isolated on white background, single object",
        "width": 256,
        "height": 256,
    },
    {
        "filename": "wooden_ramp.png",
        "prompt": "cute cartoon wooden inclined plane ramp, simple brown wooden ramp on a surface, physics experiment equipment, isolated on light background",
        "width": 512,
        "height": 384,
    },
    # Concept Cards
    {
        "filename": "concept_friction.png",
        "prompt": "cute cartoon illustration showing friction concept, a ball being slowed down on a rough surface with small resistance arrows, simple physics diagram, educational",
        "width": 1280,
        "height": 720,
    },
    {
        "filename": "concept_inertia.png",
        "prompt": "cute cartoon illustration showing inertia concept, a ball floating freely in space continuing in a straight line with motion arrows, simple physics diagram, educational",
        "width": 1280,
        "height": 720,
    },
]

# ── Thumbnail Assets ──
THUMBNAIL_ASSETS = [
    {
        "filename": "thumb_aristotle_confused.png",
        "prompt": "cute cartoon Aristotle looking confused at a rolling ball that won't stop, question marks above his head, funny educational scene, dynamic composition",
        "width": 1280,
        "height": 720,
    },
]


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python asset_generator.py <episode_dir>")
        print("Example: python asset_generator.py output/physics/newtons-laws/ep01_why_things_stop")
        sys.exit(1)

    episode_dir = sys.argv[1]
    print(f"\n{'='*60}")
    print(f"Asset Generator — Episode 1: Why Things Stop")
    print(f"Style: {STYLE_PREFIX[:60]}...")
    print(f"Model: {MODEL}")
    print(f"Output: {episode_dir}/assets/")
    print(f"{'='*60}\n")

    all_assets = EP01_ASSETS + THUMBNAIL_ASSETS
    print(f"Generating {len(all_assets)} assets...\n")

    results = generate_episode_assets(episode_dir, all_assets)

    success = sum(1 for r in results if r is not None)
    print(f"\n{'='*60}")
    print(f"Done: {success}/{len(all_assets)} assets generated")
    print(f"{'='*60}")
