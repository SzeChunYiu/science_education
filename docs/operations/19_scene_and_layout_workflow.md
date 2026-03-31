# 19. Scene And Layout Workflow

This document explains how reusable assets become actual video scenes.

Assets alone do not produce good videos. The missing layer is scene design and layout logic.

Related docs:

- `18_asset_generation_workflow.md`
- `20_evidence_based_video_design_principles.md`
- `21_storybook_visual_style_guide.md`
- `14_end_to_end_pipeline_runbook.md`
- `production-sequence.md`
- `../reference/scene-templates.md`
- `../reference/scene-patterns-raw.md`

---

## Why This Layer Matters

The project should not jump directly from:

- script

to:

- final rendered video

without an explicit scene layer.

The correct structure is:

1. script
2. scene plan
3. layout template per scene
4. asset/diagram binding
5. render

Evidence-based visual rules for how these scenes should be designed are documented in:

- `20_evidence_based_video_design_principles.md`

This is what keeps the videos visually consistent across hundreds of episodes.

The visual art-direction system that should govern those scene choices is documented in:

- `21_storybook_visual_style_guide.md`

---

## Core Scene Types

Future sessions should treat these as the base scene vocabulary:

- `character_intro`
- `historical_setting`
- `object_demo`
- `equation_focus`
- `diagram_explain`
- `comparison_split`
- `timeline`
- `worked_example`
- `limit_or_breakdown`
- `outro_bridge`

Not every episode needs all of them, but most long-form episodes will use several of these repeatedly.

---

## Scene Planning Workflow

For each episode:

1. read the script
2. split it into explanation beats
3. assign each beat a scene type
4. identify what is reusable asset, what is programmatic diagram, and what is plain text/equation overlay
5. apply the approved visual-style system from `21_storybook_visual_style_guide.md`
6. only then move to layout/render

Questions to answer per beat:

- Is this a human/historical moment?
- Is this an object interaction?
- Is this primarily an equation?
- Is this a comparison?
- Is this a diagram better generated in code?

## Automatic Slide Planner Method

The production path now treats every supported scene like an automatically planned slide before it is animated.

The active chain is:

1. script
2. scene mapper
3. slide planner
4. scene factory
5. timeline render

The planner chooses a local slide archetype and assigns named boxes for that archetype before the renderer builds motion.

Current active archetypes are documented in:

- `../reference/slide_layout_inventory.md`

Operational rule:

- the planner is the canonical layout method for the core production templates
- previews should exercise the same planner-backed path whenever possible
- scene-specific overrides are allowed, but they must be explicit and not hidden in ad hoc local coordinates

Planner requirements:

- choose one slide archetype per scene
- keep one clear focal point
- place equations, visuals, captions, and metadata into stable named boxes
- preserve subtitle-safe regions
- keep text concise or roll it over time in the same box
- allow equation placement anywhere the archetype supports, not only in a top-biased default slot
- default to plain text for routine labels, metadata, and callouts instead of decorative text cards
- choose a subject-matched background when the beat implies one, otherwise keep the scene neutral rather than mismatched
- if the focal object is naturally mobile, the layout plan should anticipate motion rather than forcing it into a static pose

Canonical vs archived docs:

- active operational guidance lives in this workflow doc, `22_animation_production_runbook.md`, `powerpoint_layout_rules.md`, and `slide_layout_inventory.md`
- older scene-template catalogs remain useful as background reference, but they are no longer the main implementation contract

---

## Layout Rules

Each scene type should have a stable layout.

Examples:

### Character Intro

- character on left or center
- name/date attached as plain text, not a detached lower-third card
- minimal props
- empty space for short narration text if needed

### Equation Focus

- dark or neutral background
- one main equation, large and centered
- labels appear in sequence
- avoid clutter and too many simultaneous math objects

### Object Demo

- one or two objects only
- clear motion direction
- labels only if essential
- if the object naturally moves, the demo should animate that motion in a physically sensible way

### Comparison Split

- left/right panels
- one idea per side
- strong visual contrast

### Timeline

- horizontal chronology
- no more than a few major figures at once
- date anchors visible

---

## Asset Binding Rules

For each scene, decide whether the visual source is:

- reusable asset from `data/assets/`
- code-generated diagram or equation
- simple layout primitive
- episode-specific media

Preferred rule:

- use reusable assets for characters and recurring objects
- use code for equations, graphs, and precise scientific diagrams

Do not turn every scientific diagram into a painted illustration if a clean programmatic diagram is better.

---

## 16:9 And 9:16 Variants

Every important scene type should eventually have:

- landscape rules for long-form YouTube
- vertical rules for Shorts/TikTok

The content can be the same while the layout changes.

Vertical adaptation usually means:

- fewer simultaneous elements
- larger focal object
- less side-by-side comparison
- tighter text usage

---

## Relation To Existing Code

Current code already contains pieces of this pipeline:

- `src/pipeline/` for script parsing and scene mapping
- `src/pipeline/slide_planner.py` for PowerPoint-style automatic layout selection
- `src/animation/` for render/export support

Future sessions should improve those systems with scene-type awareness rather than bypass them manually.

---

## Immediate Next Step After Phase 1 Assets

Once the first reusable assets are generated, the next high-value implementation step is:

1. define a compact scene-template set for the most common long-form beats
2. create `3-5` style frames using the approved storybook visual system
3. bind those templates to the shared asset library
4. test them on one representative episode

Best first candidate:

- a strong early classical mechanics episode such as Newton's laws or conservation laws

That gives a realistic test of:

- character scenes
- object scenes
- equation scenes
- historical scenes

---

## Output Standard

Every episode should eventually be able to produce:

- a scene plan
- a list of required reusable assets
- a list of required programmatic diagrams
- a layout/render spec

That is the handoff point from writing into production.
