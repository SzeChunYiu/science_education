# 18. Asset Generation Workflow

This document explains how reusable visual assets should be produced for the project.

This is not about per-episode rendered media. It is about the shared asset library that multiple episodes can reuse.

Related docs:

- `14_end_to_end_pipeline_runbook.md`
- `production-sequence.md`
- `21_storybook_visual_style_guide.md`
- `../subjects/physics/asset-inventory.md`
- `/Users/billy/Desktop/projects/science_education/data/assets/README.md`

---

## Purpose

Reusable assets exist to reduce repeated illustration work across episodes.

Typical reusable assets:

- historical characters
- simple physics objects
- background scenes
- overlay/UI elements

These assets should live in:

- `data/assets/{subject}/`

They should not live inside:

- `output/`

because `output/` is for generated episode deliverables, not shared asset libraries.

---

## Current Physics Setup

Physics reusable assets are stored in:

- `data/assets/physics/`

Current generator:

- `python3 -m src.generate_physics_assets`

Current manifest:

- `data/assets/physics/manifests/phase1_core_assets.json`

Inventory source:

- `docs/subjects/physics/asset-inventory.md`

---

## Asset Production Model

The intended workflow is:

1. audit scripts and identify repeated visual needs
2. document those needs in the asset inventory
3. convert a priority slice of the inventory into a generation manifest
4. generate assets into the shared library
5. review quality and consistency
6. promote accepted assets for production reuse

Do not generate assets blindly without tying them to an inventory or a real episode need.

---

## Priority Rules

Generate in this order:

1. assets with high reuse across many scripts
2. assets needed by the next production wave
3. assets that unblock scene templates
4. nice-to-have assets later

For physics, this typically means:

- first: Newton / Galileo / Aristotle / Euler / Noether / Lagrange / Hamilton / Kepler and core objects
- then: electromagnetism and thermodynamics character sets
- then: deeper quantum/QFT figures and more niche objects

---

## Categories

Use stable categories:

- `characters/`
- `objects/`
- `backgrounds/`
- `elements/`
- `test_*` folders only for evaluation packs
- `manifests/` for generation batches

If a test asset becomes production-worthy, either:

- copy/regenerate it into the main category with a stable filename
- or document clearly that the `test_*` asset is being treated as accepted production input

---

## Naming Rules

Use predictable filenames:

- characters: `char_<name>.png`
- objects: `obj_<thing>.png`
- backgrounds: `bg_<scene>.png`
- elements: `element_<thing>.png`

Examples:

- `char_hamilton.png`
- `obj_pendulum.png`
- `bg_deep_space.png`

Avoid:

- version spam in stable production folders
- vague names like `image1.png`
- storing final production assets only under `test_v3/`

---

## Manifest Workflow

A manifest is the bridge between the written inventory and actual generation.

Each manifest entry should specify:

- filename
- category
- width
- height
- generation prompt

Current example:

- `data/assets/physics/manifests/phase1_core_assets.json`

Run it with:

```bash
cd /Users/billy/Desktop/projects/science_education
python3 -m src.generate_physics_assets --manifest data/assets/physics/manifests/phase1_core_assets.json
```

Generate only selected assets:

```bash
python3 -m src.generate_physics_assets --names char_euler.png obj_pendulum.png
```

---

## Quality Bar

A reusable asset is acceptable only if it is:

- visually consistent with the house style
- visually consistent with `21_storybook_visual_style_guide.md`
- easy to read at video scale
- free of unwanted text/logos/artifacts
- recognizable enough to do its job
- simple enough to combine cleanly with layouts and overlays

For characters:

- correct era silhouette
- correct hair/beard/clothing cues
- clean single-figure composition

For objects:

- simple shape
- no anthropomorphic face or expression
- no glossy fake-3D look

For backgrounds:

- no clutter
- no accidental extra figures
- enough empty space for overlays and narration-driven motion

---

## Promote Or Reject

After generation, classify assets:

- `accepted`
- `regenerate`
- `reject`

If accepted:

- leave the asset in the stable production folder
- note it in the inventory if useful

If rejected:

- do not quietly rely on it in production scenes
- either fix the prompt and regenerate, or remove it later

---

## What Comes After Asset Generation

Assets are ingredients, not finished scenes.

After reusable assets exist, the next workflow is:

1. scene template design
2. layout rules for those scene types
3. episode scene mapping
4. render assembly

That follow-on workflow is documented in:

- `19_scene_and_layout_workflow.md`
