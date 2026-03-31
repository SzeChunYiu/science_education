# Slide Layout Inventory

This is the practical inventory for the automatic slide planner. Each entry is a planner archetype, when to use it, and the core boxes the layout expects.

## Planner Contract

The planner contract is:

- choose one archetype per scene
- emit named boxes for that archetype
- let the renderer animate those boxes instead of inventing a new local layout
- keep the same box semantics across previews and real episode renders
- treat the named boxes as content regions, not invitations to draw decorative cards behind routine text
- size boxes to the intended copy and visual balance of the scene, not as oversized placeholders

If a scene cannot be expressed with one of these archetypes, add a new archetype deliberately instead of patching around it with one-off coordinates.

## Inventory

| Archetype | When to use it | Core boxes |
|---|---|---|
| `equation_focus` | Use when one equation is the main teaching beat and the slide needs to land the formula cleanly with a short supporting note. Best for equation reveals, definitions, and compact math explanations. | `equation`, `caption` |
| `derivation_build` | Use when the scene is a stepwise derivation or proof. The goal is to show the previous step, the current algebra step, and a short note about what changed. | `previous`, `derivation`, `annotation` |
| `profile_quote` | Use when introducing a person or centering a historical figure with a short quote or explanation. Best for scientist introductions and speaker-style slides. | `character`, `name`, `year`, `quote` |
| `historical_profile` | Use when a historical figure, time marker, and place marker need to sit together in one scene. Best for period-setting beats and historical transitions. | `character`, `metadata`, `caption` |
| `dual_dialogue` | Use when two characters need equal visual weight and each one needs a speech region and attached name. Best for debates, contrasting historical viewpoints, and call-and-response explanations. | `left_character`, `right_character`, `left_speech`, `right_speech`, `left_name`, `right_name` |
| `split_comparison` | Use when two cases must be compared side by side. Best for old vs new, left vs right, theory vs theory, or any disciplined two-panel contrast. | `left_panel`, `right_panel`, `left_title`, `right_title`, `left_asset`, `right_asset`, `left_caption`, `right_caption`, `vs`, `bridge` |
| `title_visual_caption` | Use when the slide needs a headline, one main visual, and a short caption. This is the default explainer layout for diagrams and general visual teaching beats. | `headline`, `diagram`, `caption` |
| `motion_annotated_visual` | Use when the main visual is moving or changing over time and needs light annotation. Best for motion scenes, animated diagrams, and process reveals. | `headline`, `diagram`, `caption`, `accent` |
| `object_focus_callout` | Use when one object is the clear hero but still needs a short explanation line and one small callout. Best for object demos, props, and recurring physics objects. | `title`, `object`, `explanation`, `callout`, `accent` |
| `hook_title_visual` | Use for hook slides and opening beats where a strong title, a compact subtitle, and one hero visual need to work together. Best for episode openers and takeaway slides. | `title`, `subtitle`, `hero`, `badge` |
| `timeline_milestones` | Use when a sequence needs a clear intro, one timeline bar, and an evenly distributed milestone region. Best for historical sequences and conceptual progressions. | `intro`, `timeline`, `stages_region` |
| `equation_warning` | Use when a formula must be shown together with a warning or failure condition. Best for limits, breakdowns, and “classical intuition fails here” beats. | `warning`, `equation`, `limit` |
| `worked_example_stack` | Use when a solved example needs a vertical sequence: setup, equation, substitution, result. | `setup`, `equation`, `substitution`, `result` |
| `outro_takeaway` | Use for closing slides with one main takeaway, one next-step line, and one hero figure. | `label`, `takeaway`, `next`, `hero` |

## Usage Notes

- Keep the box count small. If a scene needs more boxes than the archetype provides, it should probably be split into two scenes.
- Treat the named boxes as the planner contract. Downstream renderers should place content into these slots instead of inventing local variants.
- Prefer the closest matching archetype rather than forcing a scene into a more complex layout.
- If a box repeatedly looks empty or oversized for its content, the planner rect is wrong even if the text technically fits.
- If the focal object naturally moves, the renderer should attach a meaningful default motion profile instead of holding the object as a still.

## Archetype Selection Rules

- Use `equation_focus` when one formula is the main teaching beat and the support text is short.
- Use `derivation_build` when the viewer needs to see a previous step, a current step, and one annotation.
- Use `profile_quote` when a person is the hero and the explanation belongs next to that person.
- Use `historical_profile` when the person is the hero but date and place are part of the teaching beat.
- Use `dual_dialogue` when two speakers must each keep a stable side of the slide and distinct speech turns.
- Use `split_comparison` when left/right alignment matters more than narrative flow.
- Use `title_visual_caption` when one object or diagram is the hero and text is secondary.
- Use `motion_annotated_visual` when the scene needs a main visual plus a motion overlay, trail, airflow, or directional annotation.
- Use `object_focus_callout` when the object is the hero but one secondary callout still matters.
- If the object itself has a natural motion, prefer a motion-capable treatment over a static placement and let the object animate in a physically sensible way.
- Use `hook_title_visual` for title-card and opener scenes where the hook text, hero visual, and small badge must read together.
- Use `timeline_milestones` when the scene is fundamentally about ordered stages rather than one single focal object.
- Use `equation_warning` when the equation needs a warning band or breakdown condition.
- Use `worked_example_stack` when the viewer needs to follow a solved problem top to bottom.
- Use `outro_takeaway` when the scene is a close or bridge rather than an opener.

## Local Layout Inventory Status

- Active: `equation_focus`, `derivation_build`, `profile_quote`, `historical_profile`, `dual_dialogue`, `split_comparison`, `title_visual_caption`, `motion_annotated_visual`, `object_focus_callout`, `hook_title_visual`, `timeline_milestones`, `equation_warning`, `worked_example_stack`, `outro_takeaway`
- The preview pack now runs through the planner-backed renderer instead of keeping a separate direct-factory route for those scene families.
- Retired as the main method: ad hoc manual placement for the same core scene families.
