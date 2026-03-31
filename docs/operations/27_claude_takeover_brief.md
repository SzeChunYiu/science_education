# 27. Claude Takeover Brief

Read this first if you are taking over the current animation/layout job.

Project rule:

- every working session should leave a short journal trail in the handoff log and issue/change log
- do not assume the next session will read the full chat history

## Goal

Keep the production renderer automatic, slide-planned, and QA-driven.

The current focus is:

- make the preview pack test all important rendering capabilities
- keep scene layout readable and PowerPoint-like
- make diagrams, equations, motion, and backgrounds production-safe

## Current Production Path

1. `scene_mapper.py`
2. `slide_planner.py`
3. `episode_renderer.py`
4. `scene_types.py` / `timeline.py`
5. preview render or full render

Use `python3 -m src.render_template_previews` for template QA.

## What Was Just Changed

- `src/animation/circuit_diagrams.py`
  - now exports higher-resolution circuit PNGs
- `src/render_template_previews.py`
  - now includes a battery-lamp circuit preview in addition to the existing generated physics diagrams and RC circuit
- `src/animation/__init__.py`
  - now exports the drawing renderers publicly

## What Still Needs To Be Done Right Now

1. run `python3 -m py_compile src/animation/circuit_diagrams.py src/render_template_previews.py src/animation/__init__.py`
2. run `python3 -m src.render_template_previews`
3. verify the new preview outputs exist and look correct
4. continue tightening equation/text size balance

## Important Rules

- treat scenes like animated slide layouts, not arbitrary video frames
- prefer plain text over decorative colored cards
- if text is long, roll it in one stable region
- if an object naturally moves, animate it meaningfully
- if the preview looks wrong, fix the pipeline or template, not the exported file by hand

## Good Files To Read Next

- `docs/operations/23_session_handoff_log.md`
- `docs/operations/26_active_issue_and_change_log.md`
- `docs/reference/powerpoint_layout_rules.md`
- `src/render_template_previews.py`
- `src/animation/physics_diagrams.py`
- `src/animation/circuit_diagrams.py`
