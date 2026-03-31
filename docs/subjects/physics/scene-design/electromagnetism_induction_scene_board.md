# Electromagnetism Pilot Scene Board

Chosen script:

- `/Users/billy/Desktop/projects/science_education/output/physics/02_electromagnetism/03_maxwells_equations/ep1_faraday_induction/scripts/ep1_youtube_long.md`

Reference style:

- `../operations/21_storybook_visual_style_guide.md`
- `../operations/19_scene_and_layout_workflow.md`
- `../operations/20_evidence_based_video_design_principles.md`

This board turns the Faraday induction episode into a reusable scene plan for future electromagnetism episodes.

---

## Production Intent

This episode should feel like:

- a warm historical discovery story
- a tactile board-book science lesson
- a precise explanation of induction and Lenz's law

The visual system should stay simple enough for children, but accurate enough that the scene language can later support Maxwell's equations and electrodynamics.

---

## Scene Board

### Scene 01

- Scene number: `01`
- Narration beat: Hook. Faraday in 1831, outsider background, one experiment changes the world.
- Scene type: `character_intro`
- Layout notes: Center Faraday slightly left; title ribbon top center; small science icons around the frame like stickers; reserve lower third for subtitle-safe space.
- Assets: `char_faraday`, `bg_royal_institution_basement`, `obj_coil`, `obj_galvanometer`, `obj_bottle_wash_bench`
- Motion: Gentle title pop-in, character settles with a soft bounce, tiny glow around the coil to imply discovery.
- Accuracy notes: Keep the setup historically grounded as a basement laboratory. Do not show modern generator parts yet.

### Scene 02

- Scene number: `02`
- Narration beat: Faraday's upbringing and apprenticeship. Bookbinder, reading self-taught, lecture notes, Davy hires him.
- Scene type: `historical_setting`
- Layout notes: Use a split storybook spread with left panel for childhood/bookbinding and right panel for the Royal Institution leap; keep text blocks short and airy.
- Assets: `char_faraday_young`, `obj_books`, `obj_bookbinding_tools`, `char_davy`, `bg_bookbinder_shop`, `bg_royal_institution_lab`
- Motion: Slide transition from book pages to lab instruments; hand-drawn paper strip revealing the job progression.
- Accuracy notes: Show apprenticeship and self-education without implying formal schooling or university attendance.

### Scene 03

- Scene number: `03`
- Narration beat: Oersted, Ampere, and Wollaston set the stage for the first motor.
- Scene type: `character_multi`
- Layout notes: Three-figure timeline across the main zone, each on a colored card with a short label; use arrows to show influence.
- Assets: `char_oersted`, `char_ampere`, `char_wollaston`, small compass icon, current-carrying wire icon
- Motion: Left-to-right reveal of the timeline cards, then a tiny compass needle wiggle.
- Accuracy notes: Keep this as context only. Do not overstate that Wollaston built a successful motor.

### Scene 04

- Scene number: `04`
- Narration beat: Faraday's 1821 wire-and-mercury motor. The first continuous rotation.
- Scene type: `motion_animation`
- Layout notes: Central circular diagram with magnet at bottom, wire above, mercury pool below. Use a clean, uncluttered background so the rotation reads instantly.
- Assets: `obj_wire`, `obj_mercury_pool`, `obj_magnet_horseshoe`, `obj_current_battery`, `obj_rotation_arrow`
- Motion: Wire begins to rotate around the magnet in a smooth loop; a small current icon pulses once.
- Accuracy notes: Mercury is historically correct, but it is hazardous. If this scene is later adapted for a modern video, include a safety note or replace the visual with a stylized non-toxic equivalent while preserving the physics.

### Scene 05

- Scene number: `05`
- Narration beat: The induction question. If electricity makes magnetism, can magnetism make electricity?
- Scene type: `comparison_split`
- Layout notes: Split screen. Left: current creating a magnetic field. Right: magnet near a wire producing nothing. Use simple arrows and a question mark in the center.
- Assets: `obj_wire`, `obj_magnet`, `obj_field_lines`, `obj_question_mark`, `obj_galvanometer`
- Motion: Left side field lines pulse outward; right side remains still, emphasizing the failed naive attempt.
- Accuracy notes: Important distinction that a static magnet near a wire does not itself create current. The change matters, not mere proximity.

### Scene 06

- Scene number: `06`
- Narration beat: The 1831 ring experiment. Closing and opening the switch gives needle kicks; steady current gives nothing.
- Scene type: `physics_diagram`
- Layout notes: Use the ring as the central object, with primary coil on one side and secondary coil on the other. Put the galvanometer on the right in clear view.
- Assets: `obj_iron_ring`, `obj_primary_coil`, `obj_secondary_coil`, `obj_switch`, `obj_battery`, `obj_galvanometer`
- Motion: Switch closes, needle jumps, then returns to zero; switch opens, needle jumps opposite direction. Use a second mini-state for the steady-current case with no needle movement.
- Accuracy notes: This is the core discovery. Make the contrast between changing current and steady current explicit.

### Scene 07

- Scene number: `07`
- Narration beat: The changed field, not the field itself, is what induces current.
- Scene type: `diagram_field`
- Layout notes: Fill the frame with field lines threading the coil. Add a before/after state showing changing flux through the loop.
- Assets: `obj_coil_loop`, `obj_field_lines_through_loop`, `obj_before_after_cards`, `obj_flux_arrow`
- Motion: Field lines grow or shrink through the loop between frames; use a subtle wipe to show temporal change.
- Accuracy notes: Do not suggest magnetic field strength alone is enough. The scene must show time variation as the cause.

### Scene 08

- Scene number: `08`
- Narration beat: Faraday's lines of force and the real field concept.
- Scene type: `historical_setting`
- Layout notes: Storybook spread with iron filings around a bar magnet; Faraday as the observer. Use a soft paper texture and sticker-like filings.
- Assets: `char_faraday`, `obj_bar_magnet`, `obj_iron_filings_pattern`, `obj_paper_sheet`, `obj_lines_of_force`
- Motion: Iron filings animate into curved lines, then hold steady as a clean field map.
- Accuracy notes: The film should suggest that Faraday treated lines of force as physically meaningful, not just a drawing trick.

### Scene 09

- Scene number: `09`
- Narration beat: Self-induction and Lenz's law. The coil resists change; magnet in a copper tube falls slowly.
- Scene type: `motion_animation`
- Layout notes: Two stacked mini-scenes work well. Top: coil kickback spark. Bottom: magnet descending through tube with braking currents.
- Assets: `obj_coil`, `obj_spark`, `obj_copper_tube`, `obj_magnet`, `obj_induced_current_loops`
- Motion: Top scene shows a short spark on switch-off. Bottom scene shows magnet slowing as current loops appear around the tube.
- Accuracy notes: Keep the direction of opposition explicit. The induced current must oppose the change, not reinforce it.

### Scene 10

- Scene number: `10`
- Narration beat: Conservation of energy explanation. If the minus sign were removed, free energy would appear.
- Scene type: `comparison_split`
- Layout notes: Left: correct world with braking and energy transfer. Right: impossible world with runaway feedback and warning symbol.
- Assets: `obj_energy_arrow`, `obj_warning_icon`, `obj_magnet`, `obj_coil`, `obj_free_energy_loop`
- Motion: Left side arrow moves from mechanical motion into electrical output; right side loop accelerates visually and then freezes on a red X.
- Accuracy notes: This is a conceptual safety scene. Frame it as a logic check, not as an actual proposed device.

### Scene 11

- Scene number: `11`
- Narration beat: Faraday's legacy and the bridge to Maxwell.
- Scene type: `character_portrait`
- Layout notes: Faraday portrait with a calm, respectful setting; a small bridge line or handoff card leading toward a Maxwell portrait in the next episode.
- Assets: `char_faraday`, `obj_notebook`, `obj_field_lines`, `obj_next_episode_card`
- Motion: Gentle page-turn effect into the next episode card.
- Accuracy notes: The transition should say "Faraday could not write the equations yet" without diminishing the experimental depth of his work.

### Scene 12

- Scene number: `12`
- Narration beat: Outro. Maxwell picks up the field idea and turns it into equations.
- Scene type: `outro_bridge`
- Layout notes: Keep the title card and next-episode teaser in the upper half; leave generous caption reserve below.
- Assets: `char_maxwell_silhouette`, `obj_equation_card`, `obj_field_lines`, `obj_next_arrow`
- Motion: Equation card slides in from the side, then the next-episode arrow glows once.
- Accuracy notes: Do not preview full Maxwell equations here. This is a bridge, not the next lesson.

---

## Scene System Notes

Core reusable template mapping for this episode:

- `character_intro` for Faraday's hook
- `historical_setting` for biography and field-lab context
- `character_multi` for Oersted/Ampere/Wollaston setup
- `motion_animation` for motor rotation and Lenz braking
- `physics_diagram` for the ring experiment
- `diagram_field` for field lines and flux change
- `comparison_split` for the induction question and the energy argument
- `character_portrait` and `outro_bridge` for the Maxwell handoff

---

## Layout Standard For Future Episodes

This pilot establishes a reusable pattern for electromagnetism episodes:

- one historical hook scene
- one context scene
- one experiment scene
- one field-meaning scene
- one law/derivation scene
- one legacy bridge scene

That structure should transfer well to:

- Faraday's law
- Maxwell's displacement current
- electromagnetic waves
- special relativity from electrodynamics

---

## Reuse Checklist

Before rendering, future sessions should confirm:

- the Faraday character asset is approved in the board-book style
- the ring experiment diagram reads clearly at thumbnail size
- the flux change is shown visually, not only narrated
- the Lenz opposition is unambiguous
- the Maxwell teaser does not jump ahead too far

