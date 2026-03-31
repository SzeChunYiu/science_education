# Video Prompt Rules

This note captures the production rules worth adopting from Sabrina Ramonov's article, [5 INSANE Claude Code + Video Prompts](https://www.sabrina.dev/p/5-insane-claude-code-video-prompts), and adapts them to this science video pipeline.

We are not copying the article's exact visual style or toolchain.

We are copying the parts that improve clarity, reviewability, and production quality.

---

## Core Rule

Every scene must make sense on its own, match the described beat, and feel believable enough that the viewer does not have to excuse obvious visual mistakes.

---

## Prompt Structure

When asking an agent or tool to build a video scene, use this order:

1. research or inspect the topic if needed
2. write the scene plan first
3. define the visual metaphor for each scene
4. wait for approval when the scene structure is still uncertain
5. only then build the visuals and animation

Do not jump straight into rendering before the scene logic is clear.

---

## Scene Rules

- one beat per scene
- one clear focal object or action per scene
- if the description names an object, that object must be visibly present
- if the narration describes motion, the motion should be visible, not only implied
- the scene should still read correctly with the audio muted
- if a scene needs hand-waving to explain what is shown, it is not ready

---

## Text Rules

- no walls of text
- keep headlines short
- keep supporting text concise
- if text is too long, roll or reveal it over time inside the same area rather than dropping the whole paragraph at once
- text should be placed for video readability, not just for still-frame symmetry
- avoid decorative text treatment that makes the explanation harder to read

Current default preference:

- headline near the upper safe area
- supporting explanation in the middle or lower-middle safe area
- preserve the lower caption-risk zone

---

## Equation Rules

- equations must render as proper math, not flattened plain text
- support fractions, integrals, superscripts, subscripts, limits, and Greek symbols
- if a formula is too complex to read comfortably in one frame, split it into stages
- equation resolution must stay crisp enough for video, especially after scaling
- equation placement should leave enough breathing room around the formula

---

## Palette Rules

- added labels, shapes, and accents must fit the active scene palette
- do not introduce random saturated boxes that feel unrelated to the background
- if plain text works, prefer plain text over unnecessary colored cards
- any remaining accent color must be intentional and tied to the scene hierarchy

---

## Layout Rules

- respect safe areas for platform UI and subtitles
- do not place important content in the lower caption collision zone
- position characters so they feel grounded in the scene
- preserve realistic floor contact, scale, and opacity
- leave enough negative space that the focal subject is easy to find immediately

---

## Preview Rules

- previews are QA tools, not just exports
- previews should make it obvious whether audio is intentionally included or absent
- the preview set should cover all major template elements, not just one or two scene types
- preview review should happen clip by clip, with concrete failures called out

Minimum preview coverage should include:

- narration scene
- character scene
- object scene
- diagram scene
- equation scene
- derivation scene
- comparison scene
- historical scene
- worked example scene

---

## Review Questions

Before approving a scene, ask:

- what is the viewer supposed to notice first
- does the visible scene match the narration
- is the named object actually visible
- is the text short enough for video
- does the scene work without colored text boxes
- do the colors fit the palette already on screen
- does the equation look crisp and correct
- would this feel intentional if paused on a single frame

If the answer is no to any of these, revise before rendering at scale.
