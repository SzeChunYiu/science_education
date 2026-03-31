from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
ASSET_ROOT = ROOT / "data" / "assets" / "physics"
DEFAULT_MANIFEST = ASSET_ROOT / "manifests" / "phase1_core_assets.json"

NEGATIVE_BY_CATEGORY = {
    "characters": (
        "realistic, photo, 3d render, gradient shading, complex detail, "
        "text, letters, numbers, multiple characters, extra people, "
        "glossy eyes, reflections, watermark"
    ),
    "objects": (
        "person, people, human, character, figure, face, eyes, mouth, smile, "
        "text, letters, numbers, logo, watermark, realistic, glossy, shiny, "
        "3d, photo, cluttered, background scene"
    ),
    "backgrounds": (
        "person, people, human, character, figure, face, eyes, mouth, "
        "text, letters, numbers, logo, watermark, realistic, photo, 3d render"
    ),
}

OUTPUT_SUBDIR = {
    "characters": "characters",
    "objects": "objects",
    "backgrounds": "backgrounds",
    "elements": "elements",
}


def load_manifest(path: Path) -> dict:
    return json.loads(path.read_text())


def output_path(asset: dict) -> Path:
    category = asset["category"]
    subdir = OUTPUT_SUBDIR[category]
    return ASSET_ROOT / subdir / asset["filename"]


def generate_asset(asset: dict, use_lora: bool = True) -> bool:
    out_path = output_path(asset)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "mflux-generate",
        "--model",
        "schnell",
        "--quantize",
        "4",
        "--low-ram",
        "--steps",
        "4",
        "--guidance",
        "1.0",
        "--width",
        str(asset["width"]),
        "--height",
        str(asset["height"]),
        "--prompt",
        asset["prompt"],
        "--negative-prompt",
        NEGATIVE_BY_CATEGORY[asset["category"]],
        "--output",
        str(out_path),
    ]
    if use_lora:
        command.extend(["--lora-style", "illustration"])

    env = os.environ.copy()
    env["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    try:
        subprocess.run(command, check=True, env=env, timeout=300)
        return True
    except subprocess.TimeoutExpired:
        print(f"FAIL timeout {asset['filename']}")
        return False
    except subprocess.CalledProcessError as exc:
        print(f"FAIL command {asset['filename']}: {exc}")
        return False


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate reusable physics assets from a manifest.")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--names", nargs="*", default=None, help="Optional asset filenames to generate.")
    parser.add_argument("--force", action="store_true", help="Regenerate even if the output already exists.")
    parser.add_argument("--no-lora", action="store_true", help="Disable the illustration LoRA.")
    args = parser.parse_args()

    manifest = load_manifest(args.manifest.expanduser().resolve())
    assets = manifest["assets"]
    if args.names:
        wanted = set(args.names)
        assets = [asset for asset in assets if asset["filename"] in wanted]

    print(f"Manifest: {manifest['name']}")
    print(f"Assets selected: {len(assets)}")
    print(f"Output root: {ASSET_ROOT}")

    stats = {"ok": 0, "skip": 0, "fail": 0}
    for asset in assets:
        out_path = output_path(asset)
        if out_path.exists() and not args.force:
            print(f"SKIP {asset['filename']}")
            stats["skip"] += 1
            continue
        if out_path.exists() and args.force:
            out_path.unlink()

        print(f"GEN  {asset['filename']}")
        ok = generate_asset(asset, use_lora=not args.no_lora)
        stats["ok" if ok else "fail"] += 1
        time.sleep(2)

    print("\nDone")
    print(f"  ok:   {stats['ok']}")
    print(f"  skip: {stats['skip']}")
    print(f"  fail: {stats['fail']}")


if __name__ == "__main__":
    main()
