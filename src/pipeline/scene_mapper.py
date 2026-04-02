"""
scene_mapper.py — Maps parsed script segments to scene descriptor dicts.

A scene descriptor is a dictionary ready to be consumed by the layout engine.
It follows the schema:

    {
        "scene_id":   "ep04_s02_f00",       # episode_segment_frame
        "template":   "equation_reveal",    # see TEMPLATES below
        "duration":   4.5,                  # seconds (float)
        "background": "assets/backgrounds/bg_study.png",
        "elements":   [                     # list of LayoutElement-compatible dicts
            {
                "role":       "equation_center",
                "text":       "p = mv",
                "font_size":  72,
                "color":      [26, 26, 26],
                "scale":      1.0,
                "padding":    8,
                "asset_path": null
            }
        ],
        "_source_visual_cue":  "[Visual: equation p = mv...]",  # debugging
        "_source_segment":     "Part 2: Every Symbol, Explained",
    }

Template taxonomy
-----------------
equation_reveal         — one equation displayed large and clean
derivation_step         — step-by-step equation build with interim results
character_scene         — one or two characters with optional caption
two_element_comparison  — side-by-side visual (split layout)
diagram_explanation     — diagram or multi-element illustration
animation_scene         — described animation (diagram + caption)
narration_with_caption  — spoken passage with on-screen caption text
"""

from __future__ import annotations

import re
from typing import Optional

from .script_parser import ScriptSegment, ParsedScript


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TEMPLATES = {
    "equation_reveal",
    "derivation_step",
    "character_scene",
    "two_element_comparison",
    "diagram_explanation",
    "animation_scene",
    "narration_with_caption",
}

# Default background per template — relative to project root
_TEMPLATE_BACKGROUNDS: dict[str, str] = {
    "equation_reveal":        "data/assets/physics/backgrounds/bg_chalkboard.png",
    "derivation_step":        "data/assets/physics/backgrounds/bg_chalkboard.png",
    "character_scene":        "data/assets/physics/backgrounds/bg_study.png",
    "two_element_comparison": "data/assets/physics/backgrounds/bg_grass_field.png",
    "diagram_explanation":    "data/assets/physics/backgrounds/bg_laboratory.png",
    "animation_scene":        "data/assets/physics/backgrounds/bg_grass_field.png",
    "narration_with_caption": "data/assets/physics/backgrounds/bg_study.png",
}

_CHARACTER_BACKGROUNDS: dict[str, str] = {
    "aristotle": "data/assets/physics/backgrounds/bg_ancient_greek_courtyard.png",
    "newton": "data/assets/physics/backgrounds/bg_grass_field.png",
    "galileo": "data/assets/physics/backgrounds/bg_laboratory.png",
    "descartes": "data/assets/physics/backgrounds/bg_study.png",
    "leibniz": "data/assets/physics/backgrounds/bg_study.png",
    "kepler": "data/assets/physics/backgrounds/bg_deep_space.png",
    "euler": "data/assets/physics/backgrounds/bg_study.png",
    "lagrange": "data/assets/physics/backgrounds/bg_study.png",
    "hamilton": "data/assets/physics/backgrounds/bg_study.png",
    "noether": "data/assets/physics/backgrounds/bg_study.png",
    "emilie": "data/assets/physics/backgrounds/bg_study.png",
    "du châtelet": "data/assets/physics/backgrounds/bg_study.png",
    "du chatelet": "data/assets/physics/backgrounds/bg_study.png",
    "einstein": "data/assets/physics/backgrounds/bg_study.png",
    "maxwell": "data/assets/physics/backgrounds/bg_laboratory.png",
    "faraday": "data/assets/physics/backgrounds/bg_laboratory.png",
    "boltzmann": "data/assets/physics/backgrounds/bg_study.png",
    "planck": "data/assets/physics/backgrounds/bg_chalkboard.png",
    "bohr": "data/assets/physics/backgrounds/bg_laboratory.png",
    "schrodinger": "data/assets/physics/backgrounds/bg_study.png",
    "dirac": "data/assets/physics/backgrounds/bg_chalkboard.png",
    "feynman": "data/assets/physics/backgrounds/bg_chalkboard.png",
}

_SUBJECT_BACKGROUND_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    # Historical periods / locations (most specific first)
    (("aristotle", "greece", "greek", "athens", "ancient", "ptolemy", "philoponus", "alexandria"), "data/assets/physics/backgrounds/bg_ancient_greek_courtyard.png"),
    (("rome", "roman", "pantheon"), "data/assets/physics/backgrounds/bg_pantheon.png"),
    (("pisa", "galileo", "ramp", "inclined plane", "brass ball"), "data/assets/physics/backgrounds/bg_laboratory.png"),
    (("royal society", "london", "1668", "hooke", "wren"), "data/assets/physics/backgrounds/bg_royal_society.png"),
    (("göttingen", "gottingen", "university", "lecture", "classroom"), "data/assets/physics/backgrounds/bg_university_lecture.png"),
    (("patent office", "bern", "1905"), "data/assets/physics/backgrounds/bg_patent_office.png"),
    (("observatory", "telescope", "uraniborg", "tycho"), "data/assets/physics/backgrounds/bg_observatory.png"),
    # Physics domains
    (("space", "orbit", "planet", "star", "moon", "galaxy", "relativity", "spacetime", "light speed", "cosmos"), "data/assets/physics/backgrounds/bg_spacetime.png"),
    (("electromagnetic", "electric", "magnetic", "charge", "current", "maxwell", "faraday", "coulomb", "field lines"), "data/assets/physics/backgrounds/bg_electromagnetic.png"),
    (("heat", "temperature", "entropy", "thermal", "thermodynamic", "boltzmann", "carnot", "steam"), "data/assets/physics/backgrounds/bg_thermal.png"),
    (("quantum", "wave function", "superposition", "probability", "schrodinger", "planck", "bohr", "photon", "uncertainty"), "data/assets/physics/backgrounds/bg_quantum.png"),
    (("accelerator", "particle", "collider", "cern"), "data/assets/physics/backgrounds/bg_particle_accelerator.png"),
    # Settings / activities
    (("experiment", "lab", "measure", "apparatus", "instrument", "device", "tested", "measured"), "data/assets/physics/backgrounds/bg_laboratory.png"),
    (("equation", "derive", "proof", "formula", "theorem", "calculus", "math"), "data/assets/physics/backgrounds/bg_chalkboard.png"),
    (("book", "wrote", "published", "library", "manuscript", "principia", "read"), "data/assets/physics/backgrounds/bg_library.png"),
    (("workshop", "machine", "gear", "mechanical", "engine", "pulley", "clockwork"), "data/assets/physics/backgrounds/bg_workshop.png"),
    (("train", "railway", "station", "track"), "data/assets/physics/backgrounds/bg_train_station.png"),
    (("road", "car", "highway", "braking", "driving"), "data/assets/physics/backgrounds/bg_road_highway.png"),
    # Natural settings
    (("ice", "skate", "slip", "frictionless", "friction"), "data/assets/physics/backgrounds/bg_ice_surface.png"),
    (("ball", "apple", "throw", "projectile", "field", "outdoor", "ground", "floor", "roll"), "data/assets/physics/backgrounds/bg_grass_field.png"),
    (("ocean", "water", "wave", "fluid", "tide", "sea"), "data/assets/physics/backgrounds/bg_ocean.png"),
    (("mountain", "height", "gravity", "potential", "climb", "hill"), "data/assets/physics/backgrounds/bg_mountain.png"),
    (("desert", "sand", "dune"), "data/assets/physics/backgrounds/bg_desert.png"),
    (("sunset", "dawn", "dusk"), "data/assets/physics/backgrounds/bg_sunset.png"),
    (("garden", "tree", "nature"), "data/assets/physics/backgrounds/bg_garden.png"),
    (("cave", "underground"), "data/assets/physics/backgrounds/bg_cave.png"),
    (("city", "skyline", "building"), "data/assets/physics/backgrounds/bg_city_skyline.png"),
    (("underwater", "submarine", "deep"), "data/assets/physics/backgrounds/bg_underwater.png"),
)

_AIRFLOW_ACCENT_ASSET = "data/assets/physics/objects/obj_airflow_streamlines.png"

# Minimum seconds to assign when no timestamp information is available
_DEFAULT_SCENE_DURATION = 5.0
# Seconds to budget per visual cue when splitting a segment's time
_MIN_SCENE_DURATION = 2.0


class SceneMapper:
    """
    Converts :class:`~script_parser.ScriptSegment` objects into lists of
    scene descriptor dicts, one dict per [Visual: ...] cue in the segment.

    If a segment has no visual cues a single fallback scene is generated
    from the narrator text using the ``narration_with_caption`` template.

    Parameters
    ----------
    episode_id : str
        Used as a prefix for generated scene_ids, e.g. ``"ep04"``.
    aspect_ratio : str
        ``"16:9"`` (default) or ``"9:16"`` — influences default backgrounds.

    Character asset map
    -------------------
    The ``CHARACTER_MAP`` class attribute maps lowercase character names to
    their expected PNG asset paths.  When a name appears in a visual cue the
    mapper resolves it to the path (or a ``PLACEHOLDER:`` string if the file
    does not yet exist).
    """

    CHARACTER_MAP: dict[str, str] = {
        "newton":       "data/assets/physics/characters/char_newton.png",
        "aristotle":    "data/assets/physics/characters/char_aristotle.png",
        "galileo":      "data/assets/physics/characters/char_galileo.png",
        "descartes":    "data/assets/physics/characters/char_descartes.png",
        "leibniz":      "data/assets/physics/characters/char_leibniz.png",
        "noether":      "data/assets/physics/characters/char_noether.png",
        "euler":        "data/assets/physics/characters/char_euler.png",
        "kepler":       "data/assets/physics/characters/char_kepler.png",
        "lagrange":     "data/assets/physics/characters/char_lagrange.png",
        "hamilton":     "data/assets/physics/characters/char_hamilton.png",
        "emilie":       "data/assets/physics/characters/char_noether.png",
        "du châtelet":  "data/assets/physics/characters/char_noether.png",
        "du chatelet":  "data/assets/physics/characters/char_noether.png",
        "einstein":     "data/assets/physics/characters/char_einstein.png",
        "maxwell":      "data/assets/physics/characters/char_maxwell.png",
        "faraday":      "data/assets/physics/characters/char_faraday.png",
        "boltzmann":    "data/assets/physics/characters/char_boltzmann.png",
        "planck":       "data/assets/physics/characters/char_planck.png",
        "bohr":         "data/assets/physics/characters/char_bohr.png",
        "schrodinger":  "data/assets/physics/characters/char_schrodinger.png",
        "dirac":        "data/assets/physics/characters/char_dirac.png",
        "feynman":      "data/assets/physics/characters/char_feynman.png",
    }

    def __init__(self, episode_id: str, aspect_ratio: str = "16:9") -> None:
        self.episode_id = episode_id
        self.aspect_ratio = aspect_ratio
        self._scene_counter: int = 0  # global counter across segments

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def map_segment_to_scenes(self, segment: ScriptSegment, segment_index: int) -> list[dict]:
        """
        Convert one script segment into a list of scene descriptor dicts.

        Each [Visual: ...] cue in the segment becomes at least one scene.
        Duration is distributed evenly across scenes within the segment.
        If no visual cues exist a single narration_with_caption scene is
        generated from the first narrator line.

        Parameters
        ----------
        segment : ScriptSegment
        segment_index : int
            0-based index of this segment, used for scene_id generation.

        Returns
        -------
        list[dict]
            Scene descriptors ready to be serialised to JSON.
        """
        scenes: list[dict] = []
        cues = segment.visual_cues if segment.visual_cues else [None]

        # Time budget per cue
        if segment.duration > 0:
            per_cue = max(_MIN_SCENE_DURATION, segment.duration / max(len(cues), 1))
        else:
            per_cue = _DEFAULT_SCENE_DURATION

        for frame_index, cue in enumerate(cues):
            scene_id = f"{self.episode_id}_s{segment_index:02d}_f{frame_index:02d}"
            self._scene_counter += 1

            if cue is not None:
                template = self.classify_visual_cue(cue)
            else:
                template = "narration_with_caption"

            # Pass narrator text for better background context matching
            if segment.narrator_lines:
                narrator_text = " ".join(
                    line.text if hasattr(line, "text") else str(line)
                    for line in segment.narrator_lines
                )
            else:
                narrator_text = ""
            background = self._background_for_scene(template, cue, narrator_text=narrator_text)
            elements = self._build_elements(template, cue, segment, frame_index)

            scene: dict = {
                "scene_id":            scene_id,
                "template":            template,
                "duration":            round(per_cue, 2),
                "background":          background,
                "elements":            elements,
                "_source_visual_cue":  f"[Visual: {cue}]" if cue else None,
                "_source_segment":     segment.title,
            }
            scenes.append(scene)

        return scenes

    def _background_for_scene(self, template: str, cue: Optional[str],
                              narrator_text: str = "") -> str:
        """Pick the best background by matching visual cue AND narrator context.

        Priority:
        1. Character-specific background (for character_scene with known character)
        2. Subject-keyword match against both visual cue and narrator text
        3. Template default
        """
        default_bg = _TEMPLATE_BACKGROUNDS.get(template, "data/assets/physics/backgrounds/bg_study.png")

        # Combine all available text for context matching
        context = " ".join(filter(None, [cue, narrator_text])).lower()

        # For character scenes, try character-specific background first
        if template == "character_scene" and cue:
            char_name = self.extract_character(cue)
            if char_name:
                char_bg = _CHARACTER_BACKGROUNDS.get(char_name)
                if char_bg:
                    return char_bg

        # Try subject-keyword matching against ALL context (for ALL templates)
        if context:
            inferred = self._background_from_subject(context)
            if inferred:
                return inferred

        return default_bg

    def _background_from_subject(self, cue: str) -> str:
        lower = (cue or "").lower()
        for keywords, background in _SUBJECT_BACKGROUND_HINTS:
            if any(keyword in lower for keyword in keywords):
                return background
        return ""

    # ------------------------------------------------------------------
    # Classification
    # ------------------------------------------------------------------

    def classify_visual_cue(self, cue: str) -> str:
        """
        Classify a [Visual: ...] string into one of the template types.

        Classification priority (first match wins):
        1. "side by side" / "comparison" / "vs" → two_element_comparison
        2. "equation" or contains recognisable math expression → equation_reveal
        3. "derivation" / "step by step" / "calculations appearing" → derivation_step
        4. "animation" / "manim" → animation_scene
        5. Known character name → character_scene
        6. "diagram" / "shows" / "table" / "chalkboard" → diagram_explanation
        7. "portrait" / "book" / "page" → character_scene (historical figure)
        8. Default → narration_with_caption

        Parameters
        ----------
        cue : str
            The raw text inside the [Visual: ...] tag.

        Returns
        -------
        str
            One of the template name strings defined in :data:`TEMPLATES`.
        """
        lower = cue.lower()

        try:
            # --- 1. Comparison / side-by-side ---
            if re.search(r"\bside.by.side\b|comparison|vs\.?\b|versus\b", lower):
                return "two_element_comparison"

            # --- 2. Equation reveal ---
            if re.search(r"\bequation\b", lower):
                return "equation_reveal"
            # Inline math: contains known equation patterns
            if re.search(
                r"[=\+\-×÷/^√∫∑∂]|"
                r"\b(p\s*=|F\s*=|v\s*=|E\s*=|mv|kg|m/s|v²|v\^2|dp/dt)\b",
                cue,
                re.IGNORECASE,
            ):
                return "equation_reveal"

            # --- 3. Derivation step ---
            if re.search(r"\bderivation\b|step.by.step\b|calculations appearing\b", lower):
                return "derivation_step"

            # --- 4. Animation ---
            if re.search(r"\banimation\b|\bmanim\b|moving toward|collision\b", lower):
                return "animation_scene"

            # --- 5. Named character ---
            if self.extract_character(cue) is not None:
                return "character_scene"

            # --- 6. Diagram / table / data ---
            if re.search(r"\bdiagram\b|\btable\b|\bchalkboard\b|\bshows?\b|\bdata\b|\bfits?\b", lower):
                return "diagram_explanation"

            # --- 7. Portrait / historical document ---
            if re.search(r"\bportrait\b|\bbook\b|\bpage\b|\bcover\b|\bprincipia\b", lower):
                return "character_scene"

            # --- Default ---
            return "narration_with_caption"

        except Exception:
            # Safety net — never crash the pipeline
            return "narration_with_caption"

    # ------------------------------------------------------------------
    # Extraction helpers
    # ------------------------------------------------------------------

    def extract_equation(self, cue: str) -> str:
        """
        Try to extract an equation string from a visual cue.

        Strategy:
        1. Look for an inline equation pattern like ``p = mv`` in the cue text.
        2. Look for LaTeX-style bold ``**p = mv**`` patterns.
        3. Fall back to returning the cue verbatim (truncated to 80 chars).

        Parameters
        ----------
        cue : str
            Raw visual cue text.

        Returns
        -------
        str
            Best-guess equation string, or the cue itself.
        """
        # Pattern: word = expression (e.g. "p = mv", "F = dp/dt", "v² = 2gh")
        m = re.search(
            r"([A-Za-z_ΔδΩω][A-Za-z_0-9ΔδΩω²³]*(?:\s*\(.*?\))?"
            r"\s*=\s*[A-Za-z0-9_.+\-×÷/^√∫∑∂()⋅\s²³,]+)",
            cue,
        )
        if m:
            return m.group(1).strip()

        # Bold **equation**
        bold_m = re.search(r"\*\*(.+?)\*\*", cue)
        if bold_m and re.search(r"[=+\-×÷/]", bold_m.group(1)):
            return bold_m.group(1).strip()

        # Last resort: return truncated cue
        return cue[:80]

    def extract_character(self, cue: str) -> Optional[str]:
        """
        Try to identify a known character name in a visual cue.

        Returns the lowercase character key (e.g. ``"newton"``) if found,
        or ``None`` if no known character is detected.

        Parameters
        ----------
        cue : str
            Raw visual cue text.
        """
        lower = cue.lower()
        for name in self.CHARACTER_MAP:
            if name in lower:
                return name
        return None

    def resolve_character_asset(self, name: str) -> str:
        """
        Return the absolute asset path for *name*, or a ``PLACEHOLDER:`` string
        if the asset file does not yet exist.

        Parameters
        ----------
        name : str
            Lowercase character key from :attr:`CHARACTER_MAP`.
        """
        import os
        from pathlib import Path
        path = self.CHARACTER_MAP.get(name.lower())
        if path is None:
            return f"PLACEHOLDER:char_{name.lower().replace(' ', '_')}"
        # Resolve relative to project root (works locally and on LUNARC)
        project_root = Path(__file__).resolve().parents[2]
        full = str(project_root / path)
        if os.path.exists(full):
            return full
        return f"PLACEHOLDER:{path}"

    # ------------------------------------------------------------------
    # Element builders
    # ------------------------------------------------------------------

    def _build_elements(
        self,
        template: str,
        cue: Optional[str],
        segment: ScriptSegment,
        frame_index: int,
    ) -> list[dict]:
        """
        Build the ``elements`` list for a scene descriptor.

        Each element dict is compatible with :class:`~layout.element.LayoutElement`.
        Required keys: ``role``, plus at least one of ``text`` or ``asset_path``.

        Parameters
        ----------
        template : str
            The classified template name.
        cue : str or None
            The source visual cue text.
        segment : ScriptSegment
            The parent segment (for fallback text).
        frame_index : int
            0-based index of this scene within its segment.
        """
        try:
            builder = _ELEMENT_BUILDERS.get(template, _build_narration_elements)
            return builder(self, cue, segment, frame_index)
        except Exception:
            # Never crash — return a safe fallback
            return _fallback_element(segment)


# ---------------------------------------------------------------------------
# Per-template element builder functions
# ---------------------------------------------------------------------------

def _build_equation_reveal_elements(
    mapper: SceneMapper,
    cue: Optional[str],
    segment: ScriptSegment,
    frame_index: int,
) -> list[dict]:
    """Build elements for equation_reveal: large centred equation + optional caption."""
    equation = mapper.extract_equation(cue) if cue else (
        segment.equations[0] if segment.equations else "?"
    )
    elements: list[dict] = [
        {
            "role":       "equation_center",
            "text":       equation,
            "font_size":  72,
            "color":      [26, 26, 26],
            "scale":      1.0,
            "padding":    16,
            "asset_path": None,
        }
    ]
    # Add a caption from the cue text (minus the extracted equation part)
    if cue:
        caption = re.sub(re.escape(equation), "", cue, flags=re.IGNORECASE).strip(" ,.-")
        if caption and len(caption) > 3:
            elements.append({
                "role":       "caption",
                "text":       caption[:140],
                "font_size":  32,
                "color":      [60, 60, 60],
                "scale":      1.0,
                "padding":    8,
                "asset_path": None,
            })
    return elements


def _build_derivation_step_elements(
    mapper: SceneMapper,
    cue: Optional[str],
    segment: ScriptSegment,
    frame_index: int,
) -> list[dict]:
    """Build elements for derivation_step: timeline zone with equation lines."""
    equations = segment.equations
    if equations:
        new_idx = min(frame_index + 1, len(equations) - 1)
        prev_idx = max(0, new_idx - 1)
        previous_line = equations[prev_idx] if new_idx != prev_idx else ""
        new_line = equations[new_idx]
    else:
        previous_line = ""
        new_line = mapper.extract_equation(cue) if cue else "..."

    elements = [
        {
            "role":       "timeline",
            "text":       new_line,
            "font_size":  56,
            "color":      [26, 26, 26],
            "scale":      1.0,
            "padding":    12,
            "asset_path": None,
        },
        {
            "role":       "caption",
            "text":       (cue or "")[:120],
            "font_size":  30,
            "color":      [80, 80, 80],
            "scale":      1.0,
            "padding":    8,
            "asset_path": None,
        },
    ]
    if previous_line:
        elements.insert(0, {
            "role":       "headline",
            "text":       previous_line,
            "font_size":  42,
            "color":      [90, 90, 90],
            "scale":      1.0,
            "padding":    8,
            "asset_path": None,
        })
    return elements


def _build_character_scene_elements(
    mapper: SceneMapper,
    cue: Optional[str],
    segment: ScriptSegment,
    frame_index: int,
) -> list[dict]:
    """Build elements for character_scene: character image + optional caption."""
    char_name = mapper.extract_character(cue or "")
    asset = mapper.resolve_character_asset(char_name) if char_name else "PLACEHOLDER:char_unknown"
    elements: list[dict] = [
        {
            "role":       "character_center",
            "asset_path": asset,
            "text":       None,
            "font_size":  36,
            "color":      [26, 26, 26],
            "scale":      0.85,
            "padding":    8,
        }
    ]
    if cue:
        # Use a short concept label for the lower-third (name, year, title)
        label = _concept_label(cue, max_words=7)
        elements.append({
            "role":       "lower_third",
            "text":       label,
            "font_size":  28,
            "color":      [26, 26, 26],
            "scale":      1.0,
            "padding":    8,
            "asset_path": None,
        })
    return elements


def _build_two_element_comparison_elements(
    mapper: SceneMapper,
    cue: Optional[str],
    segment: ScriptSegment,
    frame_index: int,
) -> list[dict]:
    """Build elements for two_element_comparison: left + right character/diagram zones."""
    # Try to split the cue on "vs" / "—" / "and" to get left/right labels
    labels = _split_comparison_cue(cue or "")
    left_label, right_label = labels

    return [
        {
            "role":       "character_left",
            "text":       left_label[:60],
            "font_size":  34,
            "color":      [26, 26, 26],
            "scale":      1.0,
            "padding":    10,
            "asset_path": None,
        },
        {
            "role":       "character_right",
            "text":       right_label[:60],
            "font_size":  34,
            "color":      [26, 26, 26],
            "scale":      1.0,
            "padding":    10,
            "asset_path": None,
        },
    ]


def _build_diagram_explanation_elements(
    mapper: SceneMapper,
    cue: Optional[str],
    segment: ScriptSegment,
    frame_index: int,
) -> list[dict]:
    """Build elements for diagram_explanation: diagram zone + short caption label."""
    return [
        {
            "role":       "diagram",
            "text":       _concept_label(cue or "diagram", max_words=6),
            "font_size":  30,
            "color":      [40, 40, 40],
            "scale":      1.0,
            "padding":    12,
            "asset_path": f"PLACEHOLDER:diagram_{_slugify(cue or 'generic')}",
        },
        {
            "role":       "caption",
            "text":       _key_phrase(cue or "", max_words=12),
            "font_size":  30,
            "color":      [60, 60, 60],
            "scale":      1.0,
            "padding":    8,
            "asset_path": None,
        },
    ]


def _build_animation_elements(
    mapper: SceneMapper,
    cue: Optional[str],
    segment: ScriptSegment,
    frame_index: int,
) -> list[dict]:
    """Build elements for animation_scene: diagram zone (animation frame) + short caption."""
    elements = [
        {
            "role":       "diagram",
            "text":       _concept_label(cue or "animation", max_words=5),
            "font_size":  28,
            "color":      [40, 40, 40],
            "scale":      1.0,
            "padding":    12,
            "asset_path": f"PLACEHOLDER:anim_{_slugify(cue or 'generic')}",
        },
        {
            "role":       "caption",
            "text":       _key_phrase(cue or "", max_words=12),
            "font_size":  30,
            "color":      [60, 60, 60],
            "scale":      1.0,
            "padding":    8,
            "asset_path": None,
        },
    ]
    lower = (cue or "").lower()
    if any(token in lower for token in ("air", "wind", "flow", "rush", "streamline")):
        elements.append({
            "role":       "accent",
            "text":       None,
            "font_size":  0,
            "color":      [40, 40, 40],
            "scale":      1.0,
            "padding":    0,
            "asset_path": _AIRFLOW_ACCENT_ASSET,
        })
    return elements


def _build_narration_elements(
    mapper: SceneMapper,
    cue: Optional[str],
    segment: ScriptSegment,
    frame_index: int,
) -> list[dict]:
    """Build elements for narration_with_caption: optional headline + key term.

    Full narration belongs in audio + subtitles.  Only show a headline when
    the segment title is real content (e.g. "Why Things Stop"), not a
    structural/section label like "Opening Hook" or "Conclusion".
    """
    title = segment.title.strip()

    # Filter out structural section labels that look like debug/navigation text.
    # These are generic segment headings (e.g. "Opening Hook", "Introduction",
    # "Conclusion") that should NOT appear as on-screen headlines.
    headline = ""
    if title and not _is_structural_label(title) and len(title.split()) <= 8:
        headline = title
    elif title and not _is_structural_label(title):
        raw = (segment.narrator_lines[0] if segment.narrator_lines else title)
        headline = _key_phrase(raw, max_words=8)

    # Secondary: extract a short key term from narration if it adds new info
    secondary = ""
    if segment.narrator_lines:
        candidate = _key_phrase(segment.narrator_lines[0], max_words=9)
        # Only show if it's meaningfully different from the headline
        if headline and candidate.lower()[:20] != headline.lower()[:20] and len(candidate.split()) >= 4:
            secondary = candidate
        elif not headline and len(candidate.split()) >= 4:
            # No headline — promote the narrator key phrase to headline
            headline = candidate

    elements: list[dict] = []
    if headline:
        elements.append({
            "role":       "headline",
            "text":       headline,
            "font_size":  44,
            "color":      [26, 26, 26],
            "scale":      1.0,
            "padding":    10,
            "asset_path": None,
        })
    if secondary:
        elements.append({
            "role":       "body_text",
            "text":       secondary,
            "font_size":  32,
            "color":      [60, 60, 60],
            "scale":      1.0,
            "padding":    8,
            "asset_path": None,
        })
    return elements


# Structural/section labels that should NOT be displayed as on-screen text.
# These are segment headings used for script organization, not content.
_STRUCTURAL_LABELS = frozenset({
    "opening hook", "hook", "introduction", "intro", "conclusion",
    "outro", "closing", "recap", "summary", "bridge", "transition",
    "opening", "ending", "final thoughts", "wrap up", "wrap-up",
    "teaser", "preview", "cold open",
})


def _is_structural_label(title: str) -> bool:
    """Return True if *title* is a generic section label, not real content."""
    normalised = title.strip().lower()
    # Exact match against known structural labels
    if normalised in _STRUCTURAL_LABELS:
        return True
    # Pattern: looks like a scene_id (e.g. "ep01_s02_f00")
    if re.match(r"^ep\d+_s\d+_f\d+$", normalised):
        return True
    # Pattern: "Part N" or "Segment N" headings
    if re.match(r"^(part|segment|section|chapter)\s+\d+", normalised, re.IGNORECASE):
        return True
    return False


# Dispatch table: template → builder function
_ELEMENT_BUILDERS = {
    "equation_reveal":        _build_equation_reveal_elements,
    "derivation_step":        _build_derivation_step_elements,
    "character_scene":        _build_character_scene_elements,
    "two_element_comparison": _build_two_element_comparison_elements,
    "diagram_explanation":    _build_diagram_explanation_elements,
    "animation_scene":        _build_animation_elements,
    "narration_with_caption": _build_narration_elements,
}


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def _fallback_element(segment: ScriptSegment) -> list[dict]:
    """Return a minimal safe element when a builder fails."""
    title = segment.title[:100]
    # Suppress structural labels from appearing on screen
    if _is_structural_label(title):
        title = ""
    if not title:
        return []
    return [{
        "role":       "headline",
        "text":       title,
        "font_size":  36,
        "color":      [26, 26, 26],
        "scale":      1.0,
        "padding":    8,
        "asset_path": None,
    }]


def _split_comparison_cue(cue: str) -> tuple[str, str]:
    """
    Split a comparison cue into left and right label strings.

    Tries splitting on " vs ", " — ", " and ", "—" in that order.
    If none match, splits at the midpoint of the string.
    """
    for sep in (" vs ", " — ", " and ", "—", " versus "):
        if sep.lower() in cue.lower():
            idx = cue.lower().index(sep.lower())
            left = cue[:idx].strip()
            right = cue[idx + len(sep):].strip()
            return left or "Item A", right or "Item B"
    # Fallback: split at midpoint of words
    words = cue.split()
    mid = len(words) // 2
    return " ".join(words[:mid]) or "Item A", " ".join(words[mid:]) or "Item B"


def _slugify(text: str) -> str:
    """Convert arbitrary text to a safe snake_case identifier (≤ 40 chars)."""
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower())
    slug = slug.strip("_")
    return slug[:40]


def _key_phrase(text: str, max_words: int = 9) -> str:
    """
    Extract a short on-screen label from a longer narration sentence.

    On-screen text should be the core concept (≤ max_words words), NOT the
    full narration — the full narration belongs in subtitles and audio.

    Strategy (first match wins):
    1. Split at the first strong pause (period, semicolon, colon, em-dash)
       and return that clause if it is 3–max_words words long.
    2. Return the first max_words words with an ellipsis.
    """
    text = text.strip()
    if not text:
        return ""
    # Try clean first-clause extraction
    for sep in (". ", "! ", "? ", "; ", ": ", " — ", " – ", " - "):
        if sep in text:
            clause = text.split(sep, 1)[0].strip(" .,;:!?—–-")
            words = clause.split()
            if 3 <= len(words) <= max_words:
                return clause
    # Fall back to first N words
    words = text.split()
    if len(words) <= max_words:
        return text.rstrip(" .,;:!?")
    return " ".join(words[:max_words]) + "…"


def _concept_label(text: str, max_words: int = 6) -> str:
    """
    Extract a very short concept label (≤ max_words words) suitable for
    headlines and lower-thirds where space is tightest.
    """
    return _key_phrase(text, max_words=max_words)


# ---------------------------------------------------------------------------
# Public pipeline function
# ---------------------------------------------------------------------------

def map_script_to_scenes(
    script_path: str,
    output_path: str,
) -> list[dict]:
    """
    Full pipeline: parse script → map to scenes → write JSON.

    Parameters
    ----------
    script_path : str
        Path to the markdown script file.
    output_path : str
        Destination path for the generated ``scenes.json`` file.
        Parent directories are created if they do not exist.

    Returns
    -------
    list[dict]
        All generated scene descriptors in order.

    Side-effects
    ------------
    Writes a JSON file to *output_path*.
    """
    import json
    from pathlib import Path
    from .script_parser import parse_script

    parsed = parse_script(script_path)
    mapper = SceneMapper(episode_id=_extract_episode_prefix(parsed.episode_id))
    all_scenes: list[dict] = []

    for seg_idx, segment in enumerate(parsed.segments):
        scenes = mapper.map_segment_to_scenes(segment, seg_idx)
        all_scenes.extend(scenes)

    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as fh:
        json.dump(all_scenes, fh, indent=2, ensure_ascii=False)

    return all_scenes


def _extract_episode_prefix(episode_id: str) -> str:
    """Extract the short episode prefix from a stem like 'ep04_youtube_long'."""
    m = re.match(r"(ep\d+)", episode_id, re.IGNORECASE)
    return m.group(1) if m else episode_id.split("_")[0]
