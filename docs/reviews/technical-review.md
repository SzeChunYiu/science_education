# Technical Architecture Review: Science Education Content Pipeline

**Reviewer:** Software Architect (Content Automation & AI Workflows)
**Date:** 2026-03-29
**Scope:** Documents 01-10, full system design review

---

## Executive Summary

This is an ambitious and well-thought-out content automation system. The content philosophy is strong, the agent decomposition is sensible, and the curriculum structure is sound. However, the architecture documents are heavy on *what* and light on *how*. This review provides concrete implementation guidance, cost projections, data model corrections, an MVP path, scaling analysis, and a CI/CD strategy for content pipelines.

---

## 1. Architecture Critique & Concrete Tech Stack

### 1.1 The Six Layers - What Is Missing

The architecture (doc 05) names six layers but leaves every technology choice as "Options: X, Y, Z." This is a decision document, not an architecture. Below are specific recommendations with rationale.

### 1.2 Orchestration: Temporal (not n8n, not custom Python)

**Recommendation: Temporal (Python SDK)**

| Option | Verdict | Reason |
|--------|---------|--------|
| n8n | Reject | Visual workflow tools break down when you need conditional branching per-agent, retry logic with backoff, human-in-the-loop approval gates, and long-running workflows (video rendering can take 10+ minutes). n8n's error handling is fragile for production content pipelines. |
| Custom Python + cron | Reject for v2+ | Works for MVP (see section 4), but becomes unmaintainable once you have 7 agents, retry logic, parallel platform publishing, and analytics feedback loops. |
| Temporal | Accept | Purpose-built for exactly this: long-running workflows with durable state, automatic retries, human approval signals, and visibility into every workflow step. The Python SDK (`temporalio`) is mature. Each agent call becomes an Activity; the full pipeline becomes a Workflow. |

**Temporal workflow sketch (text diagram):**

```
TopicWorkflow
  |
  +--> Activity: select_topic(syllabus_backlog, priority_scores)
  |
  +--> Activity: gather_sources(topic_id)
  |
  +--> Activity: generate_research_dossier(topic_id, source_pack)
  |       |-- Claude API call: Research Agent
  |       |-- Claude API call: Historian Agent
  |
  +--> Activity: plan_episodes(topic_id, dossier)
  |       |-- Claude API call: Story Architect Agent
  |
  +--> Activity: generate_scripts(topic_id, episode_plan)
  |       |-- Claude API call: Scriptwriter Agent (parallel per platform)
  |       |-- Claude API call: Citation Auditor Agent
  |       |-- Claude API call: Repurposing Agent
  |
  +--> Signal: await_human_review(scripts)     <-- HUMAN GATE
  |
  +--> Activity: generate_media(scripts)        <-- Long-running
  |       |-- TTS via ElevenLabs API
  |       |-- Video render via queue (see 1.4)
  |
  +--> Activity: compliance_check(topic_id)
  |       |-- Claude API call: Compliance Agent
  |
  +--> Activity: publish(platform_assets)       <-- Parallel per platform
  |
  +--> Activity: record_analytics_baseline(publication_ids)
```

**Why this matters:** Temporal gives you free visibility dashboards, automatic retries with exponential backoff, and the ability to pause a workflow for days (human review) without losing state. A custom Python solution would need to reinvent all of this.

**For MVP:** Skip Temporal. Use plain Python functions called sequentially (see section 4). Migrate to Temporal in Phase 3 when you add scheduled publishing and multi-platform parallelism.

### 1.3 Storage: PostgreSQL + S3-compatible Object Storage

**Recommendation: PostgreSQL (direct, not Supabase) + MinIO or Cloudflare R2**

| Component | Choice | Reason |
|-----------|--------|--------|
| Relational data | PostgreSQL 16 | Schema control, JSONB for flexible dossier payloads, full-text search for content deduplication, row-level security if needed later. Supabase adds a layer of abstraction you do not need and locks you into their hosting/auth model. |
| Object storage | Cloudflare R2 | Zero egress fees (critical for serving video). S3-compatible API. For MVP, local filesystem is fine. |
| ORM | SQLAlchemy 2.0 + Alembic | Type-safe, migration-friendly, well-documented. |
| Caching | Redis (later) | For API rate limit tracking, queue state, and prompt template caching. Not needed for MVP. |

**Why not Supabase:** Supabase is a convenience wrapper. For a system that will need custom migrations, prompt versioning tables, complex joins across 12+ tables, and batch operations, raw PostgreSQL with Alembic migrations gives you full control. Supabase's realtime features and auth are irrelevant here -- this is a backend pipeline, not a user-facing app.

### 1.4 Queue System for Async Video Rendering

**Recommendation: Celery + Redis (MVP: `subprocess` with polling)**

Video rendering is the longest-running operation in the pipeline (2-15 minutes per video depending on length and complexity). It must be asynchronous.

```
Architecture:

  Temporal Workflow
       |
       | (dispatch render job)
       v
  Celery Task Queue (Redis broker)
       |
       +--> Worker 1: render_short_video(script, audio, assets)
       +--> Worker 2: render_long_video(script, audio, assets)
       +--> Worker 3: render_equation_cards(latex_fragments)
       |
       v
  On completion: callback --> Temporal signal --> workflow continues
```

**Rendering tool recommendation:** `remotion` (TypeScript, React-based video generation) or `FFmpeg` pipelines wrapped in Python. Remotion is better for templated educational content because you can version-control your video templates as React components. FFmpeg is simpler but less maintainable for complex overlays.

**For equation rendering:** `matplotlib` or `manim` (3Blue1Brown's library) for animated math. `manim` is ideal for this project's aesthetic goals.

**Scaling note:** At 30 videos/month, you do not need a render farm. A single Mac Studio or a 4-core cloud VM handles this. At 300 videos/month, use cloud rendering (AWS Batch or Modal).

### 1.5 Claude API Integration

**Concrete integration design:**

```
Per topic, the Claude API call chain is:

  1. Research Agent:        ~4,000 input tokens, ~3,000 output tokens
  2. Historian Agent:       ~5,000 input tokens, ~2,000 output tokens
  3. Story Architect Agent: ~4,000 input tokens, ~2,500 output tokens
  4. Scriptwriter Agent:    ~3,000 input tokens, ~4,000 output tokens (x4 platforms)
  5. Citation Auditor:      ~5,000 input tokens, ~1,500 output tokens
  6. Repurposing Agent:     ~3,000 input tokens, ~3,000 output tokens
  7. Compliance Agent:      ~4,000 input tokens, ~1,000 output tokens

  Total per topic: ~50,000-70,000 input tokens, ~25,000-35,000 output tokens
  With retries/iterations: multiply by 1.5x
```

**Rate limit strategy:**
- Use Claude's Batch API for non-time-sensitive work (research, QA). 50% cost reduction.
- Implement a token budget tracker per month (hard ceiling alert at 80%).
- Wrap all API calls in a `ClaudeClient` class with automatic retry, exponential backoff, and token counting.
- Store every API call's input/output/token count/cost in a `claude_api_log` table for cost attribution per topic.

**Prompt management pattern:**
```python
class PromptManager:
    def __init__(self, prompts_dir: Path, db: Session):
        self.prompts_dir = prompts_dir
        self.db = db

    def get_prompt(self, agent_name: str, version: str = "latest") -> str:
        """Load prompt template, resolve version, log usage."""
        ...

    def render(self, agent_name: str, **context) -> str:
        """Jinja2 template rendering with context variables."""
        ...
```

Use Jinja2 templates for prompts. Store prompt text in git (version control) and register each version in the database (runtime tracking).

---

## 2. Cost Analysis: 30 Videos/Month

### 2.1 Claude API Costs

Based on Claude Sonnet 4 pricing ($3/1M input, $15/1M output):

| Item | Calculation | Monthly Cost |
|------|------------|-------------|
| Input tokens | 30 topics x 75,000 tokens x 1.5 (retries) = 3.375M | $10.13 |
| Output tokens | 30 topics x 30,000 tokens x 1.5 (retries) = 1.35M | $20.25 |
| Batch API discount (50% of calls) | -30% effective | -$9.11 |
| **Claude subtotal** | | **~$21** |

Using Claude Opus 4 for research/historian agents (higher quality, $15/$75 per 1M):

| Item | Calculation | Monthly Cost |
|------|------------|-------------|
| Opus calls (research + historian) | 30 x 15K input + 30 x 5K output = 0.45M in, 0.15M out | $18 |
| Sonnet calls (remaining agents) | 30 x 60K input + 30 x 25K output = 1.8M in, 0.75M out | $17 |
| **Claude subtotal (mixed model)** | | **~$35** |

**Verdict:** Claude API costs are surprisingly low at this scale. Even with aggressive Opus usage, you are under $50/month. This is not a bottleneck.

### 2.2 TTS Costs (ElevenLabs)

| Tier | Characters/month | Monthly Cost | Videos supported |
|------|-----------------|-------------|-----------------|
| Starter | 30,000 chars | $5 | ~3 short videos |
| Creator | 100,000 chars | $22 | ~10 short + 2 long |
| Pro | 500,000 chars | $99 | 30 short + 10 long comfortably |
| Scale | 2,000,000 chars | $330 | Overkill at 30/month |

Estimate per video:
- Short (60s): ~800 characters
- Long (8min): ~8,000 characters
- 30 shorts + 10 longs = 24,000 + 80,000 = ~104,000 chars/month

**Recommendation:** ElevenLabs Pro ($99/month). Alternatively, evaluate OpenAI TTS ($15/1M characters) which would cost ~$1.56/month but has less voice customization.

**Verdict:** If voice quality is paramount, budget $99/month for ElevenLabs Pro. If cost matters more, OpenAI TTS at ~$2/month is 50x cheaper.

### 2.3 Video Rendering Compute

| Option | Cost | Notes |
|--------|------|-------|
| Local Mac (already owned) | $0 | Fine for 30 videos/month. ~5 min/short, ~20 min/long. Total: ~6 hours/month. |
| Cloud VM (4-core, on-demand) | $15-30/month | Only if you need headless rendering. Use spot instances. |
| Modal (serverless GPU) | ~$5-10/month | Pay-per-render. Good for burst scaling. |
| Render farm | Not needed | Only relevant at 300+ videos/month. |

**Verdict:** $0-$15/month. Use local hardware initially.

### 2.4 Storage and Hosting

| Item | Estimate | Monthly Cost |
|------|----------|-------------|
| PostgreSQL (Neon free tier or local) | 30 topics x 12 rows each | $0 (free tier) |
| Video storage (Cloudflare R2) | 30 videos x ~100MB avg = 3GB/month, cumulative | $0.015/GB = ~$0.50 growing |
| Audio files | Negligible | $0 |
| Backblaze B2 (backup) | 10GB | $0.05 |

**Verdict:** Under $5/month for the first year.

### 2.5 Platform API Costs

| Platform | API Cost | Notes |
|----------|----------|-------|
| YouTube Data API | Free (quota: 10,000 units/day) | Upload = 1,600 units. 30 uploads = trivial. |
| X (Twitter) API | $100/month (Basic) or $0 (Free, limited) | Free tier allows 1,500 tweets/month -- sufficient. Basic for analytics. |
| TikTok | Free (Content Posting API) | Requires app approval. |

**Verdict:** $0-$100/month depending on X tier.

### 2.6 Total Monthly Cost Summary

| Scenario | Monthly Cost |
|----------|-------------|
| **Minimal MVP** (local, OpenAI TTS, free tiers) | **~$15-25** |
| **Recommended setup** (ElevenLabs Pro, basic cloud) | **~$150-200** |
| **Full production** (Opus for research, Pro TTS, cloud rendering, X Basic) | **~$250-300** |

This is extremely cost-effective for 30 produced videos plus multi-platform text content per month.

---

## 3. Data Model Improvements

The schema in doc 08 is a reasonable starting point but is missing five critical components.

### 3.1 Prompt Versioning Table

```sql
CREATE TABLE prompt_templates (
    id              SERIAL PRIMARY KEY,
    agent_name      VARCHAR(50) NOT NULL,  -- 'research', 'historian', etc.
    version         INTEGER NOT NULL,
    template_text   TEXT NOT NULL,
    variables       JSONB,                 -- expected template variables
    model_id        VARCHAR(50),           -- 'claude-sonnet-4', 'claude-opus-4'
    sha256_hash     VARCHAR(64) NOT NULL,  -- content-addressable dedup
    created_at      TIMESTAMPTZ DEFAULT now(),
    created_by      VARCHAR(100),
    is_active       BOOLEAN DEFAULT false,
    notes           TEXT,
    UNIQUE(agent_name, version)
);

CREATE TABLE prompt_usage_log (
    id              SERIAL PRIMARY KEY,
    prompt_template_id  INTEGER REFERENCES prompt_templates(id),
    topic_id        INTEGER REFERENCES topics(id),
    input_tokens    INTEGER,
    output_tokens   INTEGER,
    cost_usd        NUMERIC(10,6),
    latency_ms      INTEGER,
    response_quality_score  NUMERIC(3,2),  -- optional human rating
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

**Why:** Without this, you cannot attribute quality improvements to prompt changes, track cost per agent, or roll back a bad prompt version.

### 3.2 A/B Test Tracking

```sql
CREATE TABLE ab_tests (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(200) NOT NULL,
    description     TEXT,
    test_type       VARCHAR(50),  -- 'prompt', 'hook', 'thumbnail', 'title', 'voice'
    status          VARCHAR(20) DEFAULT 'draft',  -- draft, running, concluded
    start_date      DATE,
    end_date        DATE,
    winner_variant  VARCHAR(1),   -- 'A' or 'B'
    conclusion      TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE ab_test_variants (
    id              SERIAL PRIMARY KEY,
    ab_test_id      INTEGER REFERENCES ab_tests(id),
    variant_label   VARCHAR(1) NOT NULL,  -- 'A', 'B'
    description     TEXT,
    config_json     JSONB   -- prompt_template_id, thumbnail style, etc.
);

CREATE TABLE ab_test_assignments (
    id              SERIAL PRIMARY KEY,
    ab_test_id      INTEGER REFERENCES ab_tests(id),
    variant_id      INTEGER REFERENCES ab_test_variants(id),
    publication_job_id  INTEGER REFERENCES publication_jobs(id),
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

**Why:** Doc 10 mentions analytics feedback but has no mechanism to test whether prompt changes or format changes actually improve performance. Without A/B tracking, you are guessing.

### 3.3 Error/Retry Logging

```sql
CREATE TABLE pipeline_runs (
    id              SERIAL PRIMARY KEY,
    topic_id        INTEGER REFERENCES topics(id),
    workflow_id     VARCHAR(200),       -- Temporal workflow ID
    status          VARCHAR(30) NOT NULL,  -- queued, running, paused_for_review,
                                           -- completed, failed, cancelled
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_summary   TEXT,
    metadata        JSONB
);

CREATE TABLE pipeline_step_logs (
    id              SERIAL PRIMARY KEY,
    pipeline_run_id INTEGER REFERENCES pipeline_runs(id),
    step_name       VARCHAR(100) NOT NULL,  -- 'research_agent', 'tts_generation', etc.
    status          VARCHAR(30) NOT NULL,
    attempt_number  INTEGER DEFAULT 1,
    started_at      TIMESTAMPTZ,
    completed_at    TIMESTAMPTZ,
    error_message   TEXT,
    error_traceback TEXT,
    input_snapshot  JSONB,      -- for debugging/replay
    output_snapshot JSONB,
    retry_after     TIMESTAMPTZ
);
```

**Why:** The current schema has no way to answer "why did topic X fail?" or "how often does the Citation Auditor reject scripts?" This data is essential for pipeline reliability.

### 3.4 Content Dependency Graph (Prerequisites)

```sql
CREATE TABLE topic_prerequisites (
    id              SERIAL PRIMARY KEY,
    topic_id        INTEGER REFERENCES topics(id),
    prerequisite_topic_id  INTEGER REFERENCES topics(id),
    relationship_type      VARCHAR(30),  -- 'hard_prerequisite', 'soft_recommended',
                                         -- 'builds_on', 'contrasts_with'
    ordering_hint   INTEGER,
    UNIQUE(topic_id, prerequisite_topic_id)
);

-- Example: "Partition function" requires "Boltzmann distribution"
-- Example: "Gradient descent" soft-recommends "Linear regression"
```

**Why:** The curriculum (doc 03) lists modules but not dependencies between topics. Without this, the topic selection algorithm might publish "Partition Function" before "Boltzmann Distribution," confusing the audience. This table enables topological sorting for publication order.

### 3.5 Content Status Workflow

The `scripts` table has a `status` field but no defined states. Add an explicit state machine:

```sql
-- Add to topics table:
ALTER TABLE topics ADD COLUMN workflow_status VARCHAR(30) DEFAULT 'backlog';

-- Valid states and transitions:
--
--   backlog
--     --> researching
--       --> research_complete
--         --> planning
--           --> drafting
--             --> draft_review        <-- HUMAN GATE
--               --> approved | revision_requested
--                 --> media_generating
--                   --> media_review  <-- HUMAN GATE
--                     --> compliance_check
--                       --> ready_to_publish
--                         --> published
--                           --> analytics_tracking

CREATE TABLE status_transitions (
    id              SERIAL PRIMARY KEY,
    topic_id        INTEGER REFERENCES topics(id),
    from_status     VARCHAR(30),
    to_status       VARCHAR(30) NOT NULL,
    transitioned_by VARCHAR(100),  -- 'system', 'human:billy', etc.
    reason          TEXT,
    created_at      TIMESTAMPTZ DEFAULT now()
);
```

**Why:** The current schema conflates "script exists" with "script is approved." You need a clear audit trail of who approved what and when, especially for a pipeline that might publish automatically.

### 3.6 Full Improved Entity Relationship (Text Diagram)

```
subjects
  |-- 1:N --> modules
                |-- 1:N --> topics
                              |-- 1:N --> sources
                              |-- 1:N --> research_dossiers (versioned)
                              |-- 1:N --> episode_plans
                              |           |-- 1:N --> scripts (versioned, per platform)
                              |           |-- 1:N --> media_assets
                              |-- 1:N --> publication_jobs
                              |           |-- 1:N --> analytics
                              |           |-- N:1 --> ab_test_assignments
                              |-- 1:N --> pipeline_runs
                              |           |-- 1:N --> pipeline_step_logs
                              |-- 1:N --> status_transitions
                              |-- N:N --> topic_prerequisites

prompt_templates
  |-- 1:N --> prompt_usage_log

ab_tests
  |-- 1:N --> ab_test_variants
  |-- 1:N --> ab_test_assignments
```

---

## 4. MVP Technical Path

**Principle:** Ship a working pipeline in 2 weeks, not a perfect architecture in 2 months.

### 4.1 MVP Stack

| Layer | MVP Choice | Upgrade Path |
|-------|-----------|-------------|
| Orchestration | `pipeline.py` -- a single Python script with sequential function calls | Temporal in Phase 3 |
| Storage | SQLite (single file, zero config) | PostgreSQL in Phase 2 |
| ORM | SQLAlchemy 2.0 (works with both SQLite and PostgreSQL) | No change needed |
| Prompts | Jinja2 templates in `prompts/` directory, git-versioned | Add DB tracking in Phase 2 |
| Claude API | `anthropic` Python SDK, synchronous calls | Add batching in Phase 3 |
| TTS | OpenAI TTS API ($0.015/1K chars) | ElevenLabs when voice quality matters |
| Video | FFmpeg + matplotlib for equation cards | Remotion or manim in Phase 2 |
| Publishing | Manual upload (copy-paste or drag-drop) | API upload in Phase 3 |
| Review | Human reads output files, approves via CLI prompt | Web dashboard in Phase 4 |

### 4.2 MVP File Structure

```
science_education/
  docs/                          # Already exists
  prompts/
    research_agent.j2
    historian_agent.j2
    story_architect_agent.j2
    scriptwriter_agent.j2
    citation_auditor_agent.j2
    repurposing_agent.j2
    compliance_agent.j2
  src/
    pipeline.py                  # Main orchestrator (sequential)
    claude_client.py             # Wrapper: prompt loading, API calls, token tracking
    models.py                    # SQLAlchemy models
    tts.py                       # TTS generation (OpenAI or ElevenLabs)
    video.py                     # FFmpeg wrapper for basic video assembly
    utils.py
  data/
    science_education.db         # SQLite database
  output/
    topics/
      bayes-theorem/
        dossier.json
        episodes/
          01_the_mystery.json
        scripts/
          01_x_post.md
          01_tiktok_script.md
          01_youtube_short.md
          01_youtube_long.md
          01_article.md
        media/
          01_narration.mp3
          01_short_video.mp4
          01_equation_card.png
  tests/
    test_pipeline.py
    test_claude_client.py
```

### 4.3 MVP Pipeline (Pseudocode)

```python
# pipeline.py -- the entire MVP orchestrator

def run_topic(topic_slug: str):
    db = get_session()
    topic = db.query(Topic).filter_by(slug=topic_slug).one()

    # Step 1: Research
    dossier = call_claude("research_agent", topic=topic)
    save_dossier(db, topic, dossier)

    # Step 2: Historical review
    history_review = call_claude("historian_agent", topic=topic, dossier=dossier)
    update_dossier(db, topic, history_review)

    # Step 3: Episode planning
    episodes = call_claude("story_architect_agent", topic=topic, dossier=dossier)
    save_episodes(db, topic, episodes)

    # Step 4: Script generation (loop over episodes)
    for episode in episodes:
        scripts = call_claude("scriptwriter_agent", topic=topic, episode=episode)
        save_scripts(db, topic, episode, scripts)

    # Step 5: Citation audit
    audit = call_claude("citation_auditor_agent", topic=topic, scripts=scripts)
    if audit.has_failures:
        print(f"CITATION FAILURES: {audit.failures}")
        return  # Stop here, fix manually

    # Step 6: HUMAN REVIEW GATE
    print("Scripts written. Review output/ directory.")
    approval = input("Approve? (y/n): ")
    if approval != 'y':
        return

    # Step 7: TTS
    for script in get_approved_scripts(db, topic):
        audio = generate_tts(script.content)
        save_audio(topic, script, audio)

    # Step 8: Video rendering
    for script in get_approved_scripts(db, topic):
        render_video(topic, script)  # FFmpeg subprocess

    print(f"Done. Upload manually from output/{topic_slug}/media/")

if __name__ == "__main__":
    run_topic(sys.argv[1])
```

**This is ugly and that is fine.** It produces content. You can run it tomorrow. Optimize later.

### 4.4 MVP Timeline

| Week | Deliverable |
|------|------------|
| 1 | SQLAlchemy models, claude_client.py, 3 prompt templates (research, story architect, scriptwriter), pipeline.py skeleton |
| 2 | Run on one topic (Bayes' theorem), fix prompts based on output quality, add TTS and basic FFmpeg video assembly |
| 3 | Run on 3 more topics, refine house style enforcement, add citation auditor |
| 4 | Semi-automated batch: run 5 topics, manual upload, collect initial analytics |

---

## 5. Scaling Bottlenecks (Ranked by Impact)

### 5.1 Bottleneck #1: Human QA Review

**The system will break here first.**

At 30 videos/month, you need to review ~30 dossiers, ~120 scripts (4 platforms x 30), and ~40 rendered videos. That is roughly 20-30 hours/month of review time for one person.

**Mitigations:**
- Tiered review: auto-approve scripts where the Compliance Agent gives high confidence (>0.9). Human reviews only flagged items.
- Batch review UI: build a simple Streamlit dashboard showing scripts side-by-side with dossier, one-click approve/reject.
- Sampling: after the first 50 topics, review only 30% randomly. Let the compliance agent handle the rest.

### 5.2 Bottleneck #2: Video Rendering Time

At 30 videos/month with a mix of short and long form:
- 30 short videos x 5 min render = 2.5 hours
- 10 long videos x 20 min render = 3.3 hours
- Total: ~6 hours/month (manageable)

At 100+ videos/month, this becomes 20+ hours and needs parallelization (multiple Celery workers or cloud rendering).

### 5.3 Bottleneck #3: Claude API Rate Limits

Claude's rate limits (as of 2026) typically allow:
- Tier 1: 50 RPM, 40,000 TPM
- Tier 4: 4,000 RPM, 400,000 TPM

At 30 topics/month, you make ~300 API calls total. Even at Tier 1, this is nowhere near the limit if spread across days. Burst processing (all 30 topics in one day) could hit TPM limits -- solution: add a 2-second delay between calls or use the Batch API.

### 5.4 Bottleneck #4: Storage Costs (Long-Term)

Video accumulates. After 12 months at 30 videos/month:
- 360 short videos x 50MB = 18GB
- 120 long videos x 300MB = 36GB
- Total: ~54GB

At Cloudflare R2 pricing ($0.015/GB/month): $0.81/month. Not a real bottleneck.

### 5.5 Bottleneck #5: Prompt Quality Degradation

As the curriculum expands from "explain Bayes' theorem" to "explain renormalization group flow in statistical field theory," the same prompts may produce lower-quality output. This is a **silent failure mode** -- the system keeps running but quality drops.

**Mitigation:** Track output quality scores per module difficulty level. Alert when average scores for advanced topics drop below threshold. Maintain separate prompt variants for introductory vs. advanced topics.

### 5.6 Bottleneck Summary

```
Impact vs. Timeline:

  HIGH IMPACT  |  QA Review ---------> (hits at 30/month)
               |  Prompt Quality ----> (hits at ~100 topics, advanced material)
               |
  MED IMPACT   |  Render Time -------> (hits at 100/month)
               |  Rate Limits -------> (hits only with burst processing)
               |
  LOW IMPACT   |  Storage Costs -----> (years away from mattering)
               |
               +----------------------------------------------------->
                 Month 1         Month 6        Month 12       Month 24
```

---

## 6. CI/CD for Content

### 6.1 Git-Based Content Pipeline

**Everything that defines output quality goes in git:**

```
Repository structure:

  prompts/
    research_agent/
      v1.j2
      v2.j2                # New version = new file, not overwrite
      CHANGELOG.md
    historian_agent/
      v1.j2
    ...
  schemas/
    dossier_schema.json     # JSON Schema for research dossier
    episode_schema.json
    script_schema.json
  templates/
    video/
      short_form.json       # Video template definition
      long_form.json
    thumbnail/
      standard.json
  tests/
    test_prompts.py         # Validate prompts render without error
    test_schemas.py         # Validate schema files
    test_pipeline_unit.py
    test_output_quality.py  # Run a golden test topic through pipeline
  .github/
    workflows/
      prompt_test.yml       # CI: validate prompts on every push
      golden_test.yml       # CI: run one topic end-to-end weekly
```

### 6.2 Prompt Change Workflow

```
Developer edits prompts/scriptwriter_agent/v3.j2
  |
  +--> git commit + push
  |
  +--> CI: prompt_test.yml
  |     |-- Validate Jinja2 syntax
  |     |-- Check required variables present
  |     |-- Run prompt against golden topic (Bayes' theorem)
  |     |-- Compare output to baseline (fuzzy match on structure)
  |     |-- Report token count delta (cost impact)
  |
  +--> PR review (human reads diff + CI output)
  |
  +--> Merge to main
  |
  +--> CD: register new prompt version in database
  |     |-- INSERT INTO prompt_templates (agent='scriptwriter', version=3, ...)
  |     |-- SET is_active = true
  |     |-- Previous version: is_active = false
```

### 6.3 Golden Test

A "golden test" is a single topic (e.g., Bayes' theorem) run through the full pipeline with deterministic settings (temperature=0). The output is compared against a known-good baseline. This catches:
- Prompt regressions
- Schema changes that break downstream steps
- API response format changes

```python
# tests/test_golden.py
def test_bayes_theorem_pipeline():
    result = run_topic("bayes-theorem", dry_run=True, temperature=0)

    assert result.dossier is not None
    assert len(result.episodes) >= 5
    assert all(ep.word_count <= 220 for ep in result.episodes)  # 200 + tolerance
    assert result.citation_audit.failures == []
    assert result.compliance.status == "pass"

    # Structural checks
    assert "Reverend Thomas Bayes" in result.dossier.historical_timeline
    assert result.dossier.sources_count >= 3
```

### 6.4 Content Versioning Strategy

| Artifact | Versioning Method | Storage |
|----------|------------------|---------|
| Prompts | Git + DB registration | `prompts/` directory |
| Schemas | Git (JSON Schema files) | `schemas/` directory |
| Video templates | Git | `templates/` directory |
| Dossiers | DB (version column, JSONB) | `research_dossiers` table |
| Scripts | DB (version column per platform) | `scripts` table |
| Media assets | Object storage with content-hash naming | R2/S3 |
| Pipeline config | Git (`config.yaml`) | Repository root |

### 6.5 Rollback Strategy

If a prompt change causes quality degradation:
1. Revert the prompt in git (standard `git revert`).
2. CI re-runs golden test to confirm fix.
3. CD sets `is_active = false` on bad version, `is_active = true` on previous.
4. Any topics produced with the bad prompt are flagged for re-generation:
   ```sql
   UPDATE scripts SET status = 'needs_regeneration'
   WHERE prompt_template_id = <bad_version_id>;
   ```

---

## 7. Additional Recommendations

### 7.1 Observability

Add structured logging from day 1. Use Python's `structlog` library:
```python
import structlog
log = structlog.get_logger()
log.info("claude_api_call", agent="research", topic="bayes-theorem",
         input_tokens=4200, output_tokens=3100, latency_ms=2340)
```

This pays dividends immediately when debugging why a topic failed.

### 7.2 Content Deduplication

Before generating a new topic, check for semantic overlap with existing content:
```sql
-- Simple: full-text search on existing scripts
SELECT * FROM scripts
WHERE to_tsvector('english', content) @@ plainto_tsquery('english', 'Bayes theorem prior')
AND status = 'published';
```

For better results, store embeddings (via Claude or a smaller model) and do cosine similarity search. PostgreSQL + `pgvector` extension handles this natively.

### 7.3 Suggested Library Stack

| Purpose | Library | Why |
|---------|---------|-----|
| Claude API | `anthropic` (official SDK) | Maintained, typed, supports batching |
| ORM | `sqlalchemy[asyncio]` 2.0 | Async support, SQLite and PostgreSQL |
| Migrations | `alembic` | Standard for SQLAlchemy |
| Templates | `jinja2` | Battle-tested, good for prompts |
| TTS | `openai` SDK or `elevenlabs` SDK | Official SDKs |
| Video | `ffmpeg-python` + `manim` | Programmatic video, math animations |
| CLI | `typer` | Modern Python CLI framework |
| Testing | `pytest` + `pytest-asyncio` | Standard |
| Logging | `structlog` | Structured JSON logging |
| Config | `pydantic-settings` | Type-safe config from env/files |
| HTTP | `httpx` | Async HTTP for API uploads |
| Queue (later) | `celery[redis]` | Async task queue for rendering |
| Orchestration (later) | `temporalio` | Durable workflow engine |

### 7.4 Risk: Platform API Instability

TikTok and X APIs change frequently. Build a platform adapter pattern:
```python
class PlatformPublisher(Protocol):
    def upload(self, content: PlatformContent) -> PublishResult: ...
    def check_status(self, post_id: str) -> PostStatus: ...
    def get_analytics(self, post_id: str) -> Analytics: ...

class YouTubePublisher(PlatformPublisher): ...
class TikTokPublisher(PlatformPublisher): ...
class XPublisher(PlatformPublisher): ...
```

If an API breaks, you swap the implementation without touching the pipeline.

---

## 8. Summary of Recommendations

| Priority | Recommendation | Effort |
|----------|---------------|--------|
| P0 | Build MVP as single Python script + SQLite (section 4) | 2 weeks |
| P0 | Write 7 prompt templates and test on Bayes' theorem | 1 week |
| P0 | Add prompt versioning table and API cost logging | 1 day |
| P1 | Add status workflow state machine to data model | 1 day |
| P1 | Add topic prerequisites table | 0.5 day |
| P1 | Set up git-based prompt CI (golden test) | 2 days |
| P1 | Add error/retry logging tables | 0.5 day |
| P2 | Migrate SQLite to PostgreSQL | 1 day (if using SQLAlchemy) |
| P2 | Add Streamlit review dashboard | 3 days |
| P2 | Implement A/B test tracking | 2 days |
| P3 | Migrate to Temporal orchestration | 1 week |
| P3 | Add Celery for async video rendering | 2 days |
| P3 | Implement platform API publishers | 3 days per platform |

**The single most important thing:** Run the pipeline on one topic this week. Real output reveals more than any architecture document.
