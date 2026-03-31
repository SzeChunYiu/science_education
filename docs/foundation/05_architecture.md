# 5. Automation Architecture & Workflow

## Architecture Layers

### Orchestrator Layer
Triggers workflows, handles schedules, retries, status transitions, data passing.
Options: n8n, Temporal, Python workflow service with cron and queues.

### Storage Layer
Syllabus tracking, topic queue, prompt versioning, source metadata, output assets, publish history, analytics.
Options: PostgreSQL, Supabase, object storage for media files.

### Claude Intelligence Layer
Research synthesis, historical analysis, episode planning, script writing, citation formatting, repurposing, title/metadata generation, QA commentary.

### Retrieval Layer
Web source gathering, textbook note storage, uploaded PDF analysis, source pack building, source metadata normalization.

### Media Layer
AI narration, subtitles, scene lists, equation cards, video templates, thumbnail generation, final video rendering.

### Publishing Layer
YouTube/TikTok/X upload, scheduling, upload verification, post ID storage.

---

## Workflow Stages

1. **Topic Selection** — from syllabus backlog using priority score, platform suitability, freshness, diversity
2. **Source Gathering** — primary sources, textbook refs, modern explanatory refs, secondary historical refs → source pack
3. **Research Dossier** — topic definition, core problem, historical context, equation origin, derivation notes, modern formulation, analogy bank, source map, disputed claims, oversimplification warnings
4. **Episode Planning** — episode number, objective, historical position, central analogy, equation fragment, key claim, reference IDs, hook
5. **Script Generation** — X text, TikTok script, YouTube Shorts script, long-form YouTube script, article version
6. **QA & Validation** — factual, stylistic, compliance checks before media generation
7. **Media Generation** — narration audio, subtitles, scene plans, visual cards, rendered video
8. **Compliance Checks** — disclosure, originality, citation completeness, platform formatting
9. **Upload & Scheduling** — upload to platforms, record status/URLs/timestamps
10. **Analytics Feedback** — views, retention, engagement, follower growth → feed back into topic prioritization
