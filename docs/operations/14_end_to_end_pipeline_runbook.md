# 14. End-to-End Pipeline Runbook

This is the execution manual for future sessions. It describes how to take a topic from idea to published assets without needing to reconstruct the workflow from scattered planning docs.

Use this document as the default operational reference for the content factory.

Related docs:

- `../foundation/01_overview.md` for project goals
- `../foundation/07_house_style.md` for writing rules
- `../foundation/09_media_and_publishing.md` for publishing principles
- `12_youtube_connection.md` for YouTube setup
- `13_youtube_operations_runbook.md` for current YouTube machine state
- `production-sequence.md` for tool-oriented production notes

---

## Pipeline Objective

Each topic should move through the same stages:

1. topic selection
2. research dossier
3. episode architecture
4. script generation
5. scientific review
6. media production
7. packaging and metadata
8. platform publishing
9. analytics review
10. process improvement

The operating principle is:

- depth first
- accuracy non-negotiable
- short-form as discovery
- long-form as trust and authority

---

## Canonical Output Structure

Per topic, keep outputs predictable:

```text
output/{subject}/{module}/{topic}/
  dossier/
    research_dossier.md
  episodes/
    episode_plan.md
  scripts/
    ep01_youtube_long.md
    ep01_youtube_short.md
    ep01_x_post.md
  media/
    ep01_narration.mp3
    ep01_subtitles.srt
    ep01_thumbnail.png
    ep01_youtube_long.mp4
    ep01_youtube_short.mp4
```

If a topic diverges from this layout, future sessions should either normalize it or document the exception.

---

## Stage 1: Topic Intake

Input:

- subject area
- module
- topic name
- intended audience depth
- target platforms

Required decisions before starting:

- What is the core question this topic answers?
- Why does the topic matter now?
- Is the topic best taught historically, structurally, experimentally, or computationally?
- Is the immediate goal discovery content, authority content, or both?

Minimum output:

- one-line topic brief
- chosen teaching angle
- estimated episode count

---

## Stage 2: Research Dossier

Purpose:

- establish the factual base before any script is written

Required dossier sections:

- central question
- key definitions
- historical timeline
- derivation path or conceptual dependency chain
- experiments or observations that motivate the theory
- common misconceptions
- analogy candidates and where each analogy breaks
- references

Minimum evidence standard:

- at least two credible sources for non-trivial factual claims
- primary or near-primary sources for historical origin claims where practical
- textbook or equivalent authoritative source for formal derivations

Hard stop conditions:

- unsupported historical claim
- contradictory sources not reconciled
- unclear derivation path
- missing explanation of limitations or scope

---

## Stage 3: Episode Architecture

Convert the dossier into a series, not a single overloaded script.

Each episode should have:

- one learning goal
- one central tension or problem
- one hook
- one conceptual payoff
- one forward link to the next episode

Long-form episodes should not duplicate each other. If two adjacent episodes teach the same idea, split them more cleanly or merge them.

Recommended arcs:

- historical: problem -> failed attempts -> breakthrough -> impact
- conceptual: paradox -> new framework -> worked example -> limitation
- experimental: apparatus -> observation -> interpretation -> theory link
- mathematical: intuition -> formal object -> derivation -> application

---

## Stage 4: Script Generation

Generate platform-specific scripts from the approved episode plan.

Required deliverables per episode:

- `youtube_long`
- `youtube_short`
- `x_post`

Optional when needed:

- article
- newsletter
- tiktok variant
- linkedin post

Long-form requirements:

- hook in the first `15-30s`
- clear narrative spine
- real conceptual explanation, not a shallow summary
- at least one concrete example, derivation fragment, or experiment
- explicit statement of what the model/theory explains and where it does not
- source section or reference note

Short-form requirements:

- one idea only
- immediate hook in the first `1-2s`
- rapid payoff
- no extended throat-clearing
- lead naturally into the broader topic library

Social post requirements:

- native to the platform
- no forced keyword stuffing
- no generic CTA spam

---

## Stage 5: Scientific And Editorial Review

This stage is mandatory before media production for any serious release.

Review checklist:

- Are factual claims supported?
- Are historical claims clearly distinguished from modern reinterpretation?
- Are equations described accurately?
- Are analogies bounded and not misleading?
- Does the script overstate certainty?
- Does the script sound like a human explanation rather than a template?

Classification:

- `publishable`: no material factual or structural issues
- `light_edit`: solid core, but needs clarity or pacing fixes
- `rewrite`: thin, templated, unsupported, or structurally weak

Future sessions should record obvious recurring defects and update the writing prompts or review checklist accordingly.

---

## Stage 6: Media Production

The media layer turns approved scripts into assets.

Core substeps:

1. narration
2. captions/subtitles
3. visuals or animation
4. thumbnail
5. final assembly

Output expectations:

- long-form landscape video
- short-form vertical video
- thumbnail for YouTube
- clean subtitles

Quality requirements:

- no clipped audio
- no subtitle drift
- no broken renders
- no unreadable equations or labels
- no chaotic visual style

---

## Stage 7: Metadata And Packaging

Every publishable asset needs packaging, not just a raw file.

Minimum packaging set:

- title
- description
- tags or hashtags
- thumbnail
- privacy or release state
- platform-specific CTA

Packaging rules:

- titles should promise one specific payoff
- descriptions should open with value, not boilerplate
- science videos should include references or source notes where practical
- thumbnail text should be short and legible

Do not use the same copy unchanged across all platforms.

---

## Stage 8: Publishing

Default publishing order:

1. upload as `private`
2. verify metadata and render quality
3. change to `unlisted` or `public` only when ready

Current live publishing support:

- YouTube API and Studio workflow are documented in `12_youtube_connection.md`
- the current machine/channel state is documented in `13_youtube_operations_runbook.md`

For platforms without full automation, sessions should still prepare:

- final copy
- media file path
- posting checklist
- target publish window

---

## Stage 9: Analytics Review

Publishing is not the end of the pipeline.

After release, record:

- publish date and time
- platform
- asset URL
- title and thumbnail used
- first 48h metrics if available

Track by platform:

- YouTube long-form: CTR, average view duration, retention shape, subscriber conversion
- YouTube Shorts: viewed vs swiped, retention, shares, subs generated
- X: impressions, likes, reposts, replies, link clicks
- LinkedIn: impressions, comments, reposts, profile follows

Interpret metrics carefully:

- high clicks with low retention means packaging exceeded delivery
- high retention with low clicks means packaging is weak
- high engagement with low watch time may mean the topic works better as social text than as video

---

## Stage 10: Improvement Loop

Future sessions should not just execute the pipeline. They should also refine it.

When a repeated pattern appears, update one of:

- prompts
- review checklist
- title formula
- thumbnail style
- topic sequencing logic
- documentation

Preferred rule:

- fix the system, not just the instance

---

## Release States

Use explicit release states so sessions know what is safe to touch.

- `draft`: research or script still unstable
- `reviewed`: scientifically checked, awaiting packaging or media
- `rendered`: media exists, awaiting metadata review
- `private_uploaded`: uploaded for internal review only
- `scheduled`: approved and queued
- `published`: live
- `needs_revision`: regression or underperformance triggered rework

If a session changes state, it should leave enough notes for the next session to understand why.

---

## Session Handoff Standard

At the end of a substantial session, write down:

- what was completed
- what is blocked
- what files were changed
- what assumptions were made
- what the next highest-value action is

The next session should be able to resume without having to reread the entire repo.

---

## Editing This Workflow

This runbook is allowed to evolve.

Future sessions should update it when:

- a better quality gate is discovered
- a platform workflow changes
- automation replaces a manual step
- a repeated failure mode emerges

Do not quietly invent a new workflow in one session and leave the docs stale. Update the runbook when practice changes.
