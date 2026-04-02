"""
batch_processor.py — Episode and bulk-batch processing for the pipeline.

This module provides two public functions:

``process_episode``
    Parse a single script, map it to scenes, validate, and write outputs.

``process_all_episodes``
    Walk a physics directory tree, discover all ``*_youtube_long.md`` files,
    and call ``process_episode`` on each one.

Output structure (per episode)
-------------------------------
    {output_base}/{topic_dir}/{episode_dir}/
        scenes.json       — list of scene descriptors
        manifest.json     — episode metadata + asset inventory

Both files are UTF-8 JSON.

Manifest schema
---------------
    {
        "episode_id":     "ep04",
        "title":          "The Quantity of Motion ...",
        "series_subtitle":"Newton's Laws: ...",
        "script_path":    "/absolute/path/to/script.md",
        "scene_count":    18,
        "segment_count":  8,
        "total_duration": 630.0,
        "visual_cue_count": 14,
        "template_distribution": {
            "equation_reveal": 6,
            "two_element_comparison": 2,
            ...
        },
        "asset_inventory": {
            "placeholders": ["PLACEHOLDER:char_newton", ...],
            "resolved": ["assets/characters/char_newton.png", ...]
        },
        "validation": {
            "passed": true,
            "error_count": 0,
            "warning_count": 3,
            "issues": [...]
        },
        "generated_at": "2026-03-30T00:00:00"
    }
"""

from __future__ import annotations

import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .script_parser import parse_script
from .scene_mapper import SceneMapper, _extract_episode_prefix
from .scene_validator import validate_scene_sequence


# ---------------------------------------------------------------------------
# Single-episode processing
# ---------------------------------------------------------------------------

def process_episode(script_path: str, output_dir: str) -> dict:
    """
    Full episode processing pipeline.

    Steps
    -----
    1. Parse the markdown script → :class:`~script_parser.ParsedScript`
    2. Map segments to scene descriptors
    3. Validate the scene sequence
    4. Write ``scenes.json`` to *output_dir*
    5. Write ``manifest.json`` to *output_dir*

    Parameters
    ----------
    script_path : str
        Absolute path to a ``*_youtube_long.md`` script file.
    output_dir : str
        Directory where output files will be written.  Created if absent.

    Returns
    -------
    dict
        The manifest dictionary (same content as ``manifest.json``).

    Notes
    -----
    This function never raises from parsing or mapping failures — it will
    produce a partial result and record the error in the manifest.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    error_log: list[str] = []

    # Step 1: Parse
    try:
        parsed = parse_script(script_path)
    except Exception as exc:
        error_log.append(f"parse_script failed: {exc}")
        return _error_manifest(script_path, output_dir, error_log)

    episode_prefix = _extract_episode_prefix(parsed.episode_id)
    mapper = SceneMapper(episode_id=episode_prefix)

    # Step 2: Map
    all_scenes: list[dict] = []
    try:
        for seg_idx, segment in enumerate(parsed.segments):
            scenes = mapper.map_segment_to_scenes(segment, seg_idx)
            all_scenes.extend(scenes)
    except Exception as exc:
        error_log.append(f"scene mapping failed at segment {seg_idx}: {exc}")
        # Continue with whatever scenes we have so far

    # Step 3: Validate
    try:
        report = validate_scene_sequence(all_scenes)
    except Exception as exc:
        error_log.append(f"validation raised an exception: {exc}")
        report = None

    # Step 4: Write scenes.json
    scenes_path = out / "scenes.json"
    try:
        with scenes_path.open("w", encoding="utf-8") as fh:
            json.dump(all_scenes, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        error_log.append(f"writing scenes.json failed: {exc}")

    # Step 5: Build and write manifest
    manifest = _build_manifest(
        parsed=parsed,
        scenes=all_scenes,
        script_path=script_path,
        report=report,
        error_log=error_log,
    )
    manifest_path = out / "manifest.json"
    try:
        with manifest_path.open("w", encoding="utf-8") as fh:
            json.dump(manifest, fh, indent=2, ensure_ascii=False)
    except Exception as exc:
        error_log.append(f"writing manifest.json failed: {exc}")

    return manifest


# ---------------------------------------------------------------------------
# Bulk processing
# ---------------------------------------------------------------------------

def process_all_episodes(physics_dir: str, output_base: str) -> list[dict]:
    """
    Walk all episodes under *physics_dir*, find ``*_youtube_long.md`` files,
    process each one, and write results under *output_base*.

    Output layout mirrors the source tree:

        {output_base}/{topic_folder}/{episode_folder}/
            scenes.json
            manifest.json

    For example, a script at::

        .../01_classical_mechanics/01_newtons_laws/ep04_.../scripts/ep04_youtube_long.md

    produces output at::

        {output_base}/01_classical_mechanics/01_newtons_laws/ep04_.../scenes.json

    Parameters
    ----------
    physics_dir : str
        Root directory to search, e.g.
        ``".../output/physics/01_classical_mechanics"``.
    output_base : str
        Root directory for output files, e.g. ``".../output/pipeline"``.

    Returns
    -------
    list[dict]
        List of manifest dicts, one per processed episode.  Failed episodes
        have ``"error": true`` in their manifest.

    Prints
    ------
    Progress lines to stdout: one line per script found, with
    success/failure indication.
    """
    physics_path = Path(physics_dir)
    output_path = Path(output_base)

    scripts = sorted(physics_path.rglob("*_youtube_long.md"))
    if not scripts:
        print(f"No *_youtube_long.md scripts found under {physics_dir}")
        return []

    print(f"Found {len(scripts)} script(s) under {physics_dir}")
    manifests: list[dict] = []

    for script in scripts:
        # Build a mirrored output path relative to physics_dir
        try:
            rel = script.relative_to(physics_path)
        except ValueError:
            rel = Path(script.stem)

        # Strip the 'scripts' sub-directory from the path
        parts = list(rel.parts)
        if "scripts" in parts:
            parts.remove("scripts")
        # Also strip the script filename itself
        episode_parts = parts[:-1]  # everything except the filename

        ep_out = output_path.joinpath(*episode_parts) if episode_parts else output_path

        print(f"  Processing: {script.name} → {ep_out.relative_to(output_path)}")

        manifest = process_episode(str(script), str(ep_out))
        scene_count = manifest.get("scene_count", 0)
        passed = manifest.get("validation", {}).get("passed", False)
        status = "OK" if passed else "WARN"
        print(f"    [{status}] {scene_count} scenes generated")

        manifests.append(manifest)

    passed_count = sum(1 for m in manifests if m.get("validation", {}).get("passed", False))
    print(
        f"\nBatch complete: {len(manifests)} episode(s) processed, "
        f"{passed_count} passed validation."
    )
    return manifests


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _build_manifest(
    parsed: Any,
    scenes: list[dict],
    script_path: str,
    report: Any,
    error_log: list[str],
) -> dict:
    """Assemble the manifest dict for one processed episode."""
    # Template distribution
    template_counts: Counter = Counter(s.get("template", "unknown") for s in scenes)

    # Asset inventory
    placeholders: list[str] = []
    resolved: list[str] = []
    for scene in scenes:
        for elem in scene.get("elements", []):
            ap = elem.get("asset_path")
            if ap:
                if str(ap).startswith("PLACEHOLDER:"):
                    ph = str(ap)[len("PLACEHOLDER:"):]
                    if ph not in placeholders:
                        placeholders.append(ph)
                else:
                    if ap not in resolved:
                        resolved.append(ap)

    # Visual cue count
    visual_cue_count = sum(
        1 for s in scenes if s.get("_source_visual_cue") is not None
    )

    # Validation summary
    if report is not None:
        val_summary = {
            "passed": report.passed,
            "error_count": len(report.errors),
            "warning_count": len(report.warnings),
            "issues": [str(issue) for issue in report.errors + report.warnings],
        }
    else:
        val_summary = {"passed": False, "error_count": 1, "warning_count": 0,
                       "issues": ["Validation could not be run."]}

    return {
        "episode_id":            parsed.episode_id,
        "title":                 parsed.title,
        "series_subtitle":       parsed.series_subtitle,
        "script_path":           str(script_path),
        "scene_count":           len(scenes),
        "segment_count":         len(parsed.segments),
        "total_duration":        round(parsed.total_duration, 2),
        "visual_cue_count":      visual_cue_count,
        "template_distribution": dict(template_counts),
        "asset_inventory": {
            "placeholders": sorted(placeholders),
            "resolved":     sorted(resolved),
        },
        "validation":            val_summary,
        "processing_errors":     error_log,
        "generated_at":          datetime.now(timezone.utc).isoformat(),
    }


def _error_manifest(script_path: str, output_dir: str, errors: list[str]) -> dict:
    """Return a minimal error manifest when parsing fails entirely."""
    return {
        "episode_id":        Path(script_path).stem,
        "title":             "",
        "script_path":       str(script_path),
        "scene_count":       0,
        "segment_count":     0,
        "total_duration":    0.0,
        "visual_cue_count":  0,
        "template_distribution": {},
        "asset_inventory":   {"placeholders": [], "resolved": []},
        "validation":        {"passed": False, "error_count": 1, "warning_count": 0,
                              "issues": errors},
        "processing_errors": errors,
        "error":             True,
        "generated_at":      datetime.now(timezone.utc).isoformat(),
    }
