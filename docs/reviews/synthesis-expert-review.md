# Expert Review Synthesis & Improved Plan

**7 expert agents reviewed the project plan. This document consolidates their findings into prioritized, actionable improvements — all filtered through the zero-cost constraint (no expenses beyond Claude Code subscription).**

---

## The Verdict

The plan is architecturally strong but has critical gaps in: distribution strategy, pedagogy, monetization mechanics, and video production specifics. The content philosophy ("postgraduate depth, child-clear intuition, historical storytelling") is a genuine competitive differentiator. Below are the improvements, ranked by priority.

---

## 1. POSITIONING (Must Change)

**Problem:** "Postgraduate-level" intimidates the actual audience (undergrad students, working professionals, lifelong learners — postgrads are <5% of viewers).

**Fix:** Reposition as **"The story behind the equation"** — captures the historical narrative approach, implies depth without intimidation, differentiates from all competitors.

- Keep the postgraduate depth internally
- Use audience-friendly language externally
- Define 3 personas: exam-prep students (40-50%), working professionals (25-30%), curious adults (15-20%)

---

## 2. ZERO-COST PRODUCTION STACK (Confirmed)

All tools free/open-source. Everything runs locally via Claude Code.

| Layer | Tool | Cost |
|-------|------|------|
| Math animations | **Manim CE** + Math-To-Manim skill | $0 |
| Branded segments | **Remotion** (solo dev free) + Claude Code skill | $0 |
| Narration | **edge-tts** (300+ voices, excellent quality) | $0 |
| Zero-cost TTS alt | **Coqui XTTS v2** (local, offline) | $0 |
| Subtitles | **Whisper** (local) or edge-tts timestamps | $0 |
| Video assembly | **FFmpeg** | $0 |
| Equation rendering | **LaTeX** + ImageMagick, or Manim native | $0 |
| Thumbnails | **Pillow** templates + Claude SVGs | $0 |
| Music | **Pixabay Music** / YouTube Audio Library | $0 |
| Database | **SQLite** (MVP) → PostgreSQL later | $0 |
| Upload | YouTube Data API, tweepy, TikTok API | $0 |
| Orchestration | **Python scripts** (MVP) → Temporal later | $0 |
| Symbolic verification | **SymPy** for physics derivations | $0 |

**Install once:**
```bash
pip install manim edge-tts openai-whisper moviepy pillow pysrt sympy TTS
brew install ffmpeg imagemagick cairo
npx create-video@latest  # Remotion
```

---

## 3. NARRATOR CHARACTER (Critical Gap)

**Problem:** "Calm, intelligent, clear" describes Wikipedia, not a brand.

**Fix — Define a narrator archetype:**
- **Perspective:** A knowledgeable friend who loves the history of science
- **Style:** Quiet excitement, never shouting, pauses to let ideas land
- **Pronouns:** Uses "we" and "you" to include the viewer
- **Signature phrases:** "Let's rewind to [year]..." / "Here's where it gets interesting..." / "And this changes everything."
- **Emotional range:** Curiosity → tension → clarity → satisfaction within each episode
- **Vocal personas:** Calm explainer (derivations), excited discoverer (aha moments), dry commentator (misconceptions)

**Script-level emotion markers** for TTS:
```
[pause] before reveals
[slower] for key insights
[with energy] for exciting implications
Sentence fragments for impact. "And then. Nothing."
```

---

## 4. EPISODE ARC TEMPLATES (Critical Gap)

**Problem:** The 10-step arc only fits historically rich topics. ML techniques, analytical chemistry, and mathematical foundations don't have dramatic "eureka" histories.

**Fix — 4 arc templates:**

| Arc | Best For | Flow |
|-----|----------|------|
| **Historical-Dramatic** | Entropy, Bayes, Schrödinger | mystery → confusion → failed idea → turning point → equation → derivation → meaning → modern form → limits → extension |
| **Engineering** | Gradient descent, dropout, MCMC | practical problem → naive attempt fails → key insight → mechanism → walkthrough → when it breaks → the fix → formal spec → connections → frontier |
| **Structural** | Vector spaces, group theory | surprising pattern → what's the same → definition → example → second example → first theorem → proof idea → why it's everywhere → limits → where this leads |
| **Instrument** | Mass spectrometry, NMR | question to answer → obvious measurement fails → physical principle → instrument design → reading output → artifacts → calibration → application → limits → extensions |

Add a **topic-type classifier** step in the Story Architect Agent to select the right arc.

---

## 5. PREREQUISITE DEPENDENCY GRAPH (Critical Gap)

**Problem:** No prerequisite chains. A viewer hitting "Partition Function" without "Probability Distributions" will form wrong mental models.

**Fix:**
- Add `topic_prerequisites` table with `dependency_strength` (hard/soft)
- Build a DAG — never publish a topic before its hard prerequisites
- Story Architect auto-includes "If you haven't seen our episode on X, watch that first"
- Every episode includes a 1-sentence context anchor for mid-series discoverers

---

## 6. CURRICULUM ADDITIONS (High Priority)

### Missing modules identified:
- **Physics:** Nuclear/Particle Physics, Condensed Matter, Astrophysics/Cosmology
- **Chemistry:** Biochemistry Foundations, Materials Chemistry, Computational Chemistry
- **Statistics:** Causal Inference (biggest gap), Experimental Design, High-Dimensional Stats
- **ML:** Foundation Models/LLMs, Diffusion Models, RLHF/Alignment, Mechanistic Interpretability

### Recommended launch order (top 5):
1. **Entropy** — spans all 4 subjects, extraordinary history, high visual potential
2. **Bayes' Theorem** — accessible, compelling history, low risk
3. **Gradient Descent** — outstanding visuals (loss landscapes), cross-subject
4. **Schrödinger Equation** — enormous popular appeal, strong historical arc
5. **Central Limit Theorem** — beautiful visual demo (Galton board), low risk

### Cross-subject "Connections" series:
Entropy, optimization, partition function, Monte Carlo, Fourier analysis, and diffusion all appear in 3-4 subjects. Create bridge episodes linking them.

---

## 7. HOOK LIBRARY (Critical for Short-Form)

10 hook formulas for the Scriptwriter Agent:

1. **Contradiction:** "Everyone thinks entropy means disorder. That's actually wrong."
2. **Prediction:** "This equation predicted antimatter 4 years before anyone found it."
3. **Stakes:** "If Boltzmann had been believed, we'd have understood atoms 20 years earlier."
4. **What-If:** "What if temperature doesn't measure heat — but ignorance?"
5. **Number:** "Four equations explain every electrical phenomenon in the universe."
6. **Origin Story:** "Archimedes figured this out in a bath. But here's what they never tell you."
7. **Wrong Answer:** "Flip a coin 100 times, all heads. Next flip is still 50/50. Your brain refuses this."
8. **Visual Impossibility:** "This says the universe has negative energy. And it's not wrong."
9. **Deleted Scene:** "The version of Newton's 2nd law in school isn't what Newton wrote."
10. **Countdown:** "Part 1 of understanding entropy. By Part 7, you'll know why time moves forward."

Track which hooks perform best per platform in analytics.

---

## 8. MONETIZATION MECHANICS (Major Gap)

The plan lists revenue ideas but has no funnel. Zero-cost monetization actions from Day 1:

| Action | Cost | When |
|--------|------|------|
| **Affiliate links** to cited textbooks (Amazon Associates 4-4.5%) | $0 | Every video description from Ep 1 |
| **Email capture** via Substack free tier or Buttondown | $0 | From launch |
| **Lead magnets** — PDF cheat sheets, research dossiers as study guides | $0 | From launch |
| **Discord community** | $0 | Before first video |
| **YouTube Community tab** polls & teasers | $0 | From launch |
| **Pinned comment** with engagement question on every video | $0 | From launch |
| **LinkedIn posting** for Stats/ML content | $0 | From launch |

### Revenue timeline (realistic):
- Months 3-6: YouTube Partner Program ($50-200/mo)
- Months 6-12: Newsletter + affiliate ($200-500/mo)
- Months 12-18: Sponsorships at 50K+ subs ($1-10K/deal)
- Months 12-24: Membership tiers, courses ($500-5K/mo)
- Month 36: $10-50K/mo total

---

## 9. POSTING CADENCE (Was Undefined)

| Platform | Type | Frequency | Monthly |
|----------|------|-----------|---------|
| YouTube Long-Form | 5-12 min narratives | 1-2/week | 4-8 |
| YouTube Shorts | 30-60s teasers | 5-7/week | 20-30 |
| TikTok | 60-180s discovery | 5-7/week | 20-30 |
| X | Episode posts | 1/day | 30 |
| X | Engagement (polls, questions) | 1/day | 30 |
| X | Supplementary (references, BTS) | 1/day | 30 |
| **Total** | | | **~130-160** |

Content mix: **70% planned series / 20% trending-reactive / 10% experimental**

---

## 10. SAFETY GUARDRAILS

### Analogy warranty field (mandatory):
Every analogy in the research dossier must document: "Valid for [X]. Breaks when [Y]. Corrected in episode [Z]."

### Scaffolding alerts:
When simplifying, tell viewers: "This picture is a starting point. In episode N, we'll see why it needs revising."

### High-risk historical topics (defer until mature):
- Deep learning credit disputes (Schmidhuber vs "three godfathers")
- Fisher's personal views (eugenics)
- Boltzmann's death (don't romanticize mental illness)

### Physics derivations:
Use **SymPy** for symbolic verification of every equation step — free, catches sign errors the LLM won't.

### Never fully remove human review:
Even at scale, sample-based expert review of 20-30% of content.

---

## 11. DATA MODEL ADDITIONS

```
topic_prerequisites    — dependency graph (hard/soft)
prompt_templates       — versioned prompts with usage logging
pipeline_runs          — workflow execution tracking
pipeline_step_logs     — per-step error/retry logging
ab_tests              — A/B test tracking
status_transitions     — audit trail for content workflow
learning_assessments   — polls, quizzes, pedagogical tracking
community_posts        — scheduled Discord/Community tab posts
cross_references       — cross-subject topic links
```

New fields on existing tables:
- `hook_type` on episode_plans
- `emotion_markers` on scripts
- `thumbnail_spec` on media_assets
- `title_variations` on scripts
- `historical_caution_level` on topics (green/yellow/red)
- `citation_difficulty` on topics
- `analogy_warranty` in research dossier JSON
- `bridge_cta` on publication_jobs
- `content_type` on publication_jobs (series/trending/experimental)

---

## 12. MVP: SHIP IN 2 WEEKS

| Week | Deliverable |
|------|------------|
| 1 | SQLAlchemy models, `pipeline.py`, 3 prompt templates, run on Bayes' theorem |
| 2 | Add edge-tts narration + Manim animation + FFmpeg assembly → first ugly video |
| 3 | Run 3 more topics, refine prompts, add citation auditor |
| 4 | Batch of 5 topics, manual upload to YouTube + X, collect initial data |

**The single most important principle:** Get one ugly video produced end-to-end before optimizing anything.

---

## 13. VIDEO PIPELINE (Proven Approach)

```
Claude Code
  ├── Writes Manim script → renders math animation locally
  ├── Writes Remotion component → renders branded segments
  ├── Generates narration text → edge-tts → MP3
  ├── Runs Whisper on MP3 → SRT subtitles
  ├── Assembles via FFmpeg (video + audio + subtitles)
  ├── Renders platform variants (16:9, 9:16)
  └── Generates thumbnail via Pillow template
```

Key tools discovered:
- **Math-To-Manim** — 6-agent pipeline, available as Claude Code skill
- **TheoremExplainAgent** — 93.8% success rate on 5+ min theorem videos
- **Remotion official Claude Code skill** — 25K+ installs
- **Coqui XTTS v2** — free local TTS, zero cost

---

## 14. COMPETITIVE POSITIONING

**The gap in the market:** No one does systematic, serialized, historically-grounded STEM education with modern production quality.

- 3Blue1Brown: visual math intuition, but not historical, infrequent uploads
- Veritasium: investigation/surprise, but not systematic curriculum
- StatQuest: approachable stats, but low production value
- Khan Academy: broad, but dry delivery
- This project: **historical narrative + serialized curriculum + AI production scale**

**The moat is not automation** — everyone will have it by 2027. The moat is editorial quality: postgraduate depth, source grounding, historical storytelling, consistent house style.

**AI disclosure strategy:** "This channel uses AI narration so we can focus entirely on research quality. Every fact is cited. Every story is historically verified." Frame as deliberate choice, not limitation.

---

## Sources for All Reviews

All expert reviews saved in `docs/`:
- `monetization-and-strategy-review.md` — Content Strategy Expert
- `social-media-strategy-review.md` — Social Media Growth Expert
- `11_video_production_technical_review.md` — Video Production Expert
- `technical-review.md` — Software Architecture Expert
- `../research/video-creation-tools-research.md` — Video Tools Research
- (Pedagogy and Science reviews in agent output, key findings integrated above)
