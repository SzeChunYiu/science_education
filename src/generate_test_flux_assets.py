"""
Generate a clean FLUX API test pack for style evaluation.

This uses the same Hugging Face Inference API baseline as the approved
char_*_v2 character samples.
"""

import os
from pathlib import Path
import subprocess
import time

import requests


API_URL = "https://router.huggingface.co/hf-inference/models/black-forest-labs/FLUX.1-schnell"
OUT_DIR = Path("data/assets/physics/test_mflux")
TOKEN_PATH = Path.home() / ".cache" / "huggingface" / "token"
LOCAL_NEGATIVE = (
    "face, eyes, mouth, smile, cheeks, expression, anthropomorphic, mascot, character, person, "
    "text, letters, numbers, logo, watermark, realistic, glossy, shiny, 3d, photo, render, "
    "complex, detailed, cluttered"
)

OBJECT_STYLE = (
    "children's board-book scene element, simple rounded geometric cutout shapes, "
    "flat solid color fills, almost no shading, no glossy highlights, no texture, "
    "no realistic rendering, no 3D look, minimal detail, centered on plain white background"
)

NO_FACE_RULES = (
    "absolutely no face, no eyes, no mouth, no smile, no cheeks, no expression, "
    "no mascot features, not anthropomorphic, no text, no letters, no numbers"
)


ASSETS = {
    "char_aristotle_v2.png": (
        "cute cartoon Aristotle ancient Greek philosopher, elderly man with gray beard, "
        "wearing white draped toga, holding rolled parchment scroll, kawaii chibi proportions, "
        "big round head, tiny body, flat vector illustration style, pastel warm colors, "
        "white background, isolated, no text"
    ),
    "char_galileo_v2.png": (
        "cute cartoon Galileo Galilei Renaissance scientist, brown beard, wearing dark Renaissance robe, "
        "small brass telescope beside him, kawaii chibi proportions, big round head, tiny body, "
        "flat vector illustration style, pastel warm colors, white background, isolated, no text"
    ),
    "char_newton_v2.png": (
        "cute cartoon Isaac Newton English scientist, white powdered wig, wearing brown historical coat "
        "with white collar, holding small green apple, kawaii chibi proportions, big round head, tiny body, "
        "flat vector illustration style, pastel warm colors, white background, isolated, no text"
    ),
    "ball_red_v1.png": (
        f"{OBJECT_STYLE}, simple red rubber ball, one perfect red circle, single isolated inanimate object, "
        f"{NO_FACE_RULES}"
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


def generate_asset(filename: str, prompt: str) -> None:
    headers = {}
    token = os.environ.get("HF_TOKEN")
    if not token and TOKEN_PATH.exists():
        token = TOKEN_PATH.read_text().strip()
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = requests.post(API_URL, headers=headers, json={"inputs": prompt}, timeout=300)
    response.raise_for_status()
    if "image" not in response.headers.get("content-type", ""):
        raise RuntimeError(f"Unexpected response type for {filename}: {response.headers.get('content-type')}")

    path = OUT_DIR / filename
    path.write_bytes(response.content)
    print(f"OK  {filename}", flush=True)


def generate_asset_local(filename: str, prompt: str) -> None:
    path = OUT_DIR / filename
    cmd = [
        "mflux-generate",
        "--base-model",
        "schnell",
        "--quantize",
        "4",
        "--steps",
        "4",
        "--guidance",
        "1.5",
        "--width",
        "768",
        "--height",
        "768",
        "--prompt",
        prompt,
        "--negative-prompt",
        LOCAL_NEGATIVE,
        "--output",
        str(path),
    ]
    subprocess.run(cmd, check=True)
    print(f"OK  {filename} [local mflux]", flush=True)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    for filename, prompt in ASSETS.items():
        path = OUT_DIR / filename
        if path.exists():
            print(f"SKIP {filename}", flush=True)
            continue

        try:
            generate_asset(filename, prompt)
        except Exception as exc:
            if "402" in str(exc):
                print(f"API limit for {filename}; retrying with local mflux", flush=True)
                try:
                    generate_asset_local(filename, prompt)
                except Exception as local_exc:
                    print(f"FAIL {filename}: {local_exc}", flush=True)
            else:
                print(f"FAIL {filename}: {exc}", flush=True)
        time.sleep(1)

    generated = sorted(p.name for p in OUT_DIR.iterdir() if p.is_file())
    print(f"\nGenerated {len(generated)} FLUX test assets in {OUT_DIR}", flush=True)


if __name__ == "__main__":
    main()
