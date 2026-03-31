# 22. Animation Production Runbook

This document explains how the project should move from a finished scene board to style frames, animatics, reusable template scenes, and final render assets.

It is the operational bridge between:

- `19_scene_and_layout_workflow.md`
- `20_evidence_based_video_design_principles.md`
- `21_storybook_visual_style_guide.md`
- `../reference/scene-template-kit.md`
- `../subjects/physics/scene-design/`

---

## Purpose

The project already has scripts, assets, scene boards, layout primitives, and animation primitives.

What is missing is a single production workflow that tells future sessions:

1. how to turn a scene board into visual assets
2. how to turn those assets into motion
3. how to validate the result before render
4. how to reuse the result across later episodes

The goal is a repeatable system, not one-off hand-built scenes.

## QA Baseline

Every scene should pass the same baseline checks before it is accepted for render:

- the scene makes sense without hand-waving
- the scene matches the described beat and narration
- the scene feels realistic and physically believable
- the key named object or action is actually visible on screen
- on-screen text stays concise, or it is revealed over time in the same box instead of being dumped all at once
- equations render correctly, including integrals, superscripts, subscripts, and other formatted math
- if the focal object naturally moves, the default render should show that motion in a physically meaningful way rather than freezing it as a still image
- routine labels, names, metadata, and callouts default to plain text instead of decorative text boxes
- text regions are proportionate to the copy they contain and do not leave oversized empty cards
- the background belongs to the subject being introduced, or stays neutral if no fitting background exists yet
- text cards, ribbons, and placeholder shapes use colors that fit the current scene palette
- preview outputs make audio presence or absence explicit

If a scene fails any of these checks, revise the scene before treating the render as production-ready.

---

## Production Chain

Use this exact chain:

1. script
2. scene board
3. style frames
4. animatic
5. reusable template scenes
6. final render assets

Each step has a distinct job:

- `scene board` defines the beats, shot purpose, and required assets
- `style frames` lock the look, palette, typography, and composition
- `animatic` proves timing and clarity
- `reusable template scenes` turn repeated patterns into production assets
- `final render assets` are the episode-specific outputs for publishing

Do not skip directly from board to final render.

## Planner Outputs In Production

The production renderer now uses an automatic slide-planner step for the core scene families before animation is built.

That means:

- scene mapping produces scene descriptors
- the slide planner chooses a layout archetype and named boxes
- the renderer dispatches from that planned archetype
- previews should use the same path so QA is testing the real production method

Operational expectation:

- if a preview looks wrong, fix the planner contract or the scene factory, not just one exported file
- if a scene needs a manual override, document the reason and keep the override explicit
- if a planned box is never used by the renderer, that is a pipeline bug, not a cosmetic issue

---

## Scene Board To Style Frames

Scene boards are the source of truth for shot intent.

For each scene board:

1. identify the 3 to 5 highest-value beats
2. create one style frame for each key beat
3. keep the frame aligned with `21_storybook_visual_style_guide.md`
4. verify the frame is readable at thumbnail scale

Style frame rules:

- one focal subject per frame
- one dominant visual idea per frame
- the key named object or action must be visible, not only implied
- warm board-book palette
- captions safe in the lower third
- scientific labels only where they help comprehension
- if a card or shape is introduced, its color should belong to the scene palette rather than clash with it

Style frames should answer:

- what does the episode look like
- what is the exact visual tone
- what is the best composition for this beat

If a style frame is not immediately understandable, it is not ready.

---

## Style Frames To Animatic

The animatic is where the production team checks:

- pacing
- scene order
- motion readability
- narration-to-visual alignment
- transition quality

For each style frame:

1. assign a duration based on the scene type
2. decide which elements animate in, hold, and exit
3. check whether the narration has enough time to breathe
4. verify that the focal object remains visible while motion occurs

Animatic review should answer:

- can a child understand the beat in a single pass
- is the visual motion helping or distracting
- does the scene change at the right moment in the narration

---

## Reusable Template Scenes

Reusable template scenes are the durable production assets.

They should come from the template kit in [Scene Template Kit](../reference/scene-template-kit.md) and should be aligned to these core patterns:

- `CHARACTER_INTRO`
- `HISTORICAL_SETTING`
- `OBJECT_DEMO`
- `EQUATION_REVEAL`
- `DERIVATION_STEP`
- `DIAGRAM_EXPLAIN`
- `COMPARISON_SPLIT`
- `TIMELINE_SEQUENCE`
- `MOTION_SCENE`
- `OUTRO_BRIDGE`

Future sessions should reuse these templates instead of rebuilding new layouts for every episode.

Template rules:

- preserve the frame-zone logic
- preserve the motion grammar
- keep the lower-third subtitle reserve clear
- use the same typography and palette system across episodes
- keep text short enough to read comfortably, or reveal it in stages within the same card
- do not use placeholder shapes or cards whose colors fight the background palette
- prefer plain text over colored cards for names, dates, places, and routine supporting copy
- do not leave oversized text regions that visually imply a box even after the card background is removed
- if the asset is a pendulum, spring, orbit, or similar mechanism, animate the mechanism instead of presenting it as a static diagram unless the beat explicitly calls for a still frame

---

## Duration Heuristics

The duration of each scene should be driven by cognitive load, not by arbitrary even splits.

Suggested heuristics:

- `character_intro`: `3-5s`
- `historical_setting`: `3-5s`
- `object_demo`: `4-7s`
- `equation_reveal`: `4-6s`
- `derivation_step`: `6-12s`
- `diagram_explain`: `4-8s`
- `comparison_split`: `4-7s`
- `timeline_sequence`: `4-8s`
- `motion_scene`: `5-10s`
- `outro_bridge`: `3-5s`

General rules:

- if a scene contains a new equation, give it more time
- if a scene contains more than one new concept, split it
- if the motion cannot be understood in one pass, slow it down
- if the narration is dense, do not compress the scene to match

The right scene is usually shorter than the first instinct suggests, but not so short that the viewer cannot parse it.

---

## Motion Principles

The motion system should feel precise, tactile, and readable.

Use motion to clarify, not to decorate.

Preferred motion verbs:

- `pop-in`
- `slide`
- `fade`
- `draw-on`
- `pulse`
- `highlight`
- `rotate`
- `tilt`
- `move along path`
- `split/reveal`

Avoid:

- constant idle motion on every object
- heavy camera movement
- motion that obscures the math
- motion that changes the meaning of the scene

The production standard is closer to a premium children’s science book with motion than to a generic effects reel.

---

## Session Logging And Handoffs

Future sessions should not reconstruct project state from long chat history.

Use these files as the operational memory:

- `docs/operations/23_session_handoff_log.md`
- `docs/operations/26_active_issue_and_change_log.md`
- `docs/operations/27_claude_takeover_brief.md`

Rules:

- update the handoff log when the production path changes
- update the issue/change log when a problem is found, fixed, or left open
- keep the Claude takeover brief short enough that another session can read it in one minute
- if a task is mid-flight, record what was edited, what was verified, and what still needs to be rerun
- prefer short operational notes over long retrospective prose
- treat journal updates as a standard session practice, not an optional cleanup step at the end

---

## Review Gates

Every episode should pass these gates before render:

### Gate 1: Board Review

- scene beats are complete
- every beat has a clear purpose
- required assets are known
- the scene order is sensible

### Gate 2: Style Frame Review

- palette matches the storybook style
- typography is readable
- the frame is legible at thumbnail size
- captions will not collide with key content
- text cards and shape accents match the scene palette
- equations are rendered as proper math, not flattened plain text

### Gate 3: Animatic Review

- timing matches narration
- transitions feel clean
- motion supports understanding
- the episode has a clear opening, middle, and close
- the scene still reads correctly when the narration is muted
- preview renders make it obvious whether audio is included or intentionally absent

## Preview Review For Rolling Text

When a preview uses rolling text:

- the text box should stay fixed in place
- the roll should feel smooth, not like abrupt line replacement
- clause-based rolling is allowed even when the box is not technically overflowing
- the viewer should still be able to scan the text without chasing it around the frame
- if rolling makes the scene feel busy, shorten the copy or split the beat

### Gate 4: Production Review

- scientific claims are correct
- visual shortcuts do not change meaning
- reusable templates are used where possible
- final render assets are organized and named consistently
- important objects are not hidden, floating, or visually transparent in a way that breaks realism

If any gate fails, do not move forward just because the render pipeline is available.

---

## Commands Future Sessions Should Run

### Scene Pipeline Smoke Test

Use this to confirm script parsing and scene mapping still work:

```bash
cd /Users/billy/Desktop/projects/science_education
python -m src.test_pipeline
```

### Animation System Smoke Test

Use this to confirm the scene timeline renderer and ffmpeg export still work:

```bash
cd /Users/billy/Desktop/projects/science_education
python -m src.test_animation
```

### Planner-Backed Preview Rendering

Use this to preview real script scenes through the mapper, slide planner, and renderer path:

```bash
cd /Users/billy/Desktop/projects/science_education
python -m src.pipeline.preview_render --episode ep01 --scene 1 --duration 5
```

### Template Preview Pack

Use this to regenerate the broad QA pack in `output/previews`:

```bash
cd /Users/billy/Desktop/projects/science_education
python -m src.render_template_previews
```

### Full Episode Rendering

Use this to render actual videos through the active production renderer:

```bash
cd /Users/billy/Desktop/projects/science_education
python -m src.produce_all
```

### Manual Scene Timeline Checks

For direct animation prototyping, future sessions can instantiate scene factories from `src.animation.scene_types` and inspect the generated `SceneTimeline` before exporting.

---

## File Organization Rules

When animation assets are created, future sessions should keep them grouped by function:

- style frames
- animatic exports
- reusable template previews
- final episode renders

Do not mix review artifacts with final delivery assets.

---

## Operating Standard

The team should aim for the same qualities throughout the pipeline:

- clarity first
- science second only in the sense of precision, not lower priority
- warm and premium visual language
- reusable templates instead of custom one-offs
- enough motion to feel alive, not enough to become noisy

If a scene would be understandable without narration, it is probably strong.
If it only works because the narrator explains everything, it probably needs another pass.
