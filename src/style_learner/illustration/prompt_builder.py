"""Build SD prompts from production plan scene data."""
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

STYLE_TRIGGER = "teded_style"

NEGATIVE_PROMPT = (
    "photorealistic, 3d render, photograph, dark, scary, complex background, "
    "blurry, low quality, text, watermark, signature, frame, border, "
    "multiple views, collage"
)

# Scene type → additional prompt hints
SCENE_TYPE_HINTS = {
    "close-up illustrated object": "single centered object, clean background, detailed illustration",
    "wide scene with characters": "full scene composition, multiple characters, illustrated background",
    "historical map": "illustrated map, geographic features, vintage cartography style",
    "scientific diagram": "clean diagram, labeled parts, educational illustration",
    "microscopic visualization": "cellular level view, biological illustration, magnified view",
    "horizontal timeline": "timeline layout, chronological events, milestone markers",
    "text title card": "bold title text, decorative background, educational",
    "abstract pattern": "decorative illustration, pattern, educational motif",
}


def build_scene_prompt(
    scene: dict,
    episode_palette: list[str] = None,
    character_descriptions: dict[str, str] = None,
    consistency_anchors: list[str] = None,
) -> tuple[str, str]:
    """Build positive and negative prompts for a scene.

    Args:
        scene: Scene dict from production plan with keys:
            narration, scene_type, visual_metaphor, character, text_elements
        episode_palette: List of hex colour strings for the episode
        character_descriptions: Dict of character_name → description from consistency memory
        consistency_anchors: List of visual anchor strings from previously accepted scenes

    Returns:
        (positive_prompt, negative_prompt)
    """
    parts = [STYLE_TRIGGER]

    # Scene type hint
    scene_type = scene.get("scene_type", "")
    if scene_type in SCENE_TYPE_HINTS:
        parts.append(SCENE_TYPE_HINTS[scene_type])

    # Visual metaphor (the creative intelligence)
    visual_metaphor = scene.get("visual_metaphor", "")
    if visual_metaphor:
        parts.append(visual_metaphor)

    # Character
    character = scene.get("character", {})
    if character:
        char_name = character.get("name", "")
        char_pose = character.get("pose", "standing")
        if char_name and character_descriptions and char_name in character_descriptions:
            parts.append(f"{character_descriptions[char_name]}, {char_pose} pose")
        elif char_name:
            parts.append(f"character {char_name}, {char_pose} pose, chibi style")

    # Extract key concepts from narration
    narration = scene.get("narration", "")
    if narration:
        # Take key nouns from narration (simplified extraction)
        key_words = _extract_key_concepts(narration)
        if key_words:
            parts.append(f"depicting {', '.join(key_words)}")

    # Style anchors
    parts.append("flat color style, bold outlines, clean composition")
    parts.append("educational animated illustration, warm inviting style")

    # Colour palette
    if episode_palette:
        hex_str = ", ".join(episode_palette[:4])
        parts.append(f"color palette: {hex_str}")

    # Consistency anchors from previously accepted scenes
    if consistency_anchors:
        for anchor in consistency_anchors[:3]:  # Limit to avoid prompt bloat
            parts.append(anchor)

    positive = ", ".join(parts)
    return positive, NEGATIVE_PROMPT


def build_title_card_prompt(
    title: str,
    subtitle: str = "",
    palette: list[str] = None,
) -> tuple[str, str]:
    """Build prompt specifically for episode title cards."""
    parts = [
        STYLE_TRIGGER,
        "educational title card",
        f'bold text reading "{title}"',
    ]
    if subtitle:
        parts.append(f'subtitle: "{subtitle}"')
    parts.append("decorative illustrated background, warm colors")
    parts.append("flat design, clean typography, inviting educational style")

    if palette:
        parts.append(f"color palette: {', '.join(palette[:4])}")

    return ", ".join(parts), NEGATIVE_PROMPT


def _extract_key_concepts(narration: str, max_concepts: int = 5) -> list[str]:
    """Extract key visual concepts from narration text.

    Uses simple heuristics (capitalised words, nouns after prepositions).
    Falls back to first N significant words if spacy not available.
    """
    try:
        import spacy
        nlp = spacy.load("en_core_web_sm")
        doc = nlp(narration)
        concepts = []
        for ent in doc.ents:
            if ent.label_ in ("PERSON", "ORG", "GPE", "LOC", "EVENT", "PRODUCT"):
                concepts.append(ent.text)
        for chunk in doc.noun_chunks:
            if chunk.root.pos_ in ("NOUN", "PROPN") and chunk.text not in concepts:
                concepts.append(chunk.text)
        return concepts[:max_concepts]
    except (ImportError, OSError):
        # Fallback: extract capitalised words and long words
        words = narration.split()
        concepts = []
        for w in words:
            clean = w.strip(".,!?;:'\"")
            if len(clean) > 5 and clean[0].isupper():
                concepts.append(clean)
        return concepts[:max_concepts]
