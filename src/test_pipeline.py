"""
test_pipeline.py — Integration smoke-test for the script → scene pipeline.

Run from the project root:
    python -m src.test_pipeline

What it tests
-------------
1. Parses the Newton's Laws ep04 script.
2. Maps it to scene descriptors.
3. Prints a human-readable summary:
   - Number of segments found
   - Number of scene descriptors generated
   - Visual cue type distribution
4. Saves output to /tmp/test_scenes_ep04.json
5. Validates the scenes and prints any warnings/errors.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

# Ensure the project src/ is importable regardless of how the script is run
_SRC = Path(__file__).parent
_PROJECT = _SRC.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_PROJECT))

from src.pipeline import (
    parse_script,
    SceneMapper,
    validate_scene_sequence,
)
from src.pipeline.scene_mapper import _extract_episode_prefix

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

EP04_SCRIPT = (
    _PROJECT
    / "output"
    / "physics"
    / "01_classical_mechanics"
    / "01_newtons_laws"
    / "ep04_the_quantity_of_motion"
    / "scripts"
    / "ep04_youtube_long.md"
)

OUTPUT_JSON = Path("/tmp/test_scenes_ep04.json")


def _hr(char: str = "─", width: int = 60) -> None:
    print(char * width)


def run_test() -> bool:
    """
    Run the full pipeline test.

    Returns
    -------
    bool
        True when the validation report passes (no errors).
    """
    print()
    _hr("═")
    print("  PIPELINE SMOKE TEST — ep04_youtube_long")
    _hr("═")

    # ------------------------------------------------------------------
    # Step 1: Parse the script
    # ------------------------------------------------------------------
    _hr()
    print("STEP 1 — Parsing script")
    _hr()

    if not EP04_SCRIPT.exists():
        print(f"  ERROR: Script not found at:\n    {EP04_SCRIPT}")
        return False

    parsed = parse_script(str(EP04_SCRIPT))

    print(f"  episode_id      : {parsed.episode_id}")
    print(f"  title           : {parsed.title}")
    print(f"  series_subtitle : {parsed.series_subtitle}")
    print(f"  total_duration  : {parsed.total_duration:.1f}s  "
          f"({parsed.total_duration / 60:.1f} min)")
    print(f"  segments found  : {len(parsed.segments)}")
    print()

    for i, seg in enumerate(parsed.segments):
        ts = (
            f"{seg.start_time:.0f}s – {seg.end_time:.0f}s"
            if seg.start_time is not None else "no timestamp"
        )
        print(
            f"    [{i:02d}] {seg.title[:50]:<50}  "
            f"{ts}  |  "
            f"{len(seg.visual_cues)} visual(s)  "
            f"{len(seg.equations)} eq(s)  "
            f"{len(seg.narrator_lines)} lines"
        )

    # ------------------------------------------------------------------
    # Step 2: Map to scene descriptors
    # ------------------------------------------------------------------
    _hr()
    print("STEP 2 — Mapping segments to scenes")
    _hr()

    mapper = SceneMapper(episode_id=_extract_episode_prefix(parsed.episode_id))
    all_scenes: list[dict] = []

    for seg_idx, segment in enumerate(parsed.segments):
        scenes = mapper.map_segment_to_scenes(segment, seg_idx)
        all_scenes.extend(scenes)

    print(f"  Total scenes generated : {len(all_scenes)}")
    print()

    # Template distribution
    template_counts: Counter = Counter(s.get("template") for s in all_scenes)
    print("  Template distribution:")
    for template, count in sorted(template_counts.items(), key=lambda x: -x[1]):
        bar = "█" * count
        print(f"    {template:<30}  {count:>3}  {bar}")

    # Visual cue type distribution (same as template but only for cue-sourced scenes)
    cue_scenes = [s for s in all_scenes if s.get("_source_visual_cue")]
    print()
    print(f"  Scenes with a visual cue       : {len(cue_scenes)}")
    print(f"  Scenes without a visual cue    : {len(all_scenes) - len(cue_scenes)}")

    # Show a sample scene
    if all_scenes:
        print()
        print("  Sample scene (first scene):")
        sample = all_scenes[0]
        for k, v in sample.items():
            if k == "elements":
                print(f"    elements ({len(v)} item(s)):")
                for elem in v:
                    role = elem.get("role", "?")
                    text = (elem.get("text") or "")[:50]
                    asset = elem.get("asset_path") or ""
                    print(f"      role={role:<20}  text={text!r:<52}  asset={asset[:40]!r}")
            else:
                print(f"    {k:<26}: {str(v)[:70]}")

    # ------------------------------------------------------------------
    # Step 3: Save to /tmp
    # ------------------------------------------------------------------
    _hr()
    print("STEP 3 — Writing output JSON")
    _hr()

    with OUTPUT_JSON.open("w", encoding="utf-8") as fh:
        json.dump(all_scenes, fh, indent=2, ensure_ascii=False)
    print(f"  Saved {len(all_scenes)} scenes → {OUTPUT_JSON}")
    print(f"  File size: {OUTPUT_JSON.stat().st_size / 1024:.1f} KB")

    # ------------------------------------------------------------------
    # Step 4: Validate
    # ------------------------------------------------------------------
    _hr()
    print("STEP 4 — Validation")
    _hr()

    report = validate_scene_sequence(all_scenes)
    print(f"  {report.summary()}")

    if report.errors:
        print()
        print("  ERRORS:")
        for issue in report.errors:
            print(f"    {issue}")

    if report.warnings:
        print()
        print("  WARNINGS:")
        for issue in report.warnings:
            print(f"    {issue}")

    if not report.errors and not report.warnings:
        print("  All checks passed cleanly.")

    _hr("═")
    overall = "PASS" if report.passed else "FAIL"
    print(f"  OVERALL RESULT: {overall}")
    _hr("═")
    print()

    return report.passed


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    ok = run_test()
    sys.exit(0 if ok else 1)
