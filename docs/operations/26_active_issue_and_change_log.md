# 26. Active Issue And Change Log

Use this as the compact operational log for animation/video production.

It should answer three questions quickly:

1. what is still wrong
2. what was already fixed
3. what changed most recently

---

## Open Issues

### Typography And Balance

- Equation-heavy scenes still need one more normalization pass.
- The remaining weak cases are mainly `worked_example`, `limits_breakdown`, `derivation_step`, `timeline_sequence`, and some `object_demo` compositions.
- Equation size should stay visually closer to the supporting teaching text instead of dominating the slide.

### Scene Quality

- `animation_scene` is structurally better but still depends too much on simple underlying assets.
- `object_demo` can still look sparse if the hero object is too small or too isolated from the explanation.
- Some subject-aware backgrounds still fall back to neutral art because there is no stronger matching asset yet.

### Motion Coverage

- Automatic meaningful motion exists for pendulums and springs.
- Missing or weak motion profiles still include rolling objects, orbit/circular motion, waves, and some multi-part mechanisms.

### Drawing Tools

- Programmatic physics diagrams exist, but coverage is still concentrated on mechanics.
- Circuit diagrams now have a usable renderer, but the library coverage is still basic.
- Preview coverage must always be rerendered after drawing-tool edits so `output/previews/` proves the tools are working.

### Audio

- Template previews are silent by design.
- AI voice and narration checks belong to the real preview/render path, not the template pack.

---

## Fixed Recently

- Decorative colored text boxes were removed from routine layouts.
- Character labels and metadata moved toward plain text instead of card-like lower thirds.
- Subject-aware background matching was added.
- Text can roll in one region instead of dumping long copy all at once.
- Equations are no longer top-locked by design.
- Pendulum and spring objects now receive meaningful default motion.
- Slide-planner routing became the main preview QA path.
- `physics_diagrams.py` gained the missing compatibility wrappers and `spring_diagram(...)`.
- `circuit_diagrams.py` was added for programmatic circuit schematics.
- Circuit export quality was raised by switching to higher-resolution raster export settings.

---

## Current Session Changes

### 2026-03-31

- expanded the drawing-tool effort so the preview harness can test generated diagrams, not only static props
- added high-DPI circuit export settings in `src/animation/circuit_diagrams.py`
- added `circuit_battery_lamp` preview generation in `src/render_template_previews.py`
- exported drawing renderers from `src/animation/__init__.py`
- updated handoff and runbook docs so future sessions keep short operational records

---

## Next Actions

1. rerender the full preview pack after the current drawing-tool edits
2. verify the new diagram previews visually
3. do one typography-only pass for equation-heavy scenes
4. extend diagram coverage toward more canonical science visuals as needed
5. keep this file updated whenever an issue is discovered or resolved
