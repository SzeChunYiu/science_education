# Scene Template Kit

This document is the production-facing scene system for the project.

## Status

This file remains useful as design guidance for scene families and motion vocabulary.

For the active automatic layout method, treat these as the higher-priority implementation references:

- `../operations/19_scene_and_layout_workflow.md`
- `../operations/22_animation_production_runbook.md`
- `powerpoint_layout_rules.md`
- `slide_layout_inventory.md`

It sits between:

- the script
- the asset library
- the style guide
- the final render

Use this with:

- `../operations/18_asset_generation_workflow.md`
- `../operations/19_scene_and_layout_workflow.md`
- `../operations/20_evidence_based_video_design_principles.md`
- `../operations/21_storybook_visual_style_guide.md`
- `../subjects/physics/asset-inventory.md`

## Design Goal

Scenes should feel like a warm, printed storybook while still carrying precise science.

The practical standard is:

- one scene = one idea
- one visual focal point
- one primary motion beat
- one clear takeaway

If a scene needs to explain multiple ideas at once, split it.

## Frame Zones

Use these zones for 16:9 composition:

- `top zone` - title, chapter label, or short emphasis line
- `main zone` - the scientific content and focal illustration
- `lower zone` - supporting labels, date stamps, small callouts
- `subtitle reserve` - keep clear for captions and burned-in subtitles

For 9:16, compress the same logic into:

- `top` - small title or hook line
- `center` - focal subject and main explanation
- `bottom safe zone` - captions and CTA only

Do not place critical equations or labels inside the subtitle reserve.

## Core Templates

### 1. `CHARACTER_INTRO`

Purpose: introduce a scientist, inventor, or historical figure.

Frame zones: character in the main zone, name and dates in the lower zone, optional small prop or background cue.

16:9 layout: one large chibi-style character slightly off-center, simple background, lower-third name card, optional period object on the opposite side.

9:16 adaptation: character fills most of the vertical frame, name card stacked under the figure, background simplified to one strong color and one prop.

Motion cues: gentle pop-in, slight bob, name tag slide, minimal parallax.

Scientific-accuracy guardrails: clothing, hair, and props must match the historical period; do not mix eras; do not embellish with fake inventions.

Required asset types: character portrait, optional prop, optional backdrop, nameplate.

Common failure modes: too much empty space, incorrect costume, over-designed background, text too small.

### 2. `HISTORICAL_SETTING`

Purpose: establish the time, place, and intellectual environment of a concept.

Frame zones: background dominates the main zone, character or object acts as a small anchor, date label in the lower zone.

16:9 layout: wide scene with one strong environment cue such as workshop, observatory, lab, or courtyard.

9:16 adaptation: crop tightly to the single most distinctive environmental clue; remove extra figures.

Motion cues: slow pan, gentle reveal, paper-flap or slide transition.

Scientific-accuracy guardrails: the setting must be historically plausible and not anachronistic; a setting is context, not evidence.

Required asset types: background, character or silhouette, period props, date label.

Common failure modes: historical clutter, modern-looking tools, decorative elements that compete with the lesson.

### 3. `OBJECT_DEMO`

Purpose: show a physical object or setup in action.

Frame zones: the object occupies the main zone; labels sit near the object; no clutter in the lower reserve.

16:9 layout: one or two objects only, large and readable, with arrows or labels placed close to the relevant parts.

9:16 adaptation: single object centered vertically, fewer labels, larger scale, motion constrained to the middle third.

Motion cues: slide, rotate, tilt, extend, or pull apart; keep motion simple and legible.

Scientific-accuracy guardrails: preserve direction, scale relationships, and causal order; do not animate impossible motions for convenience.

Required asset types: object asset, labels, arrows, optional hand or pointer.

Common failure modes: too many props, labels detached from the object, motion that looks like a toy instead of an experiment.

### 4. `EQUATION_REVEAL`

Purpose: land a key equation cleanly and memorably.

Frame zones: equation in the main zone, symbol labels in the lower or side zones, title only if essential.

16:9 layout: large centered equation, with each symbol introduced one at a time or annotated with small callouts.

9:16 adaptation: equation stacked vertically if possible, with very short labels and generous margins.

Motion cues: line-by-line build, highlight pulse, box-in reveal, symbol-by-symbol annotation.

Scientific-accuracy guardrails: symbols must match the script exactly; do not rearrange terms for aesthetics; note when the displayed equation is a teaching simplification.

Required asset types: equation graphic or typeset overlay, symbol labels, highlight shapes.

Common failure modes: unreadable math, too many annotations, crowded lower-third captions.

### 5. `DERIVATION_STEP`

Purpose: show a derivation or proof as a controlled sequence.

Frame zones: center-aligned or left-aligned derivation in the main zone, final result in a highlighted area, reserve space below for captions.

16:9 layout: one derivation column with sequential steps appearing top to bottom; use a highlighted final box at the end.

9:16 adaptation: fewer steps per screen, split long derivations into more scenes, keep each step large.

Motion cues: stepwise reveal, substitution arrow, highlight on the changed term.

Scientific-accuracy guardrails: every step must be mathematically valid; do not skip hidden algebra unless the script explicitly says it is a pedagogical shortcut.

Required asset types: math overlay, highlight markers, optional side note panel.

Common failure modes: too many steps on one frame, skipped logic, tiny equations, overuse of decorative icons.

### 6. `DIAGRAM_EXPLAIN`

Purpose: explain a labeled scientific diagram.

Frame zones: diagram in the main zone, labels near features, short title above if needed.

16:9 layout: diagram centered with clean margins; use arrows, braces, or callouts to connect labels to features.

9:16 adaptation: simplify the diagram to the minimum necessary parts and place labels on short leader lines.

Motion cues: label-by-label reveal, pointer sweep, highlight one region at a time.

Scientific-accuracy guardrails: labels must correspond to the actual parts of the system; do not oversimplify away a crucial direction, sign, or dependency.

Required asset types: diagram asset, labels, arrows, optional legend.

Common failure modes: too many labels, crossing callout lines, vague geometry, labels too far from targets.

### 7. `COMPARISON_SPLIT`

Purpose: compare two theories, two cases, or two outcomes.

Frame zones: left and right panels in the main zone, short titles above each panel, shared takeaway below if needed.

16:9 layout: two balanced columns; each side gets one idea only.

9:16 adaptation: stack the two panels vertically unless the comparison is only symbolic.

Motion cues: alternating reveal, side-by-side emphasis pulse, checkmark or contrast marker.

Scientific-accuracy guardrails: compare like with like; do not merge unrelated cases into a false contrast.

Required asset types: two diagrams or objects, panel labels, divider, optional arrow or mark.

Common failure modes: uneven panel weight, too much text, comparison that is rhetorical rather than scientific.

### 8. `TIMELINE_SEQUENCE`

Purpose: show historical development or the transfer of an idea across people or eras.

Frame zones: horizontal timeline in 16:9, stacked timeline or stepped chronology in 9:16, date markers in the lower zone.

16:9 layout: left-to-right sequence of figures or milestones with arrows or connecting lines.

9:16 adaptation: vertical stack with one milestone per tier.

Motion cues: milestone pop-in, line draw, date stamp reveal.

Scientific-accuracy guardrails: preserve chronology; do not compress events so much that cause and effect become misleading.

Required asset types: portraits, milestone icons, dates, connector lines.

Common failure modes: timeline crowding, swapped chronology, too many names in one frame.

### 9. `MOTION_SCENE`

Purpose: show a process changing over time, such as motion, oscillation, orbit, or collision.

Frame zones: moving subject in the main zone, optional position markers or trails, minimal text.

16:9 layout: wide path or track with enough room to show before and after states.

9:16 adaptation: use a smaller motion path and more vertical stacking; avoid wide side-to-side travel that gets cropped badly.

Motion cues: actual movement, trail line, time markers, before/after frames.

Scientific-accuracy guardrails: preserve vector direction, timing, and relative scale; do not animate motion that contradicts the explanation.

Required asset types: moving object asset, trajectory path, labels, optional before/after states.

Common failure modes: motion too fast to read, camera motion fighting object motion, path geometry that implies the wrong physics.

### 10. `OUTRO_BRIDGE`

Purpose: close the episode and set up the next one.

Frame zones: central takeaway card in the main zone, small forward hook in the lower zone, optional series marker at top.

16:9 layout: simple branded end card with one visual anchor and one short next-step line.

9:16 adaptation: keep the call-to-action centered and short; avoid large paragraph text.

Motion cues: fade-in, card slide, final emphasis pulse.

Scientific-accuracy guardrails: do not introduce new claims here; this is a summary and transition scene only.

Required asset types: brand card, series icon, optional character cameo, title text.

Common failure modes: turning the outro into a second lecture, using too much text, ending without a clear bridge.

## Template Selection Rules

Use templates based on the script beat, not personal taste.

Recommended defaults for physics episodes:

- history beat -> `CHARACTER_INTRO` or `HISTORICAL_SETTING`
- experiment beat -> `OBJECT_DEMO`
- main theorem or law -> `EQUATION_REVEAL`
- derivation beat -> `DERIVATION_STEP`
- explanation of a figure or setup -> `DIAGRAM_EXPLAIN`
- contrast or limitation -> `COMPARISON_SPLIT`
- chronology or lineage -> `TIMELINE_SEQUENCE`
- physical change over time -> `MOTION_SCENE`
- closing beat -> `OUTRO_BRIDGE`

## Asset Mapping

Reusable assets should be named and stored so templates can find them quickly:

- characters
- objects
- backgrounds
- diagram primitives
- labels and icons

Templates should not depend on one-off bespoke art unless the episode absolutely requires it.

## Quality Check

Before approving a template scene, check:

- the focal idea is obvious in under two seconds
- captions have safe space
- the scene still reads at thumbnail size
- the science is not distorted by decoration
- the storybook style remains warm and consistent

If a scene fails any of these checks, simplify it before generating more assets.
