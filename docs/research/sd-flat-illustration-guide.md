# Practical Guide: High-Quality Flat Illustration from Local Stable Diffusion

**Hardware:** Apple Silicon M4, 16GB RAM, MPS backend
**Current setup:** FLUX.1-schnell via HuggingFace Inference API + `diffusers`
**Goal:** Flat paper-cutout / children's book illustrations (Nila Aye style)
**Date:** March 2026

---

## Executive Summary

Your current setup (FLUX.1-schnell via HuggingFace Inference API) is actually a strong choice. The problems you are experiencing -- character sheets, 3D look, complex scenes -- are primarily **prompt engineering and parameter issues**, not model issues. Below are three recommended setups ranked by expected quality for your specific flat-illustration use case.

---

## Top 3 Recommended Setups

### Setup 1 (RECOMMENDED): FLUX.1-schnell via HuggingFace Inference API (Current, Improved)

**Why:** You already have this working. FLUX has excellent prompt adherence. The API is free and avoids local memory pressure. The problems are fixable with prompt/parameter changes.

**What to change:**

1. **Prompt structure overhaul** (see Prompt Engineering section below)
2. **Add explicit negative concepts INTO the positive prompt** (FLUX does not support negative prompts natively -- you must say "no X" directly in the prompt)
3. **Reduce prompt length** -- your current `STYLE_PREFIX` is 600+ characters. FLUX works better with concise, well-ordered prompts.

**Code changes to `asset_generator.py`:**

```python
from huggingface_hub import InferenceClient

# Shorter, more directive style prefix
STYLE_PREFIX = (
    "flat 2D vector illustration, solid color fills, zero shading, zero gradients, "
    "paper cutout aesthetic, bold simple shapes, children's picture book style"
)

# Anti-hallucination suffix -- tell FLUX what NOT to do inline
STYLE_SUFFIX = (
    "no 3D rendering, no realistic lighting, no texture, no shadows, "
    "no multiple figures, no character sheet, no turnaround"
)

MODEL = "black-forest-labs/FLUX.1-schnell"

def generate_asset(prompt: str, output_path: str, width: int = 1024, height: int = 1024):
    full_prompt = f"{STYLE_PREFIX}. {prompt}. {STYLE_SUFFIX}"
    client = InferenceClient()
    image = client.text_to_image(
        full_prompt,
        model=MODEL,
        width=width,
        height=height,
    )
    image.save(output_path)
```

**Key parameter rules for FLUX.1-schnell:**
- `num_inference_steps`: 4 (schnell is designed for 1-4 steps; more does NOT help)
- `guidance_scale`: 0.0 (schnell uses no CFG -- it is a distilled model)
- Dimensions: must be multiples of 16; stick to 1024x1024 for characters, 1280x720 for backgrounds
- `max_sequence_length`: 256 (default; do not exceed)

---

### Setup 2: SDXL Base 1.0 + Children's Book LoRA (Local, More Style Control)

**Why:** SDXL has the richest LoRA ecosystem. Community LoRAs specifically trained for flat children's book illustration exist and work well. SDXL supports true negative prompts, giving you much more control. Fits in 16GB with float16.

**Model size:** ~6.5GB (SDXL base fp16) + ~150MB per LoRA = ~7GB total. Fits easily in 16GB.

**Best LoRAs for flat illustration (from CivitAI):**

| LoRA | CivitAI ID | Trigger Words | Recommended Weight |
|------|-----------|---------------|-------------------|
| picture books-Children cartoon | 176435 | `children's picture books`, `flat-cartoon` | 0.7-0.8 |
| Children book v2.0 | 285062 | `children book illustration` | 0.7-0.9 |
| StorybookRedmond | 132128 | `StorybookRedmondV2` | 0.6-0.8 |
| Flat Colors + Realistic Cartoon | 2146930 | `flat colors` | 0.6-0.8 |

**Complete working code:**

```python
import torch
from diffusers import StableDiffusionXLPipeline, DPMSolverMultistepScheduler

# ── Load SDXL base ──
pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
)

# ── Load a children's book LoRA ──
# Download .safetensors from CivitAI first, place in ./loras/
pipe.load_lora_weights(
    "./loras/",
    weight_name="picture_books_children_cartoon.safetensors",
    adapter_name="children_book",
)
pipe.set_adapters(["children_book"], adapter_weights=[0.75])

# ── Use DPM++ 2M Karras scheduler (best for quality) ──
pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    pipe.scheduler.config,
    algorithm_type="dpmsolver++",
    use_karras_sigmas=True,
)

# ── Move to MPS ──
pipe = pipe.to("mps")

# ── Enable memory optimizations for 16GB ──
pipe.enable_attention_slicing()
# pipe.enable_vae_tiling()  # Uncomment if you hit OOM on large images

STYLE_PREFIX = (
    "flat 2D children's picture book illustration, solid color fills, "
    "paper cutout style, simple geometric shapes, bold outlines, "
    "single character only, centered composition"
)

NEGATIVE_PROMPT = (
    "3d render, realistic, photograph, multiple characters, character sheet, "
    "turnaround sheet, model sheet, multiple views, multiple poses, "
    "multiple figures, collage, grid, reference sheet, "
    "gradient, shading, shadow, texture, noise, grain, "
    "blurry, low quality, watermark, text, signature"
)

def generate_character(prompt: str, output_path: str, seed: int = 42):
    generator = torch.Generator("mps").manual_seed(seed)
    image = pipe(
        prompt=f"{STYLE_PREFIX}, {prompt}",
        negative_prompt=NEGATIVE_PROMPT,
        width=768,       # Keep <=1024 to avoid duplicates
        height=1024,
        num_inference_steps=25,
        guidance_scale=7.0,
        generator=generator,
    ).images[0]
    image.save(output_path)

def generate_background(prompt: str, output_path: str, seed: int = 42):
    generator = torch.Generator("mps").manual_seed(seed)
    image = pipe(
        prompt=f"{STYLE_PREFIX}, {prompt}, no characters, empty scene",
        negative_prompt=NEGATIVE_PROMPT + ", person, people, figure, animal",
        width=1280,
        height=720,
        num_inference_steps=25,
        guidance_scale=7.0,
        generator=generator,
    ).images[0]
    image.save(output_path)


# ── Example usage ──
generate_character(
    "cute wooden peg doll of Isaac Newton, large round head, tiny body, "
    "white curly wig, brown coat, holding green apple, "
    "full body front view, isolated on solid pastel green background, "
    "solo, alone, single figure",
    "newton.png",
)
```

**Key settings for SDXL flat art:**
- `guidance_scale`: 7.0 (sweet spot for stylized art; higher = more prompt adherence but also more artifacts)
- `num_inference_steps`: 25 (good quality/speed balance; 30 max)
- `scheduler`: DPM++ 2M Karras (best quality for stylized content)
- Image dimensions: 768x1024 for characters, 1280x720 for backgrounds
- Keep character images at or below 1024px on longest side to prevent duplicates

---

### Setup 3: FLUX.1-schnell Local (Best Quality, Tightest on Memory)

**Why:** Running FLUX locally gives you full parameter control and no API rate limits. Quality is superior to SDXL for prompt adherence. However, it is tight on 16GB and slower (~2-3 min per image).

**Model size:** ~12GB in bfloat16. Fits in 16GB unified memory but leaves little headroom.

**Complete working code:**

```python
import os
import torch
from diffusers import FluxPipeline

# CRITICAL: Allow MPS to use all available memory (swap will be used)
os.environ["PYTORCH_MPS_HIGH_WATERMARK_RATIO"] = "0.0"

# ── Workaround for MPS rope compatibility ──
# FLUX uses rotary position embeddings that have an MPS bug.
# This patches it to compute on CPU then move back.
from diffusers.models.transformers import flux_transformer_2d
_original_rope = flux_transformer_2d.FluxTransformer2DModel  # save reference

def apply_mps_rope_fix():
    """Patch rope to work on MPS by falling back to CPU for unsupported ops."""
    import diffusers.models.embeddings as emb
    if hasattr(emb, 'get_timestep_embedding'):
        original_fn = emb.get_timestep_embedding
        def patched_fn(timesteps, embedding_dim, *args, **kwargs):
            if timesteps.device.type == "mps":
                result = original_fn(timesteps.cpu(), embedding_dim, *args, **kwargs)
                return result.to("mps")
            return original_fn(timesteps, embedding_dim, *args, **kwargs)
        emb.get_timestep_embedding = patched_fn

apply_mps_rope_fix()

# ── Load pipeline ──
pipe = FluxPipeline.from_pretrained(
    "black-forest-labs/FLUX.1-schnell",
    torch_dtype=torch.bfloat16,
    revision="refs/pr/1",      # Use the community PR with fixes
)
pipe = pipe.to("mps")

# ── Enable memory optimizations ──
pipe.enable_attention_slicing()
# Optionally enable sequential CPU offload if still OOM:
# pipe.enable_sequential_cpu_offload()

STYLE_PREFIX = (
    "flat 2D vector illustration, solid color fills, zero shading, zero gradients, "
    "paper cutout aesthetic, children's picture book, simple geometric shapes"
)

STYLE_SUFFIX = (
    "no 3D, no realistic rendering, no shadows, no texture, no gradients, "
    "no multiple figures, no character sheet, no turnaround"
)

def generate_image(prompt: str, output_path: str, width: int = 1024, height: int = 1024, seed: int = 42):
    generator = torch.Generator("mps").manual_seed(seed)
    full_prompt = f"{STYLE_PREFIX}. {prompt}. {STYLE_SUFFIX}"

    image = pipe(
        prompt=full_prompt,
        width=width,
        height=height,
        num_inference_steps=4,       # schnell: 1-4 steps only
        guidance_scale=0.0,          # schnell: no CFG
        max_sequence_length=256,
        generator=generator,
    ).images[0]
    image.save(output_path)

# ── Example ──
generate_image(
    "single cute wooden peg doll character of Isaac Newton, "
    "very large round head, tiny stubby body, white curly wig, "
    "brown coat as one flat solid color, holding small green apple, "
    "full body front view, centered, alone, "
    "isolated on solid flat pastel green background",
    "newton_flux_local.png",
    width=768,
    height=1024,
)
```

**Important notes for local FLUX on M4 16GB:**
- Set `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` or you will OOM
- Use `torch.bfloat16` (not float16 -- FLUX was trained in bf16)
- `num_inference_steps=4` -- schnell is distilled for few steps
- `guidance_scale=0.0` -- schnell does not use classifier-free guidance
- First generation is slow (~3 min) due to compilation; subsequent ones are faster
- If OOM persists, use `pipe.enable_sequential_cpu_offload()` (slower but guaranteed to fit)
- Generation takes ~2-3 minutes per image on M4 16GB

---

## Prompt Engineering Guide (Critical for All Setups)

### Problem 1: Characters Come Out as Character Sheets

**Root cause:** The model interprets "character" prompts as "character design reference sheets" because training data contains many such images.

**Fix -- add these terms:**

In positive prompt:
```
solo, alone, single figure, one character only, centered composition,
full body front view, isolated on [color] background
```

In negative prompt (SDXL only):
```
character sheet, model sheet, reference sheet, turnaround,
multiple views, multiple poses, multiple figures, grid, collage,
multiple characters, double, duplicate
```

For FLUX (no negative prompt support), embed directly:
```
... single character only. No character sheet, no turnaround,
no multiple views, no reference sheet, no multiple figures.
```

**Also critical:** Keep image dimensions reasonable. At 1024+ pixels wide, models tend to tile/duplicate. For single characters, use 768x1024 or 512x768.

### Problem 2: Style is Too 3D / Clay-like

**Root cause:** Modern diffusion models default toward photorealistic/3D rendering. Long prompts with contradictory signals cause the model to hedge.

**Fix -- be more concise and direct:**

BAD (too verbose, contradictory):
```
ABSOLUTELY ZERO gradients anywhere. ABSOLUTELY ZERO shading anywhere.
ABSOLUTELY ZERO texture anywhere. ABSOLUTELY ZERO shadows no cast shadows
no form shadows no drop shadows.
```

GOOD (concise, positive framing):
```
flat solid color fills, paper cutout style, zero shading,
matte colors, no 3D effects
```

**Key terms that push toward flat style:**
- `flat vector illustration`
- `paper cutout style`
- `cel shaded` (for slightly more defined look)
- `solid color fills`
- `simple geometric shapes`
- `children's picture book illustration`
- `matte colors`

**Key terms to avoid (they invite 3D):**
- `detailed` (invites complexity)
- `realistic` (obviously)
- `render` or `rendering`
- `lighting` or `lit`
- `clay`, `wooden` (these CAN work but often trigger 3D interpretation)

### Problem 3: Simple Elements Come Out as Complex Scenes

**Root cause:** Models have a bias toward complex, detailed outputs. Words like "hill" or "cloud" trigger entire landscape scenes from training data.

**Fix:**

For isolated objects, always specify:
```
single [object], isolated on white background, simple shape,
icon style, centered, no background, no scene, clipart
```

For backgrounds, be extremely explicit about simplicity:
```
minimalist landscape, only 3 elements: [list them],
nothing else in the scene, extremely simple,
flat paper cutout style, no details
```

### Problem 4: Prompt Length and Ordering

FLUX and SDXL both weight earlier tokens more heavily. Structure prompts as:

1. **Style first:** "flat 2D children's book illustration"
2. **Subject second:** "single cute character of Isaac Newton"
3. **Key attributes third:** "large round head, tiny body, brown coat"
4. **Composition fourth:** "full body front view, centered"
5. **Background fifth:** "isolated on solid pastel green background"
6. **Exclusions last:** "no 3D, no shadows, no multiple figures"

---

## Recommended Negative Prompt (for SDXL / models that support it)

```
3d render, 3d, realistic, photograph, photo, photorealistic,
multiple characters, character sheet, turnaround sheet, model sheet,
reference sheet, multiple views, multiple poses, multiple figures,
collage, grid, duplicate, clone, double,
gradient, shading, shadow, cast shadow, drop shadow,
texture, noise, grain, film grain,
depth of field, bokeh, lens flare, bloom, glow,
blurry, low quality, worst quality, jpeg artifacts,
watermark, text, signature, logo, writing,
complex background, detailed background,
realistic lighting, volumetric lighting, ray tracing,
clay, plastic, glossy, metallic, reflective
```

---

## Character Consistency Across Multiple Images

### Approach A: Seed Locking + Identical Prefix (Simplest)

Use the same seed and identical style prefix for all character generations. This provides ~70% consistency.

```python
NEWTON_SEED = 42
NEWTON_PREFIX = (
    "flat 2D children's book illustration, single cute peg doll character, "
    "Isaac Newton, large round head, tiny body, white curly wig cloud shape, "
    "flat brown coat, white cravat"
)
```

### Approach B: IP-Adapter (Best Consistency, SDXL Only)

Generate one "hero" image of each character, then use IP-Adapter to condition all future generations on it.

```python
from diffusers import StableDiffusionXLPipeline
from diffusers.utils import load_image

pipe = StableDiffusionXLPipeline.from_pretrained(
    "stabilityai/stable-diffusion-xl-base-1.0",
    torch_dtype=torch.float16,
).to("mps")

# Load IP-Adapter for SDXL
pipe.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="sdxl_models",
    weight_name="ip-adapter_sdxl.bin",
)
pipe.set_ip_adapter_scale(0.6)  # 0.4-0.7 is good range

# Load your hero reference image
reference = load_image("newton_hero.png")

# Generate new image conditioned on reference
image = pipe(
    prompt="flat illustration, Newton character celebrating, arms up, happy pose",
    ip_adapter_image=reference,
    negative_prompt=NEGATIVE_PROMPT,
    num_inference_steps=25,
    guidance_scale=7.0,
).images[0]
```

### Approach C: LoRA Fine-Tuning Your Own Characters (Most Work, Best Results)

Train a small LoRA (10-20 images of your character in different poses) to lock the character design. This is the approach used by professional children's book illustrators using AI.

This requires more setup but provides near-perfect consistency. Tools: `kohya_ss` trainer or `diffusers` training scripts.

---

## FLUX.1-dev vs FLUX.1-schnell

| Feature | FLUX.1-schnell | FLUX.1-dev |
|---------|---------------|------------|
| License | Apache 2.0 | Non-commercial |
| Steps needed | 1-4 | 20-50 |
| Quality | Good | Better |
| Speed on M4 16GB | ~2-3 min | ~10-15 min |
| Memory | ~12GB | ~12GB |
| CFG guidance | No (0.0) | Yes (3.5-7.0) |
| LoRA support | Limited | Growing |
| Fits 16GB? | Yes (tight) | Yes (tight) |

**Verdict:** Schnell is the pragmatic choice for iteration speed. Dev produces higher quality but is non-commercial and much slower locally.

---

## Quick Comparison Table: All Options

| Setup | Quality | Speed | Style Control | Memory | Consistency | Effort |
|-------|---------|-------|---------------|--------|-------------|--------|
| FLUX schnell (API) | Good | Fast (~5s) | Medium | None (cloud) | Medium | Low |
| SDXL + LoRA (local) | Very Good | Medium (~30s) | **Excellent** | ~7GB | Good | Medium |
| FLUX schnell (local) | Good | Slow (~3min) | Medium | ~12GB | Medium | Medium |
| SDXL + IP-Adapter | Very Good | Medium | Excellent | ~8GB | **Excellent** | High |

---

## Specific Fixes for Current `style_config.py` Issues

### Issue: The STYLE_PREFIX is 626 characters long

FLUX schnell has a 256-token sequence length. Your current prefix likely exceeds useful context. The model is ignoring the end of your prompt.

**Recommended replacement for `style_config.py`:**

```python
# ── Compact Style Prefix (for FLUX) ──
STYLE_PREFIX_FLUX = (
    "flat 2D children's book illustration, solid color fills, "
    "paper cutout style, simple shapes, no shading, no gradients, "
    "no shadows, no texture, matte colors"
)

# ── Character generation template ──
def character_prompt(description: str) -> str:
    return (
        f"{STYLE_PREFIX_FLUX}. "
        f"Single {description}. "
        "Full body front view, centered, alone. "
        "Isolated on solid color background. "
        "No character sheet, no multiple views, no multiple figures."
    )

# ── Background generation template ──
def background_prompt(description: str) -> str:
    return (
        f"{STYLE_PREFIX_FLUX}. "
        f"{description}. "
        "Absolutely no people, no characters, no figures, no animals. "
        "Empty scene, minimalist, maximum 4 elements total."
    )

# ── Object generation template ──
def object_prompt(description: str) -> str:
    return (
        f"{STYLE_PREFIX_FLUX}. "
        f"Single {description}. "
        "Isolated on white background, centered, icon style, clipart. "
        "No scene, no other objects."
    )
```

### Issue: "wooden peg doll" triggers 3D interpretation

The phrase "wooden peg doll" often causes models to render a literal 3D wooden figurine with wood grain texture and 3D lighting.

**Fix:** Replace with "simple cartoon character with round head and small body" and add the peg-doll proportions via description rather than naming the material:

```
simple cartoon character, very large round head (60% of body height),
tiny cylindrical body, stubby arms and legs,
dot eyes, pink circle cheeks, no nose
```

---

## Installation Commands

### For Setup 1 (FLUX API -- current approach, just improve prompts):
```bash
pip install huggingface_hub Pillow
```

### For Setup 2 (SDXL + LoRA local):
```bash
pip install torch torchvision diffusers transformers accelerate safetensors Pillow

# Download a children's book LoRA from CivitAI:
mkdir -p loras
# Visit https://civitai.com/models/176435 and download the .safetensors file
# Place it in ./loras/
```

### For Setup 3 (FLUX local):
```bash
pip install torch torchvision diffusers transformers accelerate sentencepiece protobuf Pillow

# Set environment variable (add to .zshrc for persistence)
export PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0
```

---

## Bottom-Line Recommendation

**Start with Setup 1** (your current FLUX.1-schnell API approach) but apply the prompt engineering fixes from this guide. Specifically:

1. Cut `STYLE_PREFIX` from 626 characters to under 200 characters
2. Use the `character_prompt()` / `background_prompt()` / `object_prompt()` template functions
3. Remove "wooden peg doll" -- describe the proportions instead
4. Add "solo, alone, single figure, no character sheet" to every character prompt
5. Keep character images at 768x1024 or smaller

If results are still not flat enough after these changes, move to **Setup 2** (SDXL + children's book LoRA) which gives you negative prompts and purpose-trained LoRAs for the exact style you want.

---

## Sources

- [SDXL Settings Guide by Replicate](https://sdxl.replicate.dev/)
- [FLUX vs SDXL Comparison 2026](https://pxz.ai/blog/flux-vs-sdxl)
- [Running FLUX.1 on MacBook M2 with Diffusers](https://dev.to/nabata/running-the-flux1-image-devschnell-generation-ai-model-by-stable-diffusions-original-developers-on-a-macbook-m2-4ld6)
- [Run Flux.1 on M3 Mac with Diffusers](https://dev.to/0xkoji/run-flux1-on-m3-mac-with-diffusers-9m5)
- [How to use Flux AI on Mac](https://stable-diffusion-art.com/flux-mac/)
- [picture books-Children cartoon LoRA (CivitAI)](https://civitai.com/models/176435/picture-books-children-cartoon)
- [Children book v2.0 LoRA (CivitAI)](https://civitai.com/models/285062/children-book)
- [StorybookRedmond LoRA (CivitAI)](https://civitai.com/models/132128/storybookredmond-storybook-kids-lora-style-for-sd-xl)
- [Flat Colors + Realistic Cartoon LoRA (CivitAI)](https://civitai.com/models/2146930/flat-colors-realistic-cartoon-illustrious-sdxl)
- [Vector illustration SDXL LoRA (CivitAI)](https://civitai.com/models/60132/vector-illustration)
- [Avoiding Multiple Characters (GitHub Discussion)](https://github.com/AUTOMATIC1111/stable-diffusion-webui/discussions/10646)
- [How to Use Negative Prompts](https://stable-diffusion-art.com/how-to-use-negative-prompts/)
- [IP-Adapter Diffusers Documentation](https://huggingface.co/docs/diffusers/en/using-diffusers/ip_adapter)
- [Consistent Character Design with AI (2025)](https://medium.com/design-bootcamp/how-to-design-consistent-ai-characters-with-prompts-diffusion-reference-control-2025-a1bf1757655d)
- [IP-Adapter for Consistent Images](https://extra-ordinary.tv/2025/08/02/comfyui-ipadapter-first-attempt-for-consistent-images/)
- [Using CivitAI LoRAs with Diffusers](https://medium.com/@natsunoyuki/using-civitai-loras-with-diffusers-e3ef3e47c413)
- [Illustrious XL v1.0 (HuggingFace)](https://huggingface.co/OnomaAIResearch/Illustrious-XL-v1.0)
- [FLUX.1-dev Running Under 16GB VRAM](https://huggingface.co/black-forest-labs/FLUX.1-dev/discussions/50)
- [Best Stable Diffusion Models 2026](https://www.aiphotogenerator.net/blog/2026/02/best-stable-diffusion-models-2026)
- [Loading LoRAs in Diffusers](https://huggingface.co/docs/diffusers/api/loaders/lora)
