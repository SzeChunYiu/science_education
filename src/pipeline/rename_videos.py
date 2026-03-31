"""
rename_videos.py — Rename rendered episode MP4s to the canonical numbering scheme.

Scheme: {TOPIC}_{subtopic:02d}_{ep:02d}_{slug}.mp4

Examples:
  CM_01_01_why_things_stop.mp4
  QM_04_02_spin_half.mp4
  QF_08_01_the_standard_model.mp4

Topic codes
-----------
  01_classical_mechanics  → CM
  02_electromagnetism     → EM
  03_thermodynamics       → TD
  04_quantum_mechanics    → QM
  05_relativity           → RE
  06_mathematical_methods → MM
  07_quantum_field_theory → QF

Usage
-----
  # Dry run (shows what would be renamed, no changes)
  python3 -m src.pipeline.rename_videos

  # Apply renames
  python3 -m src.pipeline.rename_videos --apply

  # Custom physics root
  python3 -m src.pipeline.rename_videos --apply --root output/physics
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Topic code map: directory prefix → short code
# ---------------------------------------------------------------------------

TOPIC_CODES: dict[str, str] = {
    "01_classical_mechanics": "CM",
    "02_electromagnetism":    "EM",
    "03_thermodynamics":      "TD",
    "04_quantum_mechanics":   "QM",
    "05_relativity":          "RE",
    "06_mathematical_methods":"MM",
    "07_quantum_field_theory":"QF",
}

# Already-renamed pattern — skip these
_RE_ALREADY_RENAMED = re.compile(r"^(CM|EM|TD|QM|RE|MM|QF)_\d{2}_\d{2}_")

# Episode number from folder name: ep01_..., ep1_..., ep_01_...
_RE_EP_NUM = re.compile(r"[_-]?ep[_-]?0*(\d+)[_-]", re.IGNORECASE)

# Subtopic number from folder name: 01_newtons_laws, 02_conservation_laws
_RE_SUBTOPIC_NUM = re.compile(r"^(\d+)_")


def _slug(name: str) -> str:
    """Convert a folder name to a clean slug, stripping leading ep##_ prefix."""
    # Remove leading ep##_ pattern
    cleaned = re.sub(r"^ep\d+_", "", name, flags=re.IGNORECASE)
    # Lowercase, keep alphanumeric and underscores only
    cleaned = re.sub(r"[^a-z0-9_]", "_", cleaned.lower())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    return cleaned


def _new_name(topic_dir: Path, subtopic_dir: Path, ep_dir: Path) -> str | None:
    """
    Derive the canonical filename stem for an episode.

    Returns None if any component cannot be parsed.
    """
    topic_code = TOPIC_CODES.get(topic_dir.name)
    if not topic_code:
        return None

    sub_m = _RE_SUBTOPIC_NUM.match(subtopic_dir.name)
    if not sub_m:
        return None
    subtopic_num = int(sub_m.group(1))

    ep_m = _RE_EP_NUM.search("_" + ep_dir.name + "_")
    if not ep_m:
        return None
    ep_num = int(ep_m.group(1))

    slug = _slug(ep_dir.name)
    return f"{topic_code}_{subtopic_num:02d}_{ep_num:02d}_{slug}"


def collect_renames(physics_root: Path) -> list[tuple[Path, Path]]:
    """
    Walk the physics output tree and collect (old_path, new_path) pairs
    for every *_youtube_long.mp4 that needs renaming.
    """
    renames: list[tuple[Path, Path]] = []

    for mp4 in sorted(physics_root.rglob("*.mp4")):
        # Only target youtube_long renders
        if "youtube_long" not in mp4.stem:
            continue
        # Skip already-renamed files
        if _RE_ALREADY_RENAMED.match(mp4.name):
            continue

        # Expected structure: physics/<topic>/<subtopic>/<ep>/media/<file>.mp4
        parts = mp4.parts
        try:
            media_idx = parts.index("media")
        except ValueError:
            continue

        if media_idx < 3:
            continue

        ep_dir      = Path(parts[media_idx - 1])
        subtopic_dir = Path(parts[media_idx - 2])
        topic_dir   = Path(parts[media_idx - 3])

        stem = _new_name(topic_dir, subtopic_dir, ep_dir)
        if not stem:
            print(f"  WARN: could not derive name for {mp4}", file=sys.stderr)
            continue

        new_path = mp4.parent / f"{stem}.mp4"
        if new_path != mp4:
            renames.append((mp4, new_path))

    return renames


def main() -> None:
    parser = argparse.ArgumentParser(description="Rename episode MP4s to canonical scheme.")
    parser.add_argument("--apply", action="store_true", help="Actually rename files (default: dry run)")
    parser.add_argument("--root", default="output/physics", help="Path to physics output root")
    args = parser.parse_args()

    physics_root = Path(args.root)
    if not physics_root.exists():
        sys.exit(f"ERROR: root not found: {physics_root}")

    renames = collect_renames(physics_root)

    if not renames:
        print("Nothing to rename.")
        return

    print(f"{'DRY RUN — ' if not args.apply else ''}Renaming {len(renames)} files:\n")
    for old, new in renames:
        print(f"  {old.name}")
        print(f"    → {new.name}")

    if not args.apply:
        print(f"\nRun with --apply to rename {len(renames)} files.")
        return

    done = 0
    for old, new in renames:
        old.rename(new)
        done += 1

    print(f"\nRenamed {done} files.")


if __name__ == "__main__":
    main()
