"""
Scan all physics episode scripts and extract candidate visual assets.

Outputs three files under output/asset_reports/:
  - visual_asset_candidates.json
  - visual_asset_candidates.csv
  - visual_asset_scan_summary.md

Method:
  1. Parse all *_youtube_long.md scripts with the existing script parser.
  2. Pull explicit [Visual: ...] cues where they exist.
  3. Infer additional candidate objects/concepts from headings and narration
     using a curated physics vocabulary.
  4. Compare candidates against the current asset library to surface gaps.
"""

from __future__ import annotations

import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_ROOT = ROOT / "output" / "physics"
ASSET_ROOT = ROOT / "data" / "assets" / "physics"
REPORT_DIR = ROOT / "output" / "asset_reports"

sys.path.insert(0, str(ROOT))

from src.pipeline.script_parser import ParsedScript, parse_script


@dataclass(frozen=True)
class PatternSpec:
    canonical: str
    kind: str
    pattern: str


OBJECT_SPECS: tuple[PatternSpec, ...] = (
    PatternSpec("air", "object", r"\bair\b"),
    PatternSpec("antenna", "object", r"\bantenna(?:s)?\b"),
    PatternSpec("apple", "object", r"\bapple(?:s)?\b"),
    PatternSpec("arrow", "object", r"\barrow(?:s)?\b"),
    PatternSpec("atom", "object", r"\batom(?:s)?\b"),
    PatternSpec("ball", "object", r"\bball(?:s)?\b"),
    PatternSpec("battery", "object", r"\bbatter(?:y|ies)\b"),
    PatternSpec("beam of light", "object", r"\blight beam(?:s)?\b|\bbeam of light\b"),
    PatternSpec("blackbody cavity", "object", r"\bblackbody cavity\b|\bcavity radiator\b"),
    PatternSpec("block", "object", r"\bblock(?:s)?\b"),
    PatternSpec("brass ball", "object", r"\bbrass ball(?:s)?\b"),
    PatternSpec("capacitor", "object", r"\bcapacitor(?:s)?\b"),
    PatternSpec("car", "object", r"\bcar(?:s)?\b"),
    PatternSpec("cart", "object", r"\bcart(?:s)?\b"),
    PatternSpec("cavity", "object", r"\bcavit(?:y|ies)\b"),
    PatternSpec("clock", "object", r"\bclock(?:s)?\b"),
    PatternSpec("coil", "object", r"\bcoil(?:s)?\b"),
    PatternSpec("compass", "object", r"\bcompass(?:es)?\b"),
    PatternSpec("conductor", "object", r"\bconductor(?:s)?\b"),
    PatternSpec("crystal", "object", r"\bcrystal(?:s)?\b"),
    PatternSpec("dielectric slab", "object", r"\bdielectric slab\b"),
    PatternSpec("dipole", "object", r"\bdipole(?:s)?\b"),
    PatternSpec("disk", "object", r"\bdisk(?:s)?\b"),
    PatternSpec("double slit", "object", r"\bdouble slit\b"),
    PatternSpec("earth globe", "object", r"\bearth\b|\bglobe\b"),
    PatternSpec("electron", "object", r"\belectron(?:s)?\b"),
    PatternSpec("engine", "object", r"\bengine(?:s)?\b"),
    PatternSpec("ether", "object", r"\bether\b|\baether\b"),
    PatternSpec("feather", "object", r"\bfeather(?:s)?\b"),
    PatternSpec("flywheel", "object", r"\bflywheel(?:s)?\b"),
    PatternSpec("galvanometer", "object", r"\bgalvanometer(?:s)?\b"),
    PatternSpec("gear", "object", r"\bgear(?:s)?\b"),
    PatternSpec("glass jar", "object", r"\bglass jar\b|\bjar\b"),
    PatternSpec("gyroscope", "object", r"\bgyroscope(?:s)?\b"),
    PatternSpec("heat bath", "object", r"\bheat bath\b"),
    PatternSpec("inclined plane", "object", r"\binclined plane\b"),
    PatternSpec("inductor", "object", r"\binductor(?:s)?\b"),
    PatternSpec("insulator", "object", r"\binsulator(?:s)?\b"),
    PatternSpec("interferometer", "object", r"\binterferometer(?:s)?\b"),
    PatternSpec("ladder", "object", r"\bladder(?:s)?\b"),
    PatternSpec("lamp", "object", r"\blamp(?:s)?\b|\bbulb(?:s)?\b"),
    PatternSpec("lens", "object", r"\blens(?:es)?\b"),
    PatternSpec("leyden jar", "object", r"\bleyden jar\b"),
    PatternSpec("lightning rod", "object", r"\blightning rod(?:s)?\b"),
    PatternSpec("lodestone", "object", r"\blodestone(?:s)?\b"),
    PatternSpec("magnet", "object", r"\bmagnet(?:s)?\b"),
    PatternSpec("metal shell", "object", r"\bmetal shell\b|\bouter shell\b"),
    PatternSpec("meter stick", "object", r"\bmeter stick(?:s)?\b"),
    PatternSpec("mirror", "object", r"\bmirror(?:s)?\b"),
    PatternSpec("moon", "object", r"\bmoon\b"),
    PatternSpec("nucleus", "object", r"\bnucle(?:us|i)\b"),
    PatternSpec("orbiting body", "object", r"\bplanet(?:s)?\b|\bsatellite(?:s)?\b"),
    PatternSpec("parallel plate", "object", r"\bparallel[- ]plate(?: capacitor)?\b|\bplate(?:s)?\b"),
    PatternSpec("pendulum", "object", r"\bpendulum(?:s)?\b"),
    PatternSpec("photon", "object", r"\bphoton(?:s)?\b"),
    PatternSpec("planet", "object", r"\bplanet(?:s)?\b"),
    PatternSpec("polarizer", "object", r"\bpolarizer(?:s)?\b|\bpolariser(?:s)?\b"),
    PatternSpec("proton", "object", r"\bproton(?:s)?\b"),
    PatternSpec("pulley", "object", r"\bpulley(?:s)?\b"),
    PatternSpec("prism", "object", r"\bprism(?:s)?\b"),
    PatternSpec("ramp", "object", r"\bramp(?:s)?\b"),
    PatternSpec("resistor", "object", r"\bresistor(?:s)?\b"),
    PatternSpec("rocket", "object", r"\brocket(?:s)?\b"),
    PatternSpec("rod", "object", r"\brod(?:s)?\b"),
    PatternSpec("screen", "object", r"\bscreen(?:s)?\b"),
    PatternSpec("slit", "object", r"\bslit(?:s)?\b"),
    PatternSpec("solenoid", "object", r"\bsolenoid(?:s)?\b"),
    PatternSpec("spark", "object", r"\bspark(?:s)?\b"),
    PatternSpec("sphere", "object", r"\bsphere(?:s)?\b"),
    PatternSpec("spring", "object", r"\bspring(?:s)?\b"),
    PatternSpec("star", "object", r"\bstar(?:s)?\b"),
    PatternSpec("stone", "object", r"\bstone(?:s)?\b|\brock(?:s)?\b"),
    PatternSpec("string", "object", r"\bstring(?:s)?\b"),
    PatternSpec("sun", "object", r"\bsun\b"),
    PatternSpec("telescope", "object", r"\btelescope(?:s)?\b"),
    PatternSpec("thermometer", "object", r"\bthermometer(?:s)?\b"),
    PatternSpec("train", "object", r"\btrain(?:s)?\b"),
    PatternSpec("waveguide", "object", r"\bwaveguide(?:s)?\b"),
    PatternSpec("water clock", "object", r"\bwater clock\b"),
    PatternSpec("wheel", "object", r"\bwheel(?:s)?\b"),
    PatternSpec("wire", "object", r"\bwire(?:s)?\b"),
)

CONCEPT_SPECS: tuple[PatternSpec, ...] = (
    PatternSpec("acceleration", "concept", r"\bacceleration\b"),
    PatternSpec("action", "concept", r"\baction\b"),
    PatternSpec("angular momentum", "concept", r"\bangular momentum\b"),
    PatternSpec("capacitance", "concept", r"\bcapacitance\b"),
    PatternSpec("charge density", "concept", r"\bcharge density\b|\bsurface charge\b"),
    PatternSpec("conservation of energy", "concept", r"\bconservation of energy\b"),
    PatternSpec("conservation of momentum", "concept", r"\bconservation of momentum\b"),
    PatternSpec("current", "concept", r"\bcurrent\b"),
    PatternSpec("diffraction", "concept", r"\bdiffraction\b"),
    PatternSpec("displacement current", "concept", r"\bdisplacement current\b"),
    PatternSpec("electric field", "concept", r"\belectric field\b"),
    PatternSpec("electromagnetic induction", "concept", r"\binduction\b|\belectromagnetic induction\b"),
    PatternSpec("electromagnetic wave", "concept", r"\belectromagnetic wave(?:s)?\b"),
    PatternSpec("energy", "concept", r"\benergy\b"),
    PatternSpec("entropy", "concept", r"\bentropy\b"),
    PatternSpec("equipotential", "concept", r"\bequipotential\b"),
    PatternSpec("field lines", "concept", r"\bfield lines\b"),
    PatternSpec("force", "concept", r"\bforce\b"),
    PatternSpec("frequency", "concept", r"\bfrequency\b"),
    PatternSpec("friction", "concept", r"\bfriction\b"),
    PatternSpec("gravity", "concept", r"\bgravity\b|\bgravitational\b"),
    PatternSpec("harmonic", "concept", r"\bharmonic(?:s)?\b"),
    PatternSpec("impetus", "concept", r"\bimpetus\b"),
    PatternSpec("induced field", "concept", r"\binduced field\b"),
    PatternSpec("interference", "concept", r"\binterference\b"),
    PatternSpec("kinetic energy", "concept", r"\bkinetic energy\b"),
    PatternSpec("lagrangian", "concept", r"\blagrangian\b"),
    PatternSpec("magnetic field", "concept", r"\bmagnetic field\b"),
    PatternSpec("matrix mechanics", "concept", r"\bmatrix mechanics\b"),
    PatternSpec("momentum", "concept", r"\bmomentum\b"),
    PatternSpec("normal mode", "concept", r"\bnormal mode(?:s)?\b"),
    PatternSpec("orbit", "concept", r"\borbit(?:s|al)?\b"),
    PatternSpec("phase space", "concept", r"\bphase space\b"),
    PatternSpec("polarization", "concept", r"\bpolarization\b|\bpolarisation\b"),
    PatternSpec("potential difference", "concept", r"\bpotential difference\b|\bvoltage\b"),
    PatternSpec("potential energy", "concept", r"\bpotential energy\b"),
    PatternSpec("probability wave", "concept", r"\bwave function\b|\bprobability wave\b"),
    PatternSpec("quantum jump", "concept", r"\bquantum jump\b"),
    PatternSpec("reflection", "concept", r"\breflection\b"),
    PatternSpec("refraction", "concept", r"\brefraction\b"),
    PatternSpec("resonance", "concept", r"\bresonance\b"),
    PatternSpec("standing wave", "concept", r"\bstanding wave(?:s)?\b"),
    PatternSpec("superposition", "concept", r"\bsuperposition\b"),
    PatternSpec("temperature", "concept", r"\btemperature\b"),
    PatternSpec("time dilation", "concept", r"\btime dilation\b"),
    PatternSpec("uncertainty principle", "concept", r"\buncertainty principle\b|\buncertainty\b"),
    PatternSpec("velocity", "concept", r"\bvelocity\b"),
    PatternSpec("wave packet", "concept", r"\bwave packet(?:s)?\b"),
    PatternSpec("wavelength", "concept", r"\bwavelength\b"),
    PatternSpec("work", "concept", r"\bwork\b"),
)

ALL_SPECS = OBJECT_SPECS + CONCEPT_SPECS

RAW_PHRASE_SPLIT_RE = re.compile(r"\s*[;,/]\s*|\s+\band\b\s+|\s+\bwith\b\s+|\s+showing\s+|\s+plus\s+")
BRACKET_RE = re.compile(r"[\[\]()*“”\"']")
MULTISPACE_RE = re.compile(r"\s+")
NON_ALNUM_RE = re.compile(r"[^a-z0-9]+")

EXPLICIT_CUE_BONUS = 3
TITLE_BONUS = 2
HEADING_BONUS = 2
NARRATION_WEIGHT = 1


def normalize_label(text: str) -> str:
    lowered = text.lower().strip()
    lowered = BRACKET_RE.sub(" ", lowered)
    lowered = MULTISPACE_RE.sub(" ", lowered)
    return lowered.strip(" -—–:,.")


def slugify(text: str) -> str:
    return NON_ALNUM_RE.sub("_", normalize_label(text)).strip("_")


def build_existing_asset_index() -> set[str]:
    names: set[str] = set()
    for path in ASSET_ROOT.rglob("*"):
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".svg"}:
            continue
        stem = path.stem.lower()
        stem = re.sub(r"^(obj|char|bg)_", "", stem)
        stem = re.sub(r"_v\d+$", "", stem)
        names.add(stem)
    return names


def script_relpath(path: Path) -> str:
    return str(path.relative_to(ROOT))


def segment_texts(parsed: ParsedScript) -> Iterable[tuple[str, str, str, str]]:
    for segment in parsed.segments:
        heading = segment.title
        title = parsed.title
        narration = " ".join(segment.narrator_lines)
        for cue in segment.visual_cues:
            yield ("visual_cue", cue, heading, title)
        if heading:
            yield ("heading", heading, heading, title)
        if narration:
            yield ("narration", narration, heading, title)
        for term in segment.key_terms:
            yield ("key_term", term, heading, title)


def raw_cue_fragments(cue: str) -> list[str]:
    cue = normalize_label(cue)
    if not cue:
        return []
    parts = RAW_PHRASE_SPLIT_RE.split(cue)
    cleaned: list[str] = []
    for part in parts:
        part = normalize_label(part)
        if len(part) < 4:
            continue
        if part.startswith("animation of "):
            part = part[len("animation of ") :]
        if part.startswith("diagram of "):
            part = part[len("diagram of ") :]
        if part.startswith("close-up of "):
            part = part[len("close-up of ") :]
        if part.startswith("thought experiment "):
            part = part[len("thought experiment ") :]
        if len(part) >= 4:
            cleaned.append(part)
    return cleaned


def match_specs(text: str) -> list[PatternSpec]:
    hits: list[PatternSpec] = []
    lower = normalize_label(text)
    for spec in ALL_SPECS:
        if re.search(spec.pattern, lower, re.IGNORECASE):
            hits.append(spec)
    return hits


def infer_weight(source_kind: str) -> int:
    if source_kind == "visual_cue":
        return EXPLICIT_CUE_BONUS
    if source_kind in {"heading", "key_term"}:
        return HEADING_BONUS
    return NARRATION_WEIGHT


def asset_status(canonical: str, existing_assets: set[str]) -> str:
    slug = slugify(canonical)
    for stem in existing_assets:
        if slug == stem:
            return "existing"
        if slug and (slug in stem or stem in slug):
            return "existing"
        slug_tokens = set(slug.split("_"))
        stem_tokens = set(stem.split("_"))
        if slug_tokens and slug_tokens.issubset(stem_tokens):
            return "existing"
    return "missing"


def main() -> None:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    existing_assets = build_existing_asset_index()
    script_paths = sorted(SCRIPTS_ROOT.rglob("*_youtube_long.md"))

    candidate_counts: Counter[tuple[str, str]] = Counter()
    candidate_episode_hits: defaultdict[tuple[str, str], set[str]] = defaultdict(set)
    candidate_examples: defaultdict[tuple[str, str], list[dict]] = defaultdict(list)
    candidate_sources: defaultdict[tuple[str, str], Counter[str]] = defaultdict(Counter)
    raw_cue_counts: Counter[str] = Counter()
    raw_cue_examples: defaultdict[str, list[dict]] = defaultdict(list)

    for script_path in script_paths:
        parsed = parse_script(str(script_path))
        script_id = script_relpath(script_path)

        for source_kind, text, heading, title in segment_texts(parsed):
            if source_kind == "visual_cue":
                for fragment in raw_cue_fragments(text):
                    raw_cue_counts[fragment] += 1
                    if len(raw_cue_examples[fragment]) < 3:
                        raw_cue_examples[fragment].append(
                            {"script": script_id, "title": title, "heading": heading}
                        )

            matches = match_specs(text)
            if not matches:
                continue

            weight = infer_weight(source_kind)
            for spec in matches:
                key = (spec.kind, spec.canonical)
                candidate_counts[key] += weight
                candidate_episode_hits[key].add(script_id)
                candidate_sources[key][source_kind] += 1
                if len(candidate_examples[key]) < 3:
                    candidate_examples[key].append(
                        {
                            "script": script_id,
                            "title": title,
                            "heading": heading,
                            "source_kind": source_kind,
                            "text": text[:220],
                        }
                    )

    ranked_candidates: list[dict] = []
    for (kind, canonical), weighted_mentions in sorted(
        candidate_counts.items(),
        key=lambda item: (-item[1], item[0][0], item[0][1]),
    ):
        ranked_candidates.append(
            {
                "kind": kind,
                "canonical": canonical,
                "slug": slugify(canonical),
                "weighted_mentions": weighted_mentions,
                "episode_count": len(candidate_episode_hits[(kind, canonical)]),
                "asset_status": asset_status(canonical, existing_assets),
                "source_breakdown": dict(candidate_sources[(kind, canonical)]),
                "examples": candidate_examples[(kind, canonical)],
            }
        )

    top_raw_cues = [
        {
            "phrase": phrase,
            "mentions": count,
            "examples": raw_cue_examples[phrase],
        }
        for phrase, count in raw_cue_counts.most_common(250)
    ]

    payload = {
        "script_count": len(script_paths),
        "existing_asset_count": len(existing_assets),
        "candidate_count": len(ranked_candidates),
        "raw_visual_cue_phrase_count": len(raw_cue_counts),
        "candidates": ranked_candidates,
        "top_raw_visual_phrases": top_raw_cues,
    }

    json_path = REPORT_DIR / "visual_asset_candidates.json"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    csv_path = REPORT_DIR / "visual_asset_candidates.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "kind",
                "canonical",
                "slug",
                "weighted_mentions",
                "episode_count",
                "asset_status",
                "source_breakdown",
                "example_script",
                "example_heading",
                "example_text",
            ],
        )
        writer.writeheader()
        for item in ranked_candidates:
            example = item["examples"][0] if item["examples"] else {}
            writer.writerow(
                {
                    "kind": item["kind"],
                    "canonical": item["canonical"],
                    "slug": item["slug"],
                    "weighted_mentions": item["weighted_mentions"],
                    "episode_count": item["episode_count"],
                    "asset_status": item["asset_status"],
                    "source_breakdown": json.dumps(item["source_breakdown"], sort_keys=True),
                    "example_script": example.get("script", ""),
                    "example_heading": example.get("heading", ""),
                    "example_text": example.get("text", ""),
                }
            )

    object_total = sum(1 for item in ranked_candidates if item["kind"] == "object")
    concept_total = sum(1 for item in ranked_candidates if item["kind"] == "concept")
    missing_objects = [item for item in ranked_candidates if item["kind"] == "object" and item["asset_status"] == "missing"]
    missing_concepts = [item for item in ranked_candidates if item["kind"] == "concept" and item["asset_status"] == "missing"]

    md_lines = [
        "# Visual Asset Scan Summary",
        "",
        f"- Scripts scanned: **{len(script_paths)}**",
        f"- Existing asset stems detected: **{len(existing_assets)}**",
        f"- Candidate objects: **{object_total}**",
        f"- Candidate concepts: **{concept_total}**",
        f"- Distinct raw visual-cue phrases: **{len(raw_cue_counts)}**",
        "",
        "## Top Missing Objects",
        "",
    ]
    for item in missing_objects[:40]:
        md_lines.append(
            f"- **{item['canonical']}** — score {item['weighted_mentions']}, episodes {item['episode_count']}"
        )

    md_lines.extend(["", "## Top Missing Concepts", ""])
    for item in missing_concepts[:40]:
        md_lines.append(
            f"- **{item['canonical']}** — score {item['weighted_mentions']}, episodes {item['episode_count']}"
        )

    md_lines.extend(["", "## Top Raw Visual Phrases", ""])
    for item in top_raw_cues[:40]:
        md_lines.append(f"- **{item['phrase']}** — mentions {item['mentions']}")

    summary_path = REPORT_DIR / "visual_asset_scan_summary.md"
    summary_path.write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    print(f"Scanned {len(script_paths)} scripts")
    print(f"Wrote {json_path}")
    print(f"Wrote {csv_path}")
    print(f"Wrote {summary_path}")


if __name__ == "__main__":
    main()
