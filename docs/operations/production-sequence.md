# Production Sequence Guide

Step-by-step process for producing one topic from zero to published content.

---

## Prerequisites (One-Time Setup)

```bash
# 1. System dependencies
brew install ffmpeg cairo imagemagick

# 2. Python packages
conda install -c conda-forge manim -y   # or: pip install manim (needs pycairo)
pip install edge-tts pillow pysrt sympy

# 3. Verify
manim --version
edge-tts --list-voices | head
ffmpeg -version | head -1
```

---

## Production Pipeline (Per Topic)

### Step 1: Research Dossier
**Input:** Topic name, module, subject
**Tool:** Claude Code (writing)
**Output:** `output/{subject}/{topic}/dossier/research_dossier.md`

Contents:
- Core question the topic answers
- Historical timeline (who, when, what)
- Key figures and their contributions
- Earliest useful formulation
- Modern formulation
- Derivation path
- Major misconceptions
- Analogy candidates (with warranty: valid for X, breaks at Y)
- Reference list (primary, textbook, modern)

### Step 2: Episode Arc Planning
**Input:** Research dossier
**Tool:** Claude Code (writing)
**Output:** `output/{subject}/{topic}/episodes/episode_plan.md`

Choose arc template:
- **Historical-Dramatic** — for topics with rich origin stories
- **Engineering** — for techniques/algorithms
- **Structural** — for mathematical foundations
- **Instrument** — for experimental methods

Plan 5-10 episodes with: number, objective, hook type, historical position, central analogy (with warranty), key claim, references, forward hook.

### Step 3: Script Generation (Per Episode)
**Input:** Episode plan + dossier
**Tool:** Claude Code (writing)
**Output:** `output/{subject}/{topic}/scripts/`

Generate per episode:
- `ep{N}_x_post.md` — max 280 chars, citation-light
- `ep{N}_tiktok_script.md` — 60-180s narration script with emotion markers
- `ep{N}_youtube_short.md` — 30-60s, bridge CTA to long-form
- `ep{N}_youtube_long.md` — 5-12 min narrative script
- `ep{N}_article.md` — full newsletter version with references

Include in scripts:
- Hook (from 10-formula library)
- Emotion markers: `[pause]`, `[slower]`, `[with energy]`
- Viewer interaction prompts
- Forward hook to next episode

### Step 4: Manim Animation
**Input:** Script with equation/derivation tags
**Tool:** Manim CE via Claude Code
**Output:** `output/{subject}/{topic}/media/ep{N}_animation.mp4`

```bash
# Claude Code writes the Manim scene, then:
manim render -qm scene.py SceneName
# -ql = low quality (fast preview)
# -qm = medium quality (good for testing)
# -qh = high quality (final render)
```

If render fails: feed error back to Claude Code for self-correction (2 attempts usually enough).

### Step 5: AI Narration
**Input:** Script text
**Tool:** edge-tts
**Output:** `output/{subject}/{topic}/media/ep{N}_narration.mp3`

```bash
# List available voices
edge-tts --list-voices | grep en-US

# Generate narration
edge-tts --text "script text here" \
  --voice en-US-GuyNeural \
  --write-media narration.mp3 \
  --write-subtitles narration.vtt
```

Recommended voices for educational content:
- `en-US-GuyNeural` — calm, clear male (default choice)
- `en-US-AndrewMultilingualNeural` — warm, authoritative
- `en-US-BrianMultilingualNeural` — professional narrator
- `en-GB-RyanNeural` — British, intellectual feel

### Step 6: Subtitle Generation
**Input:** Narration audio or VTT from edge-tts
**Tool:** edge-tts (built-in) or Whisper
**Output:** `output/{subject}/{topic}/media/ep{N}_subtitles.srt`

edge-tts generates VTT subtitles automatically. Convert to SRT:
```python
# Or use Whisper for word-level timing:
# whisper narration.mp3 --model base --output_format srt
```

### Step 7: Thumbnail Generation
**Input:** Episode title, key equation
**Tool:** Pillow (Python)
**Output:** `output/{subject}/{topic}/media/ep{N}_thumbnail.png`

Template: dark background + large bold text (3-4 words) + equation card + brand color accent.

### Step 8: Video Assembly
**Input:** Animation + narration + subtitles
**Tool:** FFmpeg
**Output:** `output/{subject}/{topic}/media/ep{N}_{platform}.mp4`

```bash
# Combine animation video + narration audio
ffmpeg -i animation.mp4 -i narration.mp3 \
  -c:v libx264 -c:a aac -shortest combined.mp4

# Burn subtitles
ffmpeg -i combined.mp4 -vf "subtitles=subtitles.srt" \
  -c:v libx264 -c:a copy with_subs.mp4

# Platform-specific crops
# YouTube Long (16:9): already correct
# YouTube Shorts/TikTok (9:16):
ffmpeg -i with_subs.mp4 -vf "crop=ih*9/16:ih,scale=1080:1920" \
  -c:v libx264 -c:a copy vertical.mp4
```

### Step 9: Quality Review
**Human review before publish:**
- [ ] Factual accuracy (especially derivations)
- [ ] Historical claims supported by references
- [ ] Narration sounds natural, pacing good
- [ ] Subtitles sync correctly
- [ ] Video renders without artifacts
- [ ] Hook is compelling
- [ ] Forward hook to next episode works

### Step 10: Upload & Post
**Platforms:**
- YouTube (long-form): upload via browser or YouTube Data API
- YouTube Shorts: upload as vertical video <60s
- TikTok: upload via browser or TikTok API
- X: post text + optional video via tweepy or browser

**Per upload:**
- Title (front-load the hook, include concept name)
- Description (affiliate links to cited textbooks, CTA to full series)
- Tags/hashtags
- Pinned comment with engagement question
- Thumbnail (YouTube)

### Step 11: Record & Iterate
Log: upload status, post URL, platform, publish time.
After 48h: check initial metrics (views, retention, engagement).
Feed learnings into next episode production.

---

## Quick Reference: File Layout

```
output/physics/newtons-laws/
  dossier/
    research_dossier.md
  episodes/
    episode_plan.md
  scripts/
    ep01_x_post.md
    ep01_tiktok_script.md
    ep01_youtube_short.md
    ep01_youtube_long.md
    ep01_article.md
  media/
    ep01_animation.mp4
    ep01_narration.mp3
    ep01_subtitles.srt
    ep01_thumbnail.png
    ep01_youtube_long.mp4
    ep01_youtube_short.mp4
    ep01_tiktok.mp4
```
