# 20. Evidence-Based Video Design Principles

This document translates research and official accessibility guidance into practical rules for designing scenes and layouts for this project.

This is the bridge between:

- abstract script quality
- concrete scene/layout decisions

Related docs:

- `19_scene_and_layout_workflow.md`
- `18_asset_generation_workflow.md`
- `14_end_to_end_pipeline_runbook.md`
- `../foundation/07_house_style.md`

---

## Why This Exists

Future sessions should not design scenes by pure intuition.

There is strong research and official guidance suggesting that educational videos perform better when they:

- reduce extraneous visual load
- segment information
- signal where attention should go
- align words and visuals in time and space
- respect caption/safe-area constraints
- maintain a more personal and visually active presentation style

This document turns those findings into project rules.

---

## Source Base

Primary and high-trust sources used here:

- Richard Mayer / multimedia learning summaries via Columbia CTL and Harvard HILT material
- Guo, Kim, Rubin (2014), large-scale study of MOOC video engagement
- Ou, Joyner, Goel (2019), seven-principle model for video lessons
- Section 508 caption guidance for caption-safe composition

Key sources:

- Columbia CTL: `https://ctl.columbia.edu/resources-and-technology/teaching-with-technology/diy-video/effective-videos/`
- Harvard VPAL / HILT Mayer page: `https://www.vpal.harvard.edu/research-based-principles-multimedia-learning`
- Guo et al. PDF: `https://juhokim.com/files/LAS2014-Engagement.pdf`
- Ou et al. PDF: `https://files.eric.ed.gov/fulltext/EJ1218394.pdf`
- Section 508 captions: `https://www.section508.gov/create/captions-transcripts/`

Where a recommendation below is an inference from those sources rather than a direct statement, it is labeled as such.

---

## Core Design Rules

### 1. Segment Aggressively

Research basis:

- Columbia CTL recommends multiple short, single-concept videos and cites Guo et al.
- Guo et al. found shorter videos are substantially more engaging, and recommended segmenting into chunks shorter than `6` minutes.

Project rule:

- long-form episodes should still be internally segmented into short conceptual beats
- each scene should usually serve one sub-idea only
- if a scene tries to explain too many new things at once, split it

Inference:

- even within a 10-minute video, the design should behave like a sequence of micro-lessons

---

### 2. Reduce Extraneous Processing

Research basis:

- Columbia CTL summarizes Mayer's coherence principle: remove unrelated words, pictures, and sounds
- cognitive overload harms learning

Project rule:

- do not decorate scenes just because the screen feels empty
- use only visuals that help the current explanation
- avoid excessive floating labels, ornamental particles, or constant background motion

Practical layout effect:

- fewer simultaneous elements
- cleaner whitespace
- one dominant focal object per beat

---

### 3. Signal What Matters

Research basis:

- Mayer signaling principle
- recent signaling studies in tutorial videos show signaling improves task performance/self-efficacy

Project rule:

- every equation or diagram scene should make it obvious where attention should go
- use arrows, highlights, boxed results, step emphasis, or brief spotlight motion
- do not put five equally prominent things on screen and expect the narration to do all the sorting

Practical scene effect:

- label in sequence, not all at once
- reveal derivation lines step by step
- when a concept changes, visibly highlight the changed term

---

### 4. Keep Related Words And Visuals Together

Research basis:

- Mayer spatial contiguity and temporal contiguity principles

Project rule:

- labels belong near the object or symbol they describe
- narration and visual reveal should happen at the same moment
- avoid talking about an object long before it appears, or placing labels far from the relevant target

Practical layout effect:

- local labels instead of detached legends when possible
- fewer cross-screen eye jumps

---

### 5. Prefer Visual Flow Over Static Dumping

Research basis:

- Guo et al. found Khan-style tablet/drawing formats more engaging than slide-only formats
- they also recommend introducing motion and continuous visual flow

Project rule:

- prefer progressive build-up over static finished slides
- equations should build
- diagrams should animate into meaning
- scene composition should feel guided, not dropped in all at once

Important nuance:

- motion should clarify the concept, not create spectacle for its own sake

---

### 6. Use Personal Presence Selectively

Research basis:

- Guo et al. found talking-head elements mixed with visuals can be more engaging than slides alone
- Columbia CTL recommends including instructor presence, but not necessarily all the time

Project rule:

- for this project, "presence" can be achieved through:
  - historical character scenes
  - occasional narrator/instructor-style framing
  - direct conversational narration

Inference:

- the videos do not need constant on-camera human footage, but they do need moments of human presence and narrative intimacy

Practical scene effect:

- use character-intro scenes early
- return to human or historical anchoring when a concept becomes abstract

---

### 7. Design For Captions From The Start

Official basis:

- Section 508 recommends keeping on-screen text in the top two-thirds because captions usually occupy the lower third
- it recommends readable sans serif captions, centered in the lower third, with no more than two lines at a time

Project rule:

- reserve the lower third as caption-risk space
- avoid important labels and key equations in the bottom caption zone
- keep essential scene text away from caption collision regions

Practical layout effect:

- titles and labels should prefer upper/middle zones
- bottom overlays should be used sparingly
- vertical video layouts need even stricter lower-third discipline

---

### 8. Control Speech Density

Research basis:

- Columbia CTL recommends roughly `130 words per minute`
- Section 508 warns that speech over `180 words per minute` may be too fast for captions

Project rule:

- explanation scenes should be paced for understanding, not rushed to cram content
- if a section needs extremely fast narration to fit, the scene/script is overloaded

Practical implication:

- keep dense derivations broken into multiple beats
- give viewers time to inspect equations and diagrams

---

### 9. Build Lessons, Not Just Videos

Research basis:

- Ou et al. argue video lessons should integrate instructional methods, presentation, and sequence
- their model uses activation, demonstration, application, and integration phases

Project rule:

- a good educational video should include:
  - orientation
  - explanation
  - application/example
  - integration or wrap-up

Inference:

- our scene plans should explicitly include these phases rather than just a linear lecture

---

## Scene Density Rules For This Project

These are project-level inferences from the research above.

### Default density

- most scenes: `1-2` main visual elements
- comparison scenes: `2` structured panels
- complex scenes: only if the scene type is inherently complex and signaling is strong

### Text on screen

- use less text than you think
- captions handle the spoken stream
- on-screen text should be short labels, not transcript duplication

This follows Mayer's redundancy logic and Section 508 caption constraints.

### Transition behavior

- prefer purposeful transitions tied to explanation
- avoid decorative camera moves
- each transition should either:
  - introduce a new concept
  - narrow attention
  - show a causal relationship

---

## Recommended Scene Stack For Long-Form Science Videos

This is the default structure future sessions should start from:

1. hook scene
2. human/historical anchor
3. object or intuitive demo
4. formal diagram/equation scene
5. worked example
6. meaning/limitation scene
7. bridge to next topic

Not every episode will use the exact same pattern, but this is the baseline.

---

## Recommended Layout Heuristics

### Landscape `16:9`

- one focal region plus one support region
- room for captions in lower third
- good for split comparisons and equations

### Vertical `9:16`

- one primary focal object
- much less side-by-side usage
- larger labels
- fewer concurrent elements

Inference:

- vertical versions should often be re-laid-out, not merely cropped

---

## What To Avoid

Do not:

- stack narration, labels, equations, and decorative motion all at once
- put critical text behind captions
- use static slide walls with no visual progression
- use character art when a programmatic diagram would explain better
- use visual clutter to fake depth

---

## Practical Review Checklist

Before approving a scene/layout:

- Is the focal point obvious in under a second?
- Is the scene teaching one thing at a time?
- Are text and visuals spatially aligned?
- Will captions hide anything important?
- Is the motion clarifying rather than decorative?
- Would a novice know where to look?

If not, simplify the scene.

---

## Next Project Step

Future sessions should apply this document by updating:

- `19_scene_and_layout_workflow.md`
- the scene templates in `docs/reference/`
- the actual layout/render code in `src/layout/` and `src/pipeline/`

The goal is to make the visual grammar explicit and reusable, not rediscovered episode by episode.
