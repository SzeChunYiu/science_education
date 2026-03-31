"""
Local Stable Diffusion Asset Generator
Uses SDXL base + Children's Book LoRA for consistent flat illustration style.

Key learnings from research:
- Keep prompts UNDER 77 tokens (CLIP limit)
- Lead with style descriptor
- Never say "wooden peg doll" (triggers 3D wood grain)
- Add "solo, alone, single figure" to prevent character sheets
- Use strong negative prompts
"""

import torch
import os
import sys

# Fix OpenMP duplicate library issue on Mac
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler


# ── Concise Style Prompts (under 77 tokens each!) ──

CHAR_STYLE = (
    "flat 2D board book illustration, centered full body historical character, "
    "large rounded head small body, simple black dot eyes, rosy cheeks, "
    "tiny simplified nose and mouth, rounded hair and beard shapes, "
    "clean flat colors, minimal detail, soft friendly style"
)

BG_STYLE = (
    "flat 2D children book illustration, simple minimalist landscape, "
    "flat solid colors, no shading, no gradient, retro modern style, "
    "no people, no characters, no animals, empty scene"
)

ELEMENT_STYLE = (
    "flat 2D children book illustration, single isolated simple shape, "
    "flat solid color, no shading, no gradient, clipart style, "
    "no face, no eyes, no mouth, no smile, no expression, no text, no letters, "
    "on plain white background"
)

NEGATIVE = (
    "realistic, photograph, 3d render, shading, gradient, shadow, "
    "multiple characters, character sheet, turnaround, multiple views, "
    "text, words, letters, label, logo, watermark, face, eyes, eye, mouth, smile, expression, "
    "blurry, low quality, extra limbs, "
    "detailed, complex, busy, cluttered"
)


def load_pipeline():
    """Load SDXL base + children's book LoRA."""
    print("Loading SDXL base 1.0...")
    pipe = StableDiffusionXLPipeline.from_pretrained(
        "stabilityai/stable-diffusion-xl-base-1.0",
        torch_dtype=torch.float16,
        variant="fp16",
        use_safetensors=True,
    )
    pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
    pipe = pipe.to("mps")

    print("Loading children's book LoRA...")
    try:
        pipe.load_lora_weights("chappie90/lora-style-sdxl-childrens-book")
        print("  ✓ Children's book LoRA loaded")
    except Exception as e:
        print(f"  ⚠ LoRA load failed: {e} — continuing without LoRA")

    return pipe


def generate_character(pipe, name, description, filename, output_dir):
    """Generate a single isolated character."""
    prompt = (
        f"{CHAR_STYLE}, solo, alone, single figure, "
        "historically accurate clothing, recognizable portrait likeness, "
        f"{description}"
    )
    path = os.path.join(output_dir, filename)

    print(f"🎨 Character: {name}...")
    img = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE,
        num_inference_steps=25,
        guidance_scale=7.5,
        width=512, height=768,
    ).images[0]
    img.save(path)
    print(f"  ✓ {path}")
    return path


def generate_background(pipe, name, description, filename, output_dir):
    """Generate an empty background scene."""
    prompt = f"{BG_STYLE}, {description}, maximum 4 elements, minimalist"
    path = os.path.join(output_dir, filename)

    print(f"🎨 Background: {name}...")
    img = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE + ", people, person, figure, animal",
        num_inference_steps=25,
        guidance_scale=7.5,
        width=1280, height=720,
    ).images[0]
    img.save(path)
    print(f"  ✓ {path}")
    return path


def generate_element(pipe, name, description, filename, output_dir, w=512, h=512):
    """Generate a single isolated scene element."""
    prompt = (
        f"{ELEMENT_STYLE}, {description}, single object, icon, "
        "inanimate object only, not anthropomorphic"
    )
    path = os.path.join(output_dir, filename)

    print(f"🎨 Element: {name}...")
    img = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE + ", scene, landscape, multiple objects, anthropomorphic, mascot",
        num_inference_steps=20,
        guidance_scale=7.0,
        width=w, height=h,
    ).images[0]
    img.save(path)
    print(f"  ✓ {path}")
    return path


if __name__ == "__main__":
    pipe = load_pipeline()

    CHAR_DIR = "data/assets/physics/characters"
    ELEM_DIR = "data/assets/physics/elements"
    os.makedirs(CHAR_DIR, exist_ok=True)

    # ── Characters ──
    characters = [
        ("Aristotle",
         "ancient Greek philosopher Aristotle, canonical classical bust likeness, balding crown, short curled gray hair at the sides, curled gray beard, off white chiton and himation, brown sandals, holding a clay tablet, plain light background",
         "char_aristotle.png"),
        ("Galileo",
         "Galileo Galilei, recognizable portrait likeness, high forehead, brown mustache and pointed beard, dark late Renaissance scholar robe, broad white collar, holding a simple brass telescope, plain light background",
         "char_galileo.png"),
        ("Newton",
         "Isaac Newton, recognizable portrait likeness, pale face, long white curled wig, brown late 17th century coat, waistcoat, white cravat, holding a green apple, plain light background",
         "char_newton.png"),
        ("Descartes",
         "Rene Descartes, recognizable portrait likeness, shoulder length dark hair, thin dark mustache, black 17th century doublet and cloak, flat white collar, black hat, plain light background",
         "char_descartes.png"),
        ("Euler",
         "Leonhard Euler, recognizable portrait likeness, mature face, powdered white wig or tied white hair, dark 18th century academic coat, white cravat, holding geometry paper, plain light background",
         "char_euler.png"),
        ("Einstein",
         "Albert Einstein, strong portrait likeness, wild white hair, thick white mustache, early 20th century brown gray professor jacket, white shirt, tie, holding papers, plain light background",
         "char_einstein.png"),
        ("Emmy Noether",
         "Emmy Noether, recognizable historical portrait likeness, round face, dark hair in bun, early 20th century modest dark jacket and long skirt with light blouse, holding math papers, plain light background",
         "char_noether.png"),
    ]

    for name, desc, filename in characters:
        generate_character(pipe, name, desc, filename, CHAR_DIR)

    # ── Backgrounds ──
    BG_DIR = "data/assets/physics/backgrounds"
    os.makedirs(BG_DIR, exist_ok=True)

    backgrounds = [
        ("Grass field", "green rolling hills, blue sky, one simple tree, white clouds", "bg_grass.png"),
        ("Ice surface", "frozen blue ice lake, white snowy hills, pale winter sky", "bg_ice.png"),
        ("Outer space", "dark navy blue space, yellow star dots, crescent moon", "bg_space.png"),
        ("Ancient Greece", "white marble columns, warm peach floor, olive tree, golden sky", "bg_greece.png"),
    ]

    for name, desc, filename in backgrounds:
        generate_background(pipe, name, desc, filename, BG_DIR)

    print("\n✅ All assets generated!")
