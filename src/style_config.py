"""
Locked style configuration for all asset generation.
Based on expert review feedback matching "My First Heroes: Inventors" by Nila Aye.

DO NOT MODIFY without reviewing with art direction team.
"""

# ── Master Style Prompt ──
# Prepended to EVERY image generation prompt
STYLE_PREFIX = (
    "Flat vector board-book illustration in the style of My First Heroes. "
    "Cute historical characters with very large rounded heads and tiny simple bodies. "
    "Simple black dot eyes with no highlights. Small rosy cheek circles. "
    "A tiny simplified nose and tiny simple mouth are allowed. Soft simple eyebrows are allowed. "
    "Hair, wigs, and beards are smooth rounded solid shapes with no individual strands. "
    "Clothing is flat simple color blocks with very minimal folds and very minimal detail. "
    "Arms and legs are short simple rounded forms. "
    "Background elements are ultra simplified geometric shapes like circles rectangles and rounded hills. "
    "Keep everything clean, soft, and uncluttered with mostly flat solid color fills. "
    "Avoid realistic texture, realistic rendering, or heavy 3D shading. "
    "No text no words no letters no writing anywhere in the image."
)

# ── Suffix reinforcement ──
# Appended to EVERY prompt to fight AI tendency to add detail
STYLE_SUFFIX = (
    "Remember: keep the board-book look, use simple rounded shapes, minimal detail, "
    "mostly flat color fills, no realistic rendering, no texture, no clutter"
)

# ── Background-specific rules ──
BG_RULES = (
    "CRITICAL: absolutely NO people, NO characters, NO figures, NO animals, NO silhouettes anywhere in the image. "
    "This must be a completely empty environment scene with zero living beings. "
    "Just landscape and simple geometric environmental elements only."
)

# ── Object-specific rules ──
OBJECT_RULES = (
    "CRITICAL: objects and props must be completely inanimate and non-anthropomorphic. "
    "Absolutely NO faces, NO eyes, NO mouth, NO smile, NO expressions, NO cute mascot features. "
    "Absolutely NO text, NO words, NO letters, NO numbers, NO labels, NO logos anywhere on the object."
)

# ── Character-specific rules ──
CHARACTER_RULES = (
    "CRITICAL: each historical figure must remain recognizable as that specific person, not a generic cartoon scholar. "
    "Use the canonical portrait or bust tradition for facial likeness and signature hair, beard, wig, hat, or age cues. "
    "Clothing must match the correct historical period, region, and social role. "
    "No modern clothes, no fantasy robes, no mixed-era costume elements."
)

# ── Brand Color Palette ──
COLORS = {
    "cream": "#FFF5E6",      # warm cream for backgrounds
    "coral_red": "#E85D5D",  # ball mascot and accents
    "navy": "#1A2744",       # space/contrast
    "sage_green": "#7FB685", # nature scenes
    "gold": "#F5C518",       # highlights and stars
    "lavender": "#C5A3D9",   # philosophy/thought scenes
    "sky_blue": "#87CEEB",   # sky
    "soft_pink": "#F4B8C1",  # rosy cheeks
    "brown_coat": "#8B6D4B", # Newton's coat
    "toga_white": "#F0EDE5", # Aristotle's toga
}

# ── Character Definitions ──
# Each character is generated ONCE and reused everywhere
CHARACTERS = {
    "aristotle": {
        "prompt": (
            "single cute stylized board-book character of ancient Greek philosopher Aristotle, "
            "recognizable from the canonical classical bust tradition, "
            "very large perfectly round head, tiny stubby body, "
            "balding crown with short curled gray hair at the sides as solid shapes, "
            "short curled gray beard as one solid shape, "
            "historically appropriate ancient Greek off white chiton and himation drape as flat cream white solid shapes, "
            "brown leather sandals as tiny stumps, "
            "holding a small clay tablet, thoughtful pose, "
            "full body front view, "
            "isolated on solid flat pastel blue background"
        ),
        "width": 512,
        "height": 768,
    },
    "galileo": {
        "prompt": (
            "single cute stylized board-book character of Italian scientist Galileo Galilei, "
            "recognizable from famous portraits, "
            "very large perfectly round head, tiny stubby body, "
            "high forehead, receding dark hair, brown mustache and short pointed beard as solid shapes, "
            "historically accurate late Renaissance academic robe in dark black with broad flat white collar, "
            "holding a small simple telescope shape in flat brown, "
            "full body front view, "
            "isolated on solid flat pastel yellow background"
        ),
        "width": 512,
        "height": 768,
    },
    "newton": {
        "prompt": (
            "single cute stylized board-book character of English scientist Isaac Newton, "
            "recognizable from famous portraits, "
            "very large perfectly round head, tiny stubby body, "
            "pale oval face, large white curled wig as one solid rounded cloud shape with clean edges, "
            "historically accurate late 17th century long brown coat, waistcoat, and flat white cravat, "
            "holding a small simple green apple circle, "
            "full body front view, "
            "isolated on solid flat pastel green background"
        ),
        "width": 512,
        "height": 768,
    },
    "descartes": {
        "prompt": (
            "single cute stylized board-book character of French philosopher Rene Descartes, "
            "recognizable from painted portraits, "
            "very large perfectly round head, tiny stubby body, "
            "thin dark mustache as simple curved solid shape, shoulder length dark hair as solid shape, "
            "historically accurate 17th century black doublet and cloak as flat solid black, wide white collar as flat white shape, "
            "black wide brimmed hat as simple flat circle on head, "
            "holding a quill pen, "
            "full body front view, "
            "isolated on solid flat lavender background"
        ),
        "width": 512,
        "height": 768,
    },
    "euler": {
        "prompt": (
            "single cute stylized board-book character of Swiss mathematician Leonhard Euler, "
            "recognizable from painted portraits, "
            "very large perfectly round head, tiny stubby body, "
            "powdered white wig or tied white hair as a simple solid shape, calm mature face, "
            "historically accurate 18th century dark academic coat with flat white cravat, "
            "holding a simple geometry paper, "
            "full body front view, "
            "isolated on solid flat mint background"
        ),
        "width": 512,
        "height": 768,
    },
    "einstein": {
        "prompt": (
            "single cute stylized board-book character of physicist Albert Einstein, "
            "strong recognizable portrait likeness, "
            "very large perfectly round head, tiny stubby body, "
            "wild white hair as one solid cloud shape, thick white mustache as one solid shape, "
            "historically appropriate early 20th century brown gray professor jacket, white shirt, and tie as flat solid shapes, "
            "holding a few simple papers, "
            "full body front view, "
            "isolated on solid flat pastel orange background"
        ),
        "width": 512,
        "height": 768,
    },
    "noether": {
        "prompt": (
            "single cute stylized board-book character of mathematician Emmy Noether, "
            "recognizable from historical portraits, "
            "very large perfectly round head, tiny stubby body, "
            "round face, dark hair in a bun as a simple solid shape, "
            "historically accurate early 20th century modest dark academic jacket and long skirt with light blouse, "
            "holding math papers, "
            "full body front view, "
            "isolated on solid flat pastel pink background"
        ),
        "width": 512,
        "height": 768,
    },
}

# ── Background Definitions ──
BACKGROUNDS = {
    "grass_field": {
        "prompt": (
            "completely empty landscape scene with absolutely no people no characters no animals. "
            "Simple overlapping rounded hill shapes each hill is ONE flat solid pastel green using 2 or 3 distinct greens. "
            "Sky is one flat solid light blue with zero gradient. "
            "One ultra simple tree made of a solid brown rectangle trunk topped with a solid green circle. "
            "Two simple white rounded cloud shapes. "
            "Flat paper cutout style."
        ),
        "width": 1280,
        "height": 720,
    },
    "ice_surface": {
        "prompt": (
            "completely empty winter landscape scene with absolutely no people no characters no animals. "
            "Flat icy surface as a single solid pale blue rectangle. "
            "Simple geometric white and pale blue overlapping rounded hill forms suggesting snow in distance. "
            "Sky is one flat solid very pale blue. "
            "A few simple white circle dots suggesting snowflakes. "
            "Flat paper cutout style."
        ),
        "width": 1280,
        "height": 720,
    },
    "outer_space": {
        "prompt": (
            "completely empty outer space scene with absolutely no people no characters no animals no astronauts. "
            "Flat dark navy blue background. "
            "Simple small yellow circle dots scattered for stars fewer than 15 total. "
            "One simple crescent moon shape in pale yellow. "
            "Everything is flat solid fills no glow effects no sparkle. "
            "Flat paper cutout style."
        ),
        "width": 1280,
        "height": 720,
    },
    "ancient_greece": {
        "prompt": (
            "completely empty ancient Greek courtyard scene with absolutely no people no characters no animals. "
            "Three or four simple flat white rectangular columns with simple rectangular tops. "
            "Warm peach sand colored flat solid ground as one flat color. "
            "Pale cream warm yellow flat solid sky. "
            "One ultra simple olive tree made of brown rectangle trunk and solid green circle top. "
            "Flat paper cutout style."
        ),
        "width": 1280,
        "height": 720,
    },
}

MODEL = "black-forest-labs/FLUX.1-schnell"
