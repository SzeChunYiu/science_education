# 11. Video Production & AI Media Pipeline -- Technical Review

This document is a detailed technical review of tools, architectures, and strategies for the automated video production layer described in docs 01-10. It covers AI video generation tools, Claude Code integration, pipeline architecture, quality tradeoffs, AI narrator design, and thumbnail automation.

---

## 1. AI Video Generation Tools

### 1.1 Text-to-Speech for Educational Narration

Your doc 09 specifies the voice must be "calm, intelligent, clear, story-like, not overdramatic." This is a demanding brief -- most TTS defaults sound either flat or performatively enthusiastic. Here is how the major options stack up.

#### ElevenLabs
- **Best-in-class for this project.** The Multilingual v2 and Turbo v2.5 models produce the most natural prosody available today. The voice cloning feature lets you define a stable brand voice from as little as 30 seconds of reference audio, or use their professional voice design tool to craft one from scratch.
- Handles pacing variation well -- you can use SSML-like controls or their Projects feature to adjust emphasis, pauses, and speed per sentence.
- **Cost:** Creator plan at $22/month gives 100,000 characters (~70 minutes of audio). Scale plan at $99/month gives 500,000 characters (~350 minutes). For a pipeline producing 30-50 videos/month, budget $99-$330/month.
- **API quality:** Excellent. Streaming support. Can generate sentence-level timestamps for subtitle alignment.
- **Weakness:** At very high volumes, cost escalates. Also, voice consistency across long sessions can drift slightly -- use the same voice_id and settings throughout.

#### OpenAI TTS (via API)
- The `tts-1-hd` model is good -- noticeably better than Google/Azure defaults, though a tier below ElevenLabs for naturalness.
- Six built-in voices (alloy, echo, fable, onyx, nova, shimmer). "Onyx" and "fable" are closest to a calm educational narrator.
- **No voice cloning.** You are locked to their voice library. This limits brand identity.
- **Cost:** $15 per 1M characters for tts-1-hd. Very cost-effective at scale.
- **Weakness:** No SSML support, limited pacing control, no custom voice. Good fallback, not the primary pick.

#### Google Cloud TTS (WaveNet / Neural2 / Journey)
- Journey voices (released 2024) are competitive with ElevenLabs for some use cases. Neural2 is solid but slightly robotic for storytelling.
- SSML support is excellent -- full control over pauses, rate, pitch, emphasis.
- **Cost:** WaveNet at $16 per 1M characters, Neural2 at $16, Journey at $30. Very competitive at scale.
- **Weakness:** The voices themselves, while technically capable, tend to sound "corporate narration" rather than "curious teacher telling a story." Less warmth than ElevenLabs.

#### Azure TTS (Neural / Personal Voice)
- Azure's Personal Voice feature allows voice cloning with consent verification. Good for legal compliance.
- The default neural voices are comparable to Google Neural2 -- professional but slightly stiff.
- SSML support is the most complete of any provider.
- **Cost:** $16 per 1M characters for neural. Personal Voice pricing varies.
- **Weakness:** The Azure ecosystem is heavyweight for a project like this. SDK integration is more complex than ElevenLabs or OpenAI.

#### Recommendation
**Primary: ElevenLabs.** Use their voice design or clone a voice that matches the brand. Use the Projects API for long-form, the standard API for short-form. **Fallback: OpenAI TTS** for cost-sensitive batch jobs where brand voice is less critical (e.g., draft previews).

---

### 1.2 Video Generation / Assembly Frameworks

Your videos have two very different profiles:
- **Short-form (30-90s):** hook + one idea + one visual + one takeaway. Essentially narration over motion graphics.
- **Long-form (5-12min):** full narrative with multiple scenes, equation derivations, diagrams, historical context.

#### Remotion (React-based programmatic video)
- **Strong fit for this project.** Remotion lets you define video as React components. Every frame is a function of time. You write JSX that describes what appears when, and Remotion renders it to MP4 via headless Chrome + FFmpeg.
- Perfect for templated educational content: you define a `<ShortFormVideo>` component with slots for title, narration audio, equation card, diagram, subtitle track, CTA. Then each video is just data flowing through the template.
- Supports LaTeX rendering via KaTeX or MathJax in the browser -- equations render natively.
- Remotion Lambda allows cloud rendering on AWS (renders a 60s video in ~15 seconds).
- **Cost:** Remotion requires a company license ($) for >1 person or revenue-generating use. Remotion Lambda costs are AWS-based, roughly $0.01-0.05 per render.
- **Weakness:** Requires Node.js/React expertise. Debugging visual timing issues can be tedious. Not ideal for complex 3D animations.

#### Manim (3Blue1Brown's animation engine)
- **The gold standard for math/science animation.** If you want to animate equation derivations, vector fields, graph transformations, probability distributions -- Manim is unmatched.
- Community Edition (ManimCE) is actively maintained and well-documented.
- Python-based. Each scene is a class with `construct()` method. Animations are imperative: `self.play(Write(equation))`, `self.play(Transform(old, new))`.
- **Critical for this project:** Your episode arc (doc 04) includes "one derivation step" and "meaning of a term" -- these are exactly what Manim excels at.
- **Cost:** Free and open source.
- **Weakness:** Rendering is CPU/GPU intensive. A 60-second Manim scene takes 2-10 minutes to render locally. No built-in templating system -- each scene is bespoke code. Steep learning curve for complex animations.

#### Revideo
- Fork of Remotion's concept but built on Canvas2D/WebGL instead of DOM. Faster rendering for graphics-heavy content.
- Still relatively early-stage compared to Remotion. Smaller community, fewer examples.
- **Skip for now.** Revisit if Remotion's DOM-based rendering becomes a bottleneck.

#### FFmpeg (direct pipeline)
- Not a video creation framework -- it is the universal video assembly tool. Every pipeline above ultimately calls FFmpeg.
- Use FFmpeg directly for: concatenating rendered scenes, overlaying audio tracks, adding subtitle burn-in, final encoding/compression, format conversion.
- Key commands you will use constantly:
  - `ffmpeg -i narration.mp3 -i visuals.mp4 -c:v copy -c:a aac output.mp4` (mux audio+video)
  - `ffmpeg -i input.mp4 -vf "subtitles=subs.ass" output.mp4` (burn subtitles)
  - `ffmpeg -i input.mp4 -vf "scale=1080:1920" output.mp4` (resize for vertical)
- **Cost:** Free. Runs everywhere.

#### MoviePy (Python)
- Python wrapper around FFmpeg. Good for scripting simple compositions: overlay text on images, concatenate clips, add audio.
- **Use case in this project:** Quick assembly of "equation card + narration" style videos where you do not need Remotion's full component system.
- **Weakness:** Slow for complex compositions. Limited animation capabilities. The API is showing its age.

#### Recommendation
**Primary rendering: Remotion** for templated short-form and long-form video structures. **Manim** for equation derivation and math animation scenes, rendered as clips and composed into the final video via Remotion or FFmpeg. **FFmpeg** as the universal glue for final assembly, format conversion, and platform-specific encoding.

---

### 1.3 Image / Visual Generation

#### For Diagrams and Equation Cards
- **Do NOT use AI image generators for diagrams.** Use programmatic rendering instead:
  - LaTeX → PDF → PNG via `pdflatex` + `imagemagick` or `pdf2svg` for equation cards
  - Manim for animated equations
  - Remotion with KaTeX for in-video equation rendering
  - D3.js or matplotlib/seaborn for data visualizations, rendered as static images or animated SVGs
- AI image generators produce unreliable diagram content -- they hallucinate labels, misplace arrows, and produce scientifically incorrect visualizations. For educational content where accuracy is non-negotiable, programmatic rendering is the only viable path.

#### For Thumbnails and Artistic Visuals
- **DALL-E 3 (via API):** Best for programmatic thumbnail generation. Clean, prompt-adherent outputs. $0.04-0.08 per image depending on resolution. Integrates natively with OpenAI API.
- **Midjourney:** Highest aesthetic quality, but API access is limited (still requires Discord bot or their newer web API). Better for manual batch generation of brand assets, not automated pipeline use.
- **Stable Diffusion (local or via API):** Free if run locally (SDXL/SD3). Best for high-volume generation with full control. Requires GPU. Via API (Stability AI): $0.01-0.03/image.
- **Flux (via Replicate/fal.ai):** Strong alternative to DALL-E 3. Better text rendering in images. $0.01-0.05/image via API.

#### Recommendation
**Equations/diagrams: programmatic only** (LaTeX, Manim, KaTeX, matplotlib). **Thumbnails: DALL-E 3 API** for automated generation, with Flux as backup. **Brand assets: Midjourney** for one-time design work (channel art, recurring visual motifs).

---

### 1.4 Subtitle Generation

#### Whisper (OpenAI)
- Run locally (free) or via API ($0.006/minute).
- Produces word-level timestamps. Excellent accuracy for clear English narration.
- For your pipeline: generate narration with ElevenLabs (which provides sentence timestamps), then run Whisper on the generated audio for word-level alignment. This gives you precise subtitle timing.
- **Recommended.** Use `whisper-timestamped` or `stable-ts` for enhanced word-level timing.

#### AssemblyAI
- Cloud API. $0.01/minute. Slightly better punctuation/formatting than Whisper out of the box.
- Not worth the cost premium for this use case since your narration is already clean, scripted speech.

#### Alternative approach
Since you control the script and the TTS, you can skip speech recognition entirely. ElevenLabs returns character-level timing data. Map your script text directly to audio timestamps. This is faster, cheaper, and more accurate than any STT-based approach.

#### Recommendation
**Primary: Direct timestamp mapping from ElevenLabs API response.** Fallback: Whisper locally for any audio where direct timing is unavailable.

---

### 1.5 Music / Background Audio

#### Epidemic Sound
- $15/month for creator plan. Massive library. API available for enterprise.
- Good for consistent background music across videos. Curate 5-10 tracks for your brand and reuse them.
- **License is clean** for YouTube, TikTok, and all platforms.

#### Mubert AI
- Generates AI music on demand. $14/month for creator plan.
- Can generate music per-video matched to mood/tempo.
- Quality is adequate for background but not as polished as Epidemic Sound's curated library.

#### Free alternatives
- YouTube Audio Library (free, limited selection)
- Pixabay Music (free, CC0)
- Generate ambient tracks with Suno or Udio for background textures

#### Recommendation
**Epidemic Sound** for the core library. Select 5-10 calm, intellectual background tracks and standardize. Music should be barely noticeable -- educational content benefits from subtle audio beds, not prominent music.

---

## 2. Claude Code + Video Pipeline Integration

### 2.1 Can Claude Code Generate Manim Scripts?

**Yes, and this is one of the highest-leverage capabilities for this project.**

Claude has strong knowledge of Manim's API. It can generate complete scene classes given a mathematical concept. Example workflow:

1. The Scriptwriter Agent produces a script with tagged equation segments: `[DERIVE: show that d/dx(x^2) = 2x using limit definition]`
2. Claude Code receives this tag and generates a Manim scene:

```python
from manim import *

class LimitDerivation(Scene):
    def construct(self):
        # Show the limit definition
        limit_def = MathTex(
            r"f'(x) = \lim_{h \to 0} \frac{f(x+h) - f(x)}{h}"
        )
        self.play(Write(limit_def))
        self.wait(2)

        # Substitute f(x) = x^2
        substituted = MathTex(
            r"= \lim_{h \to 0} \frac{(x+h)^2 - x^2}{h}"
        )
        self.play(TransformMatchingTex(limit_def, substituted))
        self.wait(2)

        # Expand and simplify
        expanded = MathTex(r"= \lim_{h \to 0} \frac{2xh + h^2}{h}")
        self.play(TransformMatchingTex(substituted, expanded))
        self.wait(2)

        # Final result
        result = MathTex(r"= 2x")
        self.play(TransformMatchingTex(expanded, result))
        self.play(result.animate.scale(1.5).set_color(YELLOW))
        self.wait(3)
```

3. The orchestrator runs `manim render -ql scene.py LimitDerivation` to produce a video clip.
4. This clip is composed into the final video.

**Caveats:** Claude will sometimes produce Manim code with minor API errors (wrong method names, deprecated syntax). Build a validation step that attempts to render and feeds errors back to Claude for self-correction. Two iterations is usually enough to get a clean render.

### 2.2 Can Claude Code Write Remotion Components?

**Yes.** Claude can generate Remotion compositions as React/TypeScript components. Define a base template system with standard components:

```tsx
// Template: ShortFormVideo.tsx
export const ShortFormVideo: React.FC<{
  title: string;
  narrationSrc: string;
  equationLatex: string;
  subtitles: SubtitleEntry[];
  durationInFrames: number;
}> = ({title, narrationSrc, equationLatex, subtitles, durationInFrames}) => {
  return (
    <Composition
      component={ShortFormScene}
      durationInFrames={durationInFrames}
      fps={30}
      width={1080}
      height={1920}
    />
  );
};
```

Claude Code can then generate per-video data payloads (title, equation, subtitle timing, scene descriptions) that feed into these templates. For more custom videos, Claude can write entirely new Remotion scenes.

### 2.3 Can Claude Code Call FFmpeg for Assembly?

**Yes.** Claude Code has direct shell access. It can construct and execute FFmpeg commands:

```bash
# Combine Manim clip + narration + background music
ffmpeg -i manim_scene.mp4 -i narration.mp3 -i bg_music.mp3 \
  -filter_complex "[1:a][2:a]amix=inputs=2:weights=1 0.15[aout]" \
  -map 0:v -map "[aout]" -c:v libx264 -c:a aac \
  -shortest output.mp4
```

Claude Code can also dynamically construct complex filtergraphs for multi-scene assembly, subtitle burn-in, and platform-specific reformatting.

### 2.4 Can Claude Code Generate Scene Descriptions for Image Generators?

**Yes.** This is a natural extension of the Scriptwriter Agent. From the episode plan, Claude generates structured scene descriptions:

```json
{
  "scene_id": 3,
  "type": "conceptual_illustration",
  "prompt": "A calm, minimalist illustration of a beam of white light entering a glass prism and separating into a spectrum of colors. Dark background, clean lines, educational diagram style. No text.",
  "style": "clean_educational",
  "aspect_ratio": "16:9",
  "used_for": "youtube_long_form"
}
```

These scene descriptions can be fed to DALL-E 3 or Flux APIs. The key is to establish a consistent prompt prefix/style guide so all generated images share a visual language.

---

## 3. Practical Pipeline Architecture

### 3.1 End-to-End Flow

```
SCRIPT PHASE (Claude)
  Topic selection → Research dossier → Episode planning → Script generation → QA
      |
      v
MEDIA GENERATION PHASE (mixed local/cloud)
  Script → [branch into parallel tracks]
      |
      |── Narration: script text → ElevenLabs API → .mp3 + timestamps
      |── Equations: LaTeX tags → Manim render (local) → .mp4 clips
      |── Diagrams: diagram specs → matplotlib/d3 render (local) → .png/.svg
      |── Illustrations: scene prompts → DALL-E 3 API → .png
      |── Subtitles: timestamps + script → .srt/.ass generation
      |── Music: select from pre-curated library → .mp3
      |
      v
ASSEMBLY PHASE (local)
  All assets → Remotion composition OR FFmpeg assembly → raw .mp4
      |
      v
POST-PROCESSING (local)
  Platform-specific encoding:
    - YouTube long: 1920x1080, H.264, AAC
    - YouTube Shorts: 1080x1920, H.264, AAC
    - TikTok: 1080x1920, H.264, AAC
    - X: 1280x720 or 1080x1080, H.264, AAC
      |
      v
PUBLISH PHASE (cloud APIs)
  YouTube Data API → upload + metadata
  TikTok Content Posting API → upload
  X API v2 → post with media
```

### 3.2 Local vs Cloud

| Component | Where | Why |
|-----------|-------|-----|
| Claude (all agents) | Cloud (Anthropic API) | No local alternative at this quality |
| ElevenLabs TTS | Cloud (API) | Latency ~2-5s per request, acceptable |
| DALL-E 3 | Cloud (OpenAI API) | No viable local alternative at this quality |
| Manim rendering | Local | CPU-bound, 2-10 min per scene, no cloud service |
| Remotion rendering | Local or AWS Lambda | Local for dev, Lambda for production scale |
| FFmpeg assembly | Local | Fast, no reason to cloud this |
| LaTeX rendering | Local | Instant, requires texlive installation |
| Whisper (fallback) | Local | Free, fast on Apple Silicon with whisper.cpp |
| Subtitle generation | Local | Pure text processing |
| Platform uploads | Cloud (APIs) | Required |
| PostgreSQL | Cloud (Supabase) or local | Supabase for simplicity |
| Object storage | Cloud (S3/R2/Supabase Storage) | Assets need to be accessible |

### 3.3 Cost Estimates (Monthly, 40 videos)

Assuming 40 videos/month: 20 short-form (60s avg) + 10 YouTube Shorts (45s avg) + 10 long-form (8 min avg).

| Item | Estimate |
|------|----------|
| Anthropic API (Claude Sonnet for agents) | $50-150 |
| ElevenLabs (Scale plan) | $99 |
| DALL-E 3 (thumbnails + illustrations, ~200 images) | $8-16 |
| Epidemic Sound | $15 |
| Remotion license | $0 (solo developer) or ~$50/mo |
| Supabase (free tier or Pro) | $0-25 |
| AWS S3/R2 storage | $5-10 |
| Compute (local Mac, already owned) | $0 |
| **Total** | **$177-365/month** |

This is remarkably cost-effective for a pipeline producing 40 videos/month with professional narration.

### 3.4 Equation Rendering: LaTeX to Image/Animation

Three tiers depending on context:

**Static equation cards (X posts, thumbnails):**
```bash
# LaTeX → PDF → PNG
pdflatex -interaction=nonstopmode equation.tex
convert -density 300 equation.pdf -trim +repage -background white equation.png
```

**In-video equations (Remotion):**
```tsx
import { KaTeX } from './components/KaTeX';
// KaTeX renders LaTeX in the browser, Remotion captures it as video frames
<KaTeX formula="E = mc^2" fontSize={48} color="white" />
```

**Animated derivations (Manim):**
```python
equation = MathTex(r"E = mc^2")
self.play(Write(equation))
```

Use Manim for any equation that needs to transform, highlight terms, or show step-by-step derivation. Use KaTeX in Remotion for static equation display within video. Use LaTeX+ImageMagick for standalone equation card images.

---

## 4. Quality vs Speed Tradeoffs

### What is fully automatable at high quality

| Element | Automation quality | Notes |
|---------|-------------------|-------|
| Script writing | 85-90% | Claude produces strong educational scripts. Needs periodic human review for factual nuance, not every episode. |
| Narration audio | 90-95% | ElevenLabs is nearly indistinguishable from human narration for calm educational delivery. |
| Equation rendering | 95%+ | Programmatic -- either correct or fails. No quality gradient. |
| Subtitles | 95%+ | Generated from known script + timestamps. Almost no error. |
| Short-form video assembly | 85-90% | Templated Remotion compositions look professional with good design. |
| Thumbnail generation | 70-80% | Functional but may lack the "click factor" of hand-designed thumbnails. |
| Platform uploading | 100% | Pure API calls. |

### What benefits from human involvement

| Element | Why |
|---------|-----|
| Long-form video pacing | 8-12 minute videos need careful rhythm. Automated pacing can feel monotonous. A human editor reviewing the timeline every few videos helps significantly. |
| Visual storytelling choices | Which image to show when, how to frame a diagram, when to use animation vs. static -- these creative choices benefit from human judgment. |
| Thumbnail design for key videos | For your "pillar" long-form content, manually designed thumbnails outperform AI-generated ones by 20-40% in CTR. |
| Historical accuracy review | Your Citation Auditor Agent catches most issues, but domain-expert spot checks (1 in 5 videos) add credibility assurance. |
| Brand voice calibration | Every 2-4 weeks, review a batch of outputs to ensure tone has not drifted. |

### Recommended operating mode

**Fully automated for short-form.** The risk per video is low, the templates are tight, and volume matters. Run QA agents and publish.

**Semi-automated for long-form.** Generate everything automatically, but have a human review the rendered video before publishing. This review should take 10-15 minutes per video. At 10 long-form videos/month, that is ~2-3 hours of human time.

---

## 5. AI Narrative Design

### 5.1 Voice Selection and Cloning

**Recommended approach: Design a custom voice with ElevenLabs Voice Design.**

Rather than cloning an existing person's voice (which carries legal and ethical complexity), use ElevenLabs' voice design feature to create a synthetic voice from scratch by specifying parameters: gender, age, accent, tone. This gives you:
- A voice you fully own
- No licensing or consent issues
- A consistent brand identity
- The ability to fine-tune the voice over time

If you want to clone a voice, ElevenLabs requires explicit consent from the voice owner. Options:
- License a voice from a voice actor marketplace (Voices.com, Fiverr) -- budget $200-500 for a consent-cleared recording session
- Use your own voice -- record 30 minutes of clean narration in the target style, upload to ElevenLabs Professional Voice Clone ($99+ tier)

**Legal considerations:**
- Several US states have voice likeness protection laws (California, New York, Tennessee)
- The EU AI Act requires disclosure of AI-generated content
- YouTube requires disclosure of "altered or synthetic" content in certain cases
- Your Compliance Agent (doc 06) should flag all AI voice content for appropriate disclosure

### 5.2 Avoiding the Robotic Feel

The difference between "sounds like AI" and "sounds like a great narrator" comes down to six factors:

**1. Prosodic variation.** Avoid feeding TTS a wall of text. Break scripts into segments with explicit pacing notes:

```json
{
  "segments": [
    {"text": "Here is the strange thing about entropy.", "pace": "normal", "pause_after": 0.8},
    {"text": "It always increases.", "pace": "slow", "emphasis": true, "pause_after": 1.2},
    {"text": "Not sometimes. Not usually. Always.", "pace": "deliberate", "pause_after": 0.5}
  ]
}
```

**2. Sentence length variation.** Short sentences. Then a longer one that builds and unfolds. Then another short punch. This creates natural rhythm that TTS engines render more convincingly than uniform sentence lengths.

**3. Conversational phrasing.** Write scripts as spoken language, not written language. "Now, here is where it gets interesting" sounds human. "The following demonstrates an interesting property" sounds like a textbook.

**4. Strategic pauses.** Insert explicit pauses before key reveals. ElevenLabs respects `...` and `--` as pause indicators. These micro-pauses create the sense that the narrator is thinking, which is what makes real narration feel alive.

**5. Emotional arc per episode.** Even in 60 seconds, there should be a tonal journey: curiosity (opening) -> tension (the problem) -> clarity (the insight) -> satisfaction (the takeaway). Write the script to guide the TTS through these emotional states via word choice and sentence structure.

**6. Post-processing.** Apply subtle audio processing:
- Light compression to even out volume
- A touch of reverb to add "room" warmth
- EQ to reduce harshness in the 2-4kHz range where synthetic voices often sound metallic
- Normalize loudness to -14 LUFS (YouTube standard)

### 5.3 The "Narrator Character"

Your house style (doc 07) describes "warm, patient, clear, precise." Build this into a narrator persona document that the Scriptwriter Agent references:

> The narrator is a knowledgeable friend who happens to love the history of science. They speak with quiet excitement -- never shouting, never rushing. They pause to let ideas land. They use "we" and "you" to include the viewer. They treat every concept as a story worth savoring.

This persona document is as important as the technical voice settings. It governs word choice, phrasing, rhythm -- all of which the TTS engine will render more naturally when the input text itself sounds human.

---

## 6. Thumbnail Automation

### 6.1 Can Thumbnails Be Auto-Generated Effectively?

**Yes, with caveats.** Automated thumbnails can be functional and consistent, but they will not match hand-crafted thumbnails for your top-performing content.

### 6.2 Recommended Approach: Hybrid Template + AI

**Step 1: Design 3-5 thumbnail templates in Figma or as HTML/CSS.**

Each template has fixed layout zones:
- Background zone (gradient, texture, or AI-generated image)
- Title text zone (large, bold, 3-6 words max)
- Equation/symbol zone (LaTeX-rendered equation or icon)
- Accent element (colored bar, glow effect, episode number)

**Step 2: Automate with Remotion or Puppeteer.**

Render thumbnail templates programmatically:

```tsx
// Remotion thumbnail component
export const Thumbnail: React.FC<{
  title: string;
  equation: string;
  bgColor: string;
  episodeNumber: number;
}> = (props) => {
  return (
    <AbsoluteFill style={{background: props.bgColor}}>
      <EquationCard formula={props.equation} />
      <TitleText text={props.title} />
      <EpisodeBadge number={props.episodeNumber} />
    </AbsoluteFill>
  );
};
```

**Step 3: Use DALL-E 3 for background imagery when needed.**

For topics that benefit from a visual hook (e.g., "The history of entropy" -- show a steam engine; "Quantum tunneling" -- show a particle passing through a wall), generate a background image:

```
Prompt: "Minimalist illustration of a 19th century steam engine with visible
heat flow arrows, dark blue background, educational diagram style, no text,
clean and modern"
```

**Step 4: Claude generates thumbnail metadata.**

The Repurposing Agent produces:
- 3-word title variant for thumbnail
- Equation to feature
- Suggested background mood/subject
- Color palette selection from brand palette

### 6.3 Thumbnail Quality Assessment

For short-form content (Shorts, TikTok): automated thumbnails are fine. These platforms auto-select frames anyway, and custom thumbnails have less impact on discovery.

For long-form YouTube: automated thumbnails get you to 70-80% of optimal CTR. For your top 20% of videos (highest performing topics), manually refine the thumbnail. This is 2 videos/month at 10 minutes each -- negligible time investment for measurable CTR improvement.

---

## 7. Recommended Starter Stack

For Phase 2 (Prototype) as described in doc 10, here is the minimal viable technical stack:

### Must-haves for day one

| Layer | Tool | Why |
|-------|------|-----|
| Intelligence | Claude API (Sonnet for speed, Opus for research quality) | Core of the system per your architecture |
| TTS | ElevenLabs (Scale plan) | Best narration quality, timestamp API, custom voice |
| Math animation | Manim Community Edition | Essential for equation derivations |
| Video assembly | FFmpeg (direct commands) | Start simple before adding Remotion |
| Equation cards | pdflatex + ImageMagick | Reliable, zero cost |
| Subtitles | Script-to-SRT from ElevenLabs timestamps | No STT needed |
| Orchestration | Python scripts + SQLite | Sufficient for prototype |
| Storage | Local filesystem + SQLite | Move to Supabase in Phase 3 |

### Add in Phase 3 (semi-automated publishing)

| Layer | Tool | Why |
|-------|------|-----|
| Video templates | Remotion | Templated composition scales better than raw FFmpeg |
| Thumbnails | Remotion + DALL-E 3 | Automated thumbnail pipeline |
| Cloud rendering | Remotion Lambda | Parallel rendering at scale |
| Database | PostgreSQL via Supabase | Production-grade storage |
| Object storage | Supabase Storage or Cloudflare R2 | Asset hosting |
| Background music | Epidemic Sound | Licensed library |
| Publishing | YouTube Data API v3 + TikTok API + X API v2 | Automated uploads |

### Add in Phase 4-5 (expanded automation)

| Layer | Tool | Why |
|-------|------|-----|
| Workflow orchestration | n8n or Temporal | Complex multi-step workflows with retries |
| Analytics | YouTube Analytics API + custom dashboard | Feedback loop |
| A/B testing | Multiple thumbnail/title variants | CTR optimization |
| Voice expansion | Additional ElevenLabs voices | Series differentiation |
| Multilingual | ElevenLabs Multilingual v2 | Same voice in multiple languages |

---

## 8. Key Technical Risks and Mitigations

**Risk: Manim rendering is slow and fragile.**
Mitigation: Build a Manim scene library of reusable components (axes, arrows, labels, transforms). Cache rendered clips. Have Claude Code attempt render and self-correct on failure (2-attempt loop).

**Risk: ElevenLabs voice consistency drift.**
Mitigation: Lock voice_id, model_id, and all voice settings. Store reference audio. Periodically compare new output against reference samples.

**Risk: Visual quality inconsistency across AI-generated images.**
Mitigation: Use AI images only for backgrounds/illustrations, never for diagrams or equations. Establish a strict prompt template with style prefix. Reject and regenerate images that do not match (use Claude Vision to evaluate).

**Risk: Platform API changes break upload pipeline.**
Mitigation: Abstract each platform behind a publisher interface. YouTube and X APIs are stable. TikTok API changes frequently -- expect maintenance.

**Risk: Cost escalation at scale.**
Mitigation: ElevenLabs is the main variable cost. Monitor character usage. For draft/preview iterations, use OpenAI TTS ($15/1M chars vs ElevenLabs' higher rate). Only use ElevenLabs for final renders.

---

## 9. Implementation Priority for Immediate Next Steps

Given your doc 10 immediate next steps, here is where video production fits:

1. **Now:** Install Manim CE, test rendering a basic equation animation. Verify your local environment can produce `.mp4` clips.
2. **Now:** Create an ElevenLabs account, design or select a narrator voice, generate a 60-second test narration from a sample script.
3. **Now:** Write a Python function that takes a script + narration audio + equation image and produces a basic video via FFmpeg. This is your minimum viable video pipeline.
4. **Week 2-3:** Have Claude Code generate Manim scripts from episode plans. Build the render-and-retry loop.
5. **Week 3-4:** Build the subtitle generation pipeline from ElevenLabs timestamps.
6. **Week 4-5:** Create 2-3 Remotion templates for short-form and long-form video structures.
7. **Week 6+:** Connect to platform upload APIs. Start semi-automated publishing.

The most important principle: **get a single ugly video produced end-to-end before optimizing any individual component.** A working pipeline that produces mediocre video is infinitely more valuable than a perfect TTS setup with no video output.

---

## Summary

This project's video production needs are well-served by current tools. The combination of ElevenLabs (narration) + Manim (math animation) + Remotion (templated composition) + FFmpeg (assembly) + DALL-E 3 (illustrations) provides a complete automated pipeline at $177-365/month for 40 videos. Claude Code can orchestrate the entire flow: generating Manim scripts, writing Remotion components, constructing FFmpeg commands, and producing scene descriptions for image generators. The main quality bottleneck is not the tools -- it is the scripts. If the Scriptwriter Agent produces compelling, well-paced, narratively structured scripts, every downstream tool will produce good output. Invest the most effort in prompt engineering for the writing agents, and the media layer will follow.
