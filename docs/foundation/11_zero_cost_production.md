# 11. Zero-Cost Production Stack

**Hard constraint:** No production costs beyond the Claude Code subscription. Everything must be free/open-source and run locally.

---

## Text-to-Speech (Free Options)

| Tool | Quality | Notes |
|------|---------|-------|
| **edge-tts** (Python) | Excellent | Microsoft Edge's TTS API, free, 300+ voices, multiple languages, SSML support |
| **Piper TTS** | Very good | Fully offline, open-source, fast, natural-sounding |
| **Coqui TTS** | Good | Open-source, supports voice cloning (train on a sample) |
| macOS `say` | Basic | Built-in, usable for prototyping only |
| **gTTS** | Decent | Google Translate TTS, free, limited control |

**Recommendation:** `edge-tts` for production quality at zero cost. Piper as offline fallback.

```bash
pip install edge-tts
edge-tts --text "Bayes didn't publish his theorem." --voice en-US-GuyNeural --write-media output.mp3
```

---

## Video & Animation (Free)

| Tool | Use Case | Notes |
|------|----------|-------|
| **Manim** (Community Edition) | Math/science animations | 3Blue1Brown's engine, Claude can write Manim scripts |
| **FFmpeg** | Video assembly, overlays, transitions | Industry standard, free, runs locally |
| **MoviePy** | Python video editing | Wraps FFmpeg, easier scripting |
| **Pillow / Cairo** | Static graphics, equation cards | Free image generation |
| **matplotlib** | Plots, diagrams | Already installed with most Python setups |

**Recommendation:** Manim for animations + FFmpeg for final assembly.

---

## Equation Rendering (Free)

| Tool | Notes |
|------|-------|
| **LaTeX → PDF → PNG** | `pdflatex` + `convert` (ImageMagick) |
| **Manim** | Renders LaTeX natively in animations |
| **MathJax (Node)** | SVG output from LaTeX strings |
| **matplotlib** | `plt.text()` with LaTeX support |

---

## Subtitles (Free)

| Tool | Notes |
|------|-------|
| **Whisper** (OpenAI, open-source) | Runs locally, generates SRT from audio |
| **edge-tts** | Can output word-level timestamps directly |
| **pysrt** | Python SRT manipulation |

---

## Thumbnails (Free)

| Tool | Notes |
|------|-------|
| **Pillow** | Template-based thumbnail generation |
| **Claude** | Generates SVG diagrams directly |
| **ImageMagick** | Text overlays, compositing |
| **Canva free tier** | If any manual touch needed |

---

## Music / Background (Free)

| Source | Notes |
|--------|-------|
| **Pixabay Music** | Free, no attribution required |
| **Free Music Archive** | CC-licensed tracks |
| **Incompetech** | Kevin MacLeod's library, CC-BY |
| No music | Many top edu-channels use narration only |

---

## Publishing APIs (Free)

| Platform | Method |
|----------|--------|
| YouTube | `google-api-python-client` (free with OAuth) |
| TikTok | TikTok Research/Content API or Selenium automation |
| X | `tweepy` with free API tier (limited but sufficient) |

---

## The Full Zero-Cost Pipeline

```
Claude Code (subscription)
    ├── Research & write scripts (Claude API included)
    ├── Generate Manim animation code → render locally
    ├── Generate LaTeX equations → render to PNG
    ├── Generate thumbnail templates → Pillow render
    ├── edge-tts narration → MP3 with timestamps
    ├── Whisper → SRT subtitles
    ├── FFmpeg → assemble video (narration + visuals + subtitles)
    ├── FFmpeg → platform-specific crops/formats
    └── Upload via free APIs
```

**Total additional cost: $0**

---

## What Claude Code Does Directly

Claude Code can:
- Write complete Manim scripts (it knows the API well)
- Write FFmpeg commands for assembly
- Generate SVG diagrams as code
- Write LaTeX for equations
- Write Python scripts that orchestrate the entire pipeline
- Call edge-tts, Whisper, and FFmpeg via bash
- Generate and run the upload scripts

The entire production pipeline is Claude Code writing and executing scripts locally.

---

## One-Time Setup

```bash
# Install all free tools
pip install manim edge-tts openai-whisper moviepy pillow pysrt
brew install ffmpeg imagemagick
# Optional
pip install tweepy google-api-python-client
```

---

## Quality Expectations at Zero Cost

| Aspect | Quality Level | Notes |
|--------|--------------|-------|
| Narration | 8/10 | edge-tts is near-studio quality |
| Math animations | 9/10 | Manim is what 3Blue1Brown uses |
| Equation cards | 9/10 | LaTeX rendering is perfect |
| Thumbnails | 6/10 | Template-based, functional but not stunning |
| Overall video | 7-8/10 | Competitive with mid-tier edu-channels |
| Music | 7/10 | Free library or narration-only |
