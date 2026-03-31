# PowerPoint-Informed Layout Rules for Animated Slide Scenes

This document turns practical slide-design guidance into rules for our animated slide system.

The right mental model is not "film scene design." It is "well-designed slides with animation."

The goal is not to imitate generic PowerPoint templates. The goal is to borrow the layout habits that make strong slides easy to read, visually calm, and structurally clear on screen.

## Core findings from the research

1. Consistency matters more than decoration.
Use a stable master layout so text size, color, and position stay predictable across scenes. Good slide design relies on repeated structure, not ad hoc box placement.

2. Hierarchy must be obvious at a glance.
Titles should be the largest text. Supporting text should be smaller. One element should read as the focal point, with the rest clearly supporting it.

3. Alignment is not optional.
Elements should line up intentionally so the reading order is obvious. Random offsets and floating text boxes make layouts feel amateur and confusing.

4. Proximity should show relationships.
Labels and captions should sit close to the object they describe. Related elements should feel grouped; unrelated elements should have visible separation.

5. White space improves comprehension.
Slides are easier to read when there is breathing room around the main object and between content groups. Crowded compositions weaken focus.

6. Color should support meaning, not compete with it.
Dark text on a light background is the most reliable default. Accent color should be used sparingly to group or emphasize, not to fill large boxes behind routine text.

7. Avoid unnecessary shapes and gimmicks.
Microsoft’s own Designer guidance favors clean title/content layouts and warns that extra shapes and objects reduce layout quality. Decorative cards should not be the default.

8. Motion should guide attention, not force reading.
Animation is useful when it reveals or focuses content. It should not make the viewer chase moving text or visually noisy transitions.

9. Do not solve overflow by shrinking text into ugliness.
If copy does not fit at the intended size, split the idea, roll the text over time, or recompose the scene. Do not silently collapse the hierarchy.

## Operational rules for this repo

### 1. Build every template around a stable scene master

- Every scene type must use a repeatable layout skeleton, not one-off text placements.
- Headline, focal visual, support text, lower metadata, and equation zones should stay consistent across scenes of the same type.
- If a new scene type needs a different structure, codify it as a template, not as a local exception.

### 2. One scene, one focal point

- Each scene must have one dominant thing the viewer notices first.
- The focal point can be a character, object, equation, diagram, or timeline state.
- Text cannot compete with the focal point for visual dominance unless the scene is intentionally text-led.

### 3. Attach text to the thing it describes

- Character names go directly under the character, centered to the figure width.
- Year, place, or era labels belong in a fixed metadata position and should be plain text, not boxed.
- Captions for diagrams or objects should sit close to the visual they describe.
- Do not place detached “floating explanation cards” across unrelated parts of the frame.

### 4. Remove routine colored text boxes

- Default text rendering is plain text with sufficient contrast and spacing.
- Colored rectangles behind text are an exception, not a default.
- If a text background is absolutely necessary for legibility, it must be subtle, scene-matched, and smaller than the text group it supports.
- Never use a large colored box for a short line of text.
- This applies globally, not just to name labels. Debate names, metadata, callouts, warnings, and ordinary support copy should all default to plain text first.

### 5. Keep hierarchy stable

- Headline > focal annotation > body/support text > metadata.
- The equation should be visually close to the explanatory text in scale.
- For equation scenes, the equation should usually feel only modestly larger than the support text, not dramatically larger.
- If the explanation becomes tiny next to the math, the layout is wrong.

### 6. Preserve readable text sizes

- Do not rely on aggressive autofit-style shrinkage.
- If text needs more than a short phrase, split it across beats or roll it over time in the same text area.
- Avoid long multi-line paragraphs inside the frame.
- Text blocks should stay comfortably readable on a 16:9 video at preview size.
- If a text region is much larger than the copy inside it, reduce the region or choose a better archetype instead of leaving a loose empty box.

### Rolling Text And Overflow Policy

- Rolling text is allowed inside one stable text box when the copy is longer than the visual beat should show at once.
- Rolling is not only for overflow. If text is naturally clause-based, especially comma-separated teaching copy, it may roll across clauses even when the full text technically fits.
- The text box itself should stay anchored. The viewer should feel that content is changing within a stable slot, not that a new box is jumping around the slide.
- Prefer rolling or staged replacement over shrinking text until it looks weak.
- If the text still feels dense after rolling, split the scene.

### 7. Use white space aggressively

- Leave visible empty space around the focal object.
- Separate content groups clearly.
- If text, cards, or graphics touch too many edges of the scene, the layout is probably overbuilt.

### 8. Use color as a system

- Accent colors must belong to the current scene palette.
- If the scene background is warm and earthy, support elements must not introduce unrelated neon or cold UI colors.
- Color should group or emphasize only the most important secondary elements.
- If plain text works, prefer plain text.
- The background itself should also match the subject. Historical figures need period-appropriate settings when available, and object/diagram scenes should avoid unrelated scenic backdrops.

### 9. Prefer clean columns over wide cards

- When a character or object occupies one side, place support text in a narrower text column on the other side.
- Do not stretch a quote or explanation card across the subject area.
- Text width should be narrow enough to read in a few short lines.

### 10. Animation should reveal, not distract

- Use motion to stage attention.
- Avoid effects that require viewers to read moving words.
- Use restrained fades, reveals, or short directional moves rather than flashy transitions.

## Slide archetypes for our test scenes

These are the closest PowerPoint-style archetypes for the templates in our preview pack.

### `animation_scene` and object demo scenes

PowerPoint analogy: picture-with-caption or title-plus-visual.

- The object or phenomenon is the hero and should occupy most of the usable frame.
- The named object must be immediately visible without the viewer reading first.
- If the object naturally moves, the default should be a physically meaningful motion setup, not a static image.
- Use one short line of support text near the object, not a wide explanation card.
- If motion is important, use arrows, trails, or staged reveals as annotations, not large text.
- If the object is small and the text is large, the slide is upside down.

### `narration_with_caption`

PowerPoint analogy: image slide with a short caption.

- One visual first, one short caption second.
- Keep the caption in a repeatable lower or side position across scenes.
- The caption should summarize, not duplicate a whole spoken paragraph.
- If the narration is long, roll the text over time inside the same caption zone rather than growing a giant block.
- If the sentence has clear clause breaks, roll by clause rather than waiting for literal overflow.

### `character_scene`

PowerPoint analogy: speaker/profile slide with a quote.

- Use a clean two-column composition.
- Character on one side, support text on the other side.
- Name is attached directly to the character, centered below the figure.
- Year is smaller metadata, not merged into a bulky lower-third.
- Quote text should sit in a narrow column and should never span under or behind the character.

### `historical_moment`

PowerPoint analogy: hero image plus metadata.

- The historical visual or figure should dominate the slide.
- Year and place belong in one stable metadata slot.
- Metadata should be plain text with strong contrast, not a banner.
- Supporting narration belongs in a compact text block separated from the metadata.
- If the date/location treatment becomes the loudest thing on the slide, it is wrong.

### `equation_reveal`

PowerPoint analogy: teaching slide with staged math build.

- Only show the math needed for the current teaching beat.
- Complex formulas should build in stages, not appear as one dense wall if the explanation depends on parts.
- Keep the explanation close to the equation, either directly under it or as a nearby side note.
- The equation can be larger than the explanation, but only modestly so.
- If the equation is crisp but the explanation becomes tiny, the composition has failed.
- The equation is not locked to the top of the slide. The planner should be free to place it wherever the scene balance is best.
- Default equation placement should feel centered as a teaching unit with its explanation, not top-heavy.

### `two_element_comparison`

PowerPoint analogy: side-by-side comparison slide.

- Use a disciplined 50/50 split by default.
- Use a 60/40 split only when one side is intentionally the recommended or emphasized option.
- Titles, images, and support text should align on shared baselines.
- Wording should stay parallel across sides.
- Keep support lines short and comparable so one side does not visually outweigh the other by accident.

### `timeline_sequence`

PowerPoint analogy: process or timeline slide.

- Treat the timeline as a structured row of milestones, not a collection of floating cards.
- Keep milestone titles short, ideally about 5-7 words or less.
- Keep dates in one format.
- Align milestone markers and distribute them evenly.
- If there are too many milestones to read comfortably, split them across beats or scenes instead of shrinking everything.

### `outro_bridge`

PowerPoint analogy: title-plus-hero or takeaway-plus-next-step slide.

- The hero visual must still feel larger than the takeaway text.
- Use one clear takeaway and one clear next-step cue.
- Text groups should be compact and subordinate to the hero image.
- If the human or object looks tiny next to text, reduce the text footprint before changing anything else.

## Sizing and placement heuristics

These are practical defaults for 16:9 animated slides.

- Hero subject width: usually 24% to 40% of frame width, depending on whether the scene is single-subject or diagram-led.
- Support text column width: usually 28% to 38% of frame width.
- Gutter between subject and support column: about 6% to 10% of frame width.
- Comparison columns: about 44% to 48% each, with a clear gutter.
- Equation-to-explanation scale ratio: target roughly 1.15x to 1.35x, not 2x.
- Timeline milestone count: usually 5 to 8 per scene before readability drops.
- Metadata lines: keep them visually smaller than body text.

## Template-specific rules

## Character scene

- Character is the focal point.
- Name is centered directly below the character.
- Year is optional and smaller, also plain text.
- Quote/explanation belongs in a separate right-side text column.
- No large quote box behind the character.

## Historical moment

- Background image or character/event visual is primary.
- Year/place lives in a fixed metadata slot as plain text.
- Narration text stays in a compact support zone and should not become a banner.

## Equation reveal

- Equation and explanation must feel like one visual unit.
- Equation gets space, but not so much that the explanation becomes secondary noise.
- Long formulas should expand width first, then split/reveal in stages before shrinking text too far.
- Math rendering must stay crisp at video resolution.

## Timeline sequence

- The timeline itself is the focal graphic.
- Milestones should read as structured nodes, not as a row of unrelated floating cards.
- Date labels and milestone labels should be short and vertically aligned.

## Comparison and outro bridge

- Human, object, or primary visual must not be dwarfed by text.
- Text groups should be narrower and more disciplined than the hero element.
- If a scene reads as “big text plus tiny subject,” rebalance in favor of the subject.

## Research notes by source

The most useful scene-specific takeaways were:

- Microsoft Support emphasizes starting from strong built-in layout structures and avoiding extra objects or shapes that confuse the layout engine.
- Old Dominion University emphasizes consistent masters, readable font sizes, dark-on-light contrast, and avoiding shrink-to-fit behavior.
- University of Michigan’s checklist is especially useful for scene composition: alignment, contrast, repetition, proximity, and white space.
- University of Waterloo and Schulich both stress large fonts, simple clean templates, high-quality images, and minimal distracting animation.
- Timeline guidance repeatedly stresses even spacing, consistent date formats, short milestone labels, and splitting overloaded timelines.
- Comparison-slide guidance consistently recommends disciplined columns, parallel wording, and keeping the number of criteria limited enough to scan quickly.
- Math-presentation guidance is consistent that equations should be shown only when necessary and often introduced with staged builds rather than dumped all at once.

## Review checklist

Before accepting a preview, ask:

- What is the first thing the eye sees?
- Is the reading order obvious?
- Are related items visually grouped?
- Is there enough empty space?
- Does any text box feel decorative rather than necessary?
- Does the color treatment belong to the scene palette?
- Is the subject larger and clearer than its explanation?
- If this were a good slide, would it still feel balanced?

## How we will apply this

- We will treat these rules as the default for all preview templates.
- New scene templates should inherit these constraints instead of inventing their own card-heavy layouts.
- If a template breaks these rules, it should justify why.

## Sources

- Microsoft Support, “Quick tips: Design a presentation in PowerPoint for Windows”  
  https://support.microsoft.com/en-au/office/quick-tips-design-a-presentation-in-powerpoint-for-windows-727168d9-46cd-41be-89c2-a764858e417b

- Microsoft Support, “Create professional slide layouts with Designer”  
  https://support.microsoft.com/en-us/office/create-professional-slide-layouts-with-designer-53c77d7b-dc40-45c2-b684-81415eac0617

- Old Dominion University, “Best Practices for Creating Presentations”  
  https://www.odu.edu/online-faculty/training/presentations

- University of Michigan Sweetland Center, “How Can I Create a More Successful PowerPoint Presentation?”  
  https://lsa.umich.edu/content/dam/sweetland-assets/sweetland-documents/WritingGuides/HowCanICreateaMoreSuccessfulPowerPoint.pdf

- University of Waterloo Centre for Teaching Excellence, “PowerPoint”  
  https://uwaterloo.ca/centre-for-teaching-excellence/catalogs/tip-sheets/powerpoint

- Schulich School of Medicine & Dentistry, “How Do I Prepare PowerPoint Slides For Teaching?”  
  https://www.schulich.uwo.ca/digitallearningandsimulation/docs/1_PowerPoint_For_Teaching.pdf

- Skywork, “How to Create a Timeline in PowerPoint”  
  https://skywork.ai/blog/slide/how-to-create-timeline-in-powerpoint-guide/

- Deckary, “Comparison Slide PowerPoint: 5 Formats That Drive Decisions”  
  https://deckary.com/blog/comparison-slide-powerpoint

- University of Hawai'i, “Presentation Tips”  
  https://www2.hawaii.edu/~esb/2017fall.ics690/presentation.pdf
