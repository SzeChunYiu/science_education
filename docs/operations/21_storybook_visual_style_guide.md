# 21. Storybook Visual Style Guide

This document defines the visual direction for the video system after script generation.

It translates the preferred look shown by the `My First Heroes: Inventors` references into a repeatable production style for this project.

Use this guide together with:

- `18_asset_generation_workflow.md`
- `19_scene_and_layout_workflow.md`
- `20_evidence_based_video_design_principles.md`
- `../subjects/physics/asset-inventory.md`

---

## Goal

We want the videos to feel:

- warm
- playful
- memorable
- premium
- readable for children
- trustworthy for adults

This means the style should be:

- board-book inspired
- retro-modern
- flat and shape-driven
- strongly color-coded
- simple at first glance
- still precise when the science matters

Important:

- use the book references as style inspiration, not as material to copy directly
- do not reproduce specific page compositions, exact lettering, or proprietary decorative elements one-for-one

---

## Reference Basis

External references used for this guide:

- Pan Macmillan product page for `Inventors`, which describes the book as using `bright, bold illustration` by Nila Aye:
  - `https://www.panmacmillan.com/authors/nila-aye/inventors/9781529046861`
- Nila Aye portfolio:
  - `https://www.nilaaye.co.uk/childrens-portfolio`
- IdN creator profile noting Nila Aye's attraction to `50s and 60s design` and the child-like wonder in the work:
  - `https://www.idnworld.com/creators/NilaAye`

The font identification below is an inference from the reference images, not a confirmed font match from the publisher.

---

## Visual North Star

The target look is:

- rounded chibi-like historical characters
- thick but friendly outlines
- flat fills with only light texture
- large simple shapes
- soft paper or printed-board-book feeling
- cheerful retro palette
- hand-made lettering energy
- decorative scientific props placed like stickers around the page
- a bold cover-language for openers and chapter cards

The emotional effect should be:

- curious rather than childish
- charming rather than silly
- educational rather than sterile

Additional observations from the wider `My First Heroes` family covers:

- cool teal and dusty blue backgrounds are common, not only warm yellow pages
- the title often sits in a white plaque under a striped or checker-trim arch
- a colored left-edge spine strip gives the frame strong editorial structure
- small circular icon stickers float around the main cast near the border
- characters use rosy cheeks, tiny eyes, simple noses, and low-detail hands
- the covers balance a large clean field with only a handful of prop badges

---

## Typography

### Font Style Analysis

The reference book appears to use two related lettering modes:

- a playful hand-lettered display style for headings and labels
- a schoolbook-style handwritten print for body copy and callouts

The large `INVENTORS` wordmark looks like a rounded geometric all-caps display sans that has been intentionally roughened or hand-drawn.

The interior page text looks like neat monoline handwritten print with:

- rounded terminals
- open counters
- slightly irregular baseline rhythm
- child-friendly legibility

Best working assumption:

- the book likely uses custom lettering or heavily stylized display fonts rather than a single obvious off-the-shelf font

### Production Font Stack

Use a controlled two-font system.

Recommended primary options:

- title/display font:
  - `Baloo 2`
  - fallback: `DynaPuff`
- handwritten/body/callout font:
  - `Patrick Hand`
  - fallback: `Schoolbell`

If a more obviously hand-drawn title is needed for small labels:

- `Short Stack`

Rules:

- do not use more than two font families in one episode
- use all-caps only for short emphasis labels, not full paragraphs
- keep body copy in sentence case
- slightly loosen tracking on large titles
- avoid narrow, technical, corporate, or futuristic fonts
- avoid perfect geometric cleanliness; a small amount of wobble is good

---

## Color System

The reference pages use a warm pastel base with brighter accent shapes and dark ink-like text.

### Core Palette

Use this as the default palette token set:

- `butter_yellow` `#F6E78B`
- `warm_cream` `#FFF7E7`
- `soft_teal` `#63C6C5`
- `sky_blue` `#A9D8F2`
- `leaf_green` `#B8D97A`
- `peach_orange` `#F3B06E`
- `coral` `#F28D79`
- `rose_pink` `#E8A2B9`
- `lavender` `#B9AEDC`
- `ink_brown` `#342A25`
- `paper_tan` `#DCC79D`
- `cover_aqua` `#9FD3D9`
- `cover_blue` `#6CB7D6`
- `spine_red` `#D84B57`
- `checker_olive` `#6C8B63`
- `sticker_gold` `#F2CF63`

### Color Roles

- backgrounds:
  - butter yellow
  - warm cream
  - paper tan
  - cover aqua
  - cover blue
- ribbons, labels, and chapter tabs:
  - coral
  - peach orange
  - soft teal
  - spine red
- science object accents:
  - sky blue
  - leaf green
  - lavender
  - sticker gold
- text and outlines:
  - ink brown

Rules:

- every scene should have one dominant background color and no more than two accent families
- avoid neon tones
- avoid dark-mode scenes except where absolutely necessary for space or chalkboard sequences
- use black sparingly; prefer ink brown for most outlines and text

Recommended split:

- cover/opening scenes:
  - cover aqua or cover blue base
  - spine red framing accent
  - sticker gold icon circles
- interior explanation scenes:
  - warm cream, butter yellow, paper tan
  - softer teal, coral, lavender accents

---

## Illustration Rules

### Character Design

Characters should use:

- oversized head-to-body ratio
- simplified hands
- tiny dot or bead eyes
- small mouth shapes
- light blush or cheek warmth where appropriate
- historically recognizable hair, clothing, and silhouette
- a clear upright pose that reads instantly at small size

Do not use:

- photoreal shading
- highly detailed anatomy
- glossy 3D render lighting
- anime proportions
- generic stock-avatar faces

### Object Design

Objects should be:

- simplified to the minimum recognizable shape
- outlined clearly
- readable at thumbnail size
- consistent in edge weight with the characters

Science props should feel like:

- movable board-book tokens
- sticker-like visual helpers

### Texture

Use only subtle texture:

- light paper grain
- faint print noise
- occasional dry-brush edge softness

Do not use:

- heavy gradients
- metallic shine
- glassmorphism
- sharp glossy reflections

Line treatment:

- outlines should feel softer than comic-book black ink
- fills should stay mostly flat with only mild dusty variation
- cheeks, hair, and props can carry a gentle paper-like texture

---

## Composition And Layout

The reference spreads use a child-friendly editorial layout rather than cinematic realism.

### Core Layout Characteristics

- one large focal character or object per scene
- supporting props around the frame edges
- big open reading zones
- rounded panels, circles, capsules, and ribbons
- playful asymmetry with clear visual balance
- page-like framing instead of deep perspective

Recurring cover motifs worth reusing:

- striped or checker-trim title plaque
- left-edge spine strip for opening cards or recurring segment frames
- circular sticker icons for supporting props
- lower-right medallion or seal for recurring brand moments
- soft stage-like ground ellipse beneath the cast

### Scene Layout Rules

For most scenes:

- keep the main figure center-left or center-right
- keep explanatory text in a clean upper or side block
- reserve lower-third space for captions in video versions
- use icon-like props to reinforce the topic without crowding the frame

Interior spread pattern observed from full-book page samples:

- left page often acts as a `bio + fact card`
- right page often acts as a `single big demonstration`

Common left-page structure:

- name ribbon at top
- portrait medallion or oval frame
- short biography paragraph
- one `wow!` or surprise bubble
- `3` colored fact blocks along the bottom

Common right-page structure:

- one dominant scene or object interaction
- a big environmental clue or title word
- far fewer text blocks than the left page
- one central experiment, tool, or visual payoff

Video adaptation rule:

- use the left-page logic for character intro / context scenes
- use the right-page logic for object demo / experiment scenes
- do not put both page logics on screen at full density at the same time

### Page Mechanics To Borrow For Video

The reference book uses interactive board-book mechanics. We should adapt those into motion language:

- slide reveal
- wheel turn
- flap open
- object pull
- pointer pop-in

These should become scene transitions and micro-animations.

Examples:

- reveal Archimedes' principle by sliding the water level marker
- reveal a field line pattern by turning a dial
- reveal orbital comparison with a flap-open timeline card

Opening/title scenes can also borrow:

- badge spin-in
- title-plaque drop-in
- icon sticker pop-in around the perimeter
- side-spine wipe reveal

---

## Motion Style

The motion system should feel tactile and printed, not sleek or high-tech.

### Preferred Motion

- slide-in panels
- gentle pop and settle
- short paper-cut parallax
- dial rotation
- pointer bounce
- sequential reveal of labels

### Avoid

- fast whip pans
- heavy particle systems
- cinematic lens flares
- exaggerated squash-and-stretch
- constant idle motion on every element

Timing guidance:

- scene entrance: `200-400 ms`
- emphasis pop: `120-220 ms`
- diagram reveal: `300-700 ms`

Inference:

- if the motion feels like a mobile game ad or a startup promo, it is wrong for this project

Opening-scene note:

- use the stronger cover-family framing for first impressions
- simplify into cleaner interior layouts once the explanation begins

---

## Scientific Accuracy Inside A Cute Style

The illustration language can be playful, but the science cannot become vague.

Rules:

- use cute characters for history, narrative framing, and intuition
- use clean programmatic overlays when precision matters
- keep equations and graphs crisp even inside soft scenes
- preserve correct relative direction, cause, and sequence in demonstrations
- when scale accuracy matters, explicitly label that a visual is not to scale

Recommended hybrid approach:

- storybook frame
- character or object in foreground
- precise scientific diagram layered on top or beside it

This keeps the emotional warmth without sacrificing correctness.

---

## Production Deliverables Before Full Video Rendering

Do not jump from assets directly to final video production.

The correct order is:

1. asset pack
2. style guide
3. scene template kit
4. style frames
5. animatic
6. final render

### Required Pre-Render Outputs

For each new topic or episode family, create:

- `visual_style_notes.md`
- `scene_plan.json` or equivalent
- `3-5` approved style frames
- a title card template
- a caption-safe layout template
- a 16:9 variant and a 9:16 variant for the core scene types

---

## First Implementation Recommendation

For physics, the first video design pass should build a reusable template family for:

- `character_intro`
- `historical_setting`
- `object_demo`
- `equation_focus`
- `diagram_explain`
- `timeline`
- `outro_bridge`

Use the palette and typography above, then test on:

- a Newton episode
- an Archimedes-style historical episode
- an electromagnetism object-demo episode

That will stress-test the style across:

- historical figures
- physics objects
- equations
- diagrams

---

## Decision Standard

When reviewing a frame, ask:

- does it look warm and distinctive at a glance
- is the focal idea obvious in under two seconds
- can captions fit without collisions
- does it still read as science, not generic kids content
- does it feel like the same brand as the reference direction

If the answer to the last question is no, revise the typography, color balance, or prop density before producing more assets.
