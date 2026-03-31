# Project Plan: Fully Automated Educational Content Factory for Claude Code

## 1. Project Overview

Build a fully automated content pipeline that uses Claude as the main intelligence layer to research, plan, write, adapt, package, render, and publish educational content across multiple social platforms.

The content focus is postgraduate-level **Physics, Chemistry, Statistics, and Machine Learning**, taught through:
- historically grounded development
- intuitive storytelling
- daily-life examples
- short serialized episodes
- formal citations and references

The key promise of the project is:

> Teach postgraduate-level subjects with child-clear intuition.

The system should produce:
- short written episodes for X
- short narrated videos for TikTok and YouTube Shorts
- longer narrated videos for YouTube
- deeper article/newsletter versions for archive or premium products

The system should be designed so that:
- research is source-grounded
- outputs are original
- historical claims are cited
- the style stays consistent
- media production and uploading can run automatically

---

## 2. Core Goal

Create a reusable automation system that can:

1. choose a topic from a postgraduate syllabus
2. collect and analyze source material
3. generate a historical and conceptual research dossier
4. break the topic into a short story-based episode series
5. create platform-specific content variants
6. generate AI narration and visuals
7. render videos and visual assets
8. run factual, stylistic, and compliance checks
9. upload content to social media platforms
10. record analytics and use them to improve future topic selection

---

## 3. Content Philosophy

The project is based on five principles:

### 3.1 Postgraduate depth
All subjects should be taught at serious academic depth.

### 3.2 Child-clear intuition
The central idea of a topic should be explainable through a simple story or everyday image that a bright 10-year-old could understand.

### 3.3 Historical development
Topics should be presented following the historical growth of the concept whenever reasonable:
- what problem people faced
- what earlier attempts existed
- what idea changed the field
- how the equation or theory emerged
- how the modern version differs from the original form

### 3.4 Formal credibility
All non-obvious factual claims should be tied to references. The project must distinguish:
- historical fact
- pedagogical simplification
- modern notation
- storyteller analogy

### 3.5 Serialization
Each big concept becomes a series of short episodes rather than one overloaded explanation.

---

## 4. Content Formats

## 4.1 Canonical content unit
Each topic should first exist as a **canonical research-backed lesson package**.

This package will then be transformed into multiple formats.

## 4.2 Episode format
Each episode should:
- be at most 200 words for short written versions
- explain one step, one historical turn, one equation term, or one conceptual leap
- end with a hook to the next episode
- include a historical note and references outside the story body

## 4.3 Platform outputs
For each topic, the system should generate:

### X
- 1 short post or one thread segment per episode
- optional image or equation card
- citation-light format

### TikTok
- 30–90 second short narrated video
- quick hook
- clear story arc
- visual overlays and captions

### YouTube Shorts
- adapted version of TikTok script
- slightly more educational density if appropriate

### Long-form YouTube
- 5–12 minute narrative video
- historical progression
- derivation overview
- references in description

### Article / Newsletter / PDF
- deeper explanation
- full references
- formal structure
- expandable into premium content later

---

## 5. Project Scope

The initial subject domains are:

- Physics
- Chemistry
- Statistics
- Machine Learning

The long-term goal is to cover all essential postgraduate-level core topics in these subjects through serialized story-based instruction.

---

## 6. Curriculum Framework

Each subject should be organized into:
- subject
- module
- topic
- subtopic
- episode sequence

## 6.1 Physics modules
Suggested core modules:
- Mathematical Methods
- Classical Mechanics
- Electromagnetism
- Quantum Mechanics
- Statistical Mechanics and Thermodynamics
- Relativity
- Waves and Continuum Topics
- Advanced / Elective Topics

## 6.2 Chemistry modules
Suggested core modules:
- Physical Chemistry
- Organic Chemistry
- Inorganic Chemistry
- Analytical and Instrumental Chemistry
- Quantum Chemistry Foundations
- Spectroscopy
- Thermodynamics and Kinetics

## 6.3 Statistics modules
Suggested core modules:
- Probability Foundations
- Statistical Inference
- Linear Models
- Bayesian Statistics
- Multivariate Statistics
- Stochastic Processes
- Computational Statistics
- Statistical Learning Foundations

## 6.4 Machine Learning modules
Suggested core modules:
- Mathematical Foundations
- Optimization
- Supervised Learning
- Probabilistic Modeling
- Statistical Learning Theory
- Deep Learning
- Representation Learning
- Sequence Models
- Generative Models
- Reinforcement Learning

---

## 7. Content Unit Design

Each topic should move through the following hierarchy:

### 7.1 Topic
A major concept, such as:
- Bayes' theorem
- Gradient descent
- Partition function
- Schrödinger equation
- Entropy
- Linear regression

### 7.2 Research dossier
A structured document containing:
- core question
- historical timeline
- key figures
- earliest useful formulation
- modern formulation
- derivation path
- major misconceptions
- analogy candidates
- approved reference list

### 7.3 Episode arc
A set of short episodes that together explain the concept.

A standard episode arc may include:
1. the mystery
2. the early confusion
3. the failed old idea
4. the conceptual turning point
5. the first useful equation form
6. one derivation step
7. meaning of a term
8. modern interpretation
9. assumptions and limitations
10. postgraduate extension

---

## 8. Automation Architecture

The system should be divided into layers.

## 8.1 Orchestrator layer
Responsible for:
- triggering workflows
- handling schedules
- retries
- status transitions
- passing data between stages

Recommended options:
- n8n
- Temporal
- Python workflow service with cron and queues

## 8.2 Storage layer
Responsible for:
- syllabus tracking
- topic queue
- prompt versioning
- source metadata
- output assets
- publish history
- analytics

Recommended options:
- PostgreSQL
- Supabase
- object storage for media files

## 8.3 Claude intelligence layer
Responsible for:
- research synthesis
- historical analysis
- episode planning
- script writing
- citation formatting
- repurposing
- title generation
- metadata generation
- QA commentary

## 8.4 Retrieval layer
Responsible for:
- web source gathering
- textbook note storage
- uploaded PDF analysis
- source pack building
- source metadata normalization

## 8.5 Media layer
Responsible for:
- AI narration
- subtitles
- scene lists
- equation cards
- video templates
- thumbnail generation
- final video rendering

## 8.6 Publishing layer
Responsible for:
- YouTube upload
- TikTok upload
- X post creation
- scheduling
- upload verification
- post ID storage

---

## 9. Workflow Stages

## 9.1 Stage 1: Topic selection
Input:
- syllabus backlog
- priority score
- platform suitability
- topic freshness and diversity

Output:
- selected topic for production

Selection criteria may include:
- educational importance
- visual potential
- historical richness
- audience demand
- cross-platform fit
- prerequisite readiness

## 9.2 Stage 2: Source gathering
The system gathers:
- primary or historically close sources
- standard textbook references
- modern explanatory references
- secondary historical references

Output:
- a source pack

## 9.3 Stage 3: Research dossier generation
Claude generates a structured research dossier.

Required dossier sections:
- topic definition
- core problem
- historical context
- equation origin
- derivation notes
- modern formulation
- analogy bank
- source map
- known disputed claims
- warning notes for oversimplification

## 9.4 Stage 4: Episode series planning
Claude converts the dossier into a short series plan.

Each episode plan should include:
- episode number
- objective
- historical position
- central analogy
- equation fragment if any
- key claim
- reference IDs
- hook to next episode

## 9.5 Stage 5: Script generation
Claude produces:
- X episode text
- TikTok script
- YouTube Shorts script
- long-form YouTube outline or script
- article/newsletter version

## 9.6 Stage 6: QA and validation
The system must run checks before media generation or upload.

## 9.7 Stage 7: Media generation
Generate:
- narration audio
- subtitle files
- scene plans
- visual cards
- rendered video outputs

## 9.8 Stage 8: Compliance checks
Check:
- disclosure requirements
- originality and repetition risk
- citation completeness
- platform-specific formatting

## 9.9 Stage 9: Upload and scheduling
Upload finalized assets to:
- X
- TikTok
- YouTube

Record:
- upload status
- post URL or ID
- scheduled/published timestamps

## 9.10 Stage 10: Analytics feedback
Collect:
- views
- retention
- engagement
- follower growth
- click-through
- conversion to longer content

Feed results back into topic prioritization and style optimization.

---

## 10. Claude Agent Design

Do not use one giant prompt.

Use role-based prompt modules.

## 10.1 Research Agent
Purpose:
- gather and synthesize sources
- produce research dossier

Inputs:
- topic
- module
- source pack

Outputs:
- normalized topic research JSON
- bibliographic list
- claim table

## 10.2 Historian Agent
Purpose:
- verify historical order
- detect anachronisms
- separate original vs modern forms

Outputs:
- corrected timeline
- historical caution notes
- priority/discovery warnings

## 10.3 Story Architect Agent
Purpose:
- design the episode arc
- assign one learning goal per episode
- propose everyday analogies

Outputs:
- episode blueprint
- analogy map
- narrative progression

## 10.4 Scriptwriter Agent
Purpose:
- write the content in house style

Outputs:
- X version
- short video version
- long-form version
- article version

## 10.5 Citation Auditor Agent
Purpose:
- verify support for non-obvious claims
- ensure proper referencing

Outputs:
- missing citation report
- weak-claim warnings
- final reference list

## 10.6 Repurposing Agent
Purpose:
- adapt one core script into all platforms

Outputs:
- platform-specific text assets
- title variations
- captions
- CTAs
- hashtag suggestions

## 10.7 Compliance Agent
Purpose:
- check policy alignment
- flag possible low-value mass-content patterns
- set disclosure requirements

Outputs:
- pass/fail
- disclosure flags
- publication notes

---

## 11. House Style for Claude

Claude should follow these writing instructions.

### 11.1 Mission
Write serialized educational stories that teach a postgraduate-level concept with historically faithful, intuitive, everyday storytelling.

### 11.2 Target outcome
The core idea should be understandable to a bright 10-year-old, while remaining accurate enough for a serious graduate learner to trust the setup.

### 11.3 Tone
- warm
- patient
- clear
- precise
- never childish
- never condescending
- never melodramatic

### 11.4 Episode rules
- max 200 words for short episode formats
- one main idea per episode
- one analogy at a time
- one derivation move at a time
- end with a forward hook
- avoid unnecessary jargon
- define symbols only when needed

### 11.5 Historical fidelity rules
- do not start with the final polished modern equation if history did not
- do not invent fake discovery stories
- do not merge separate historical developments without saying so
- distinguish history from teaching simplification
- if a derivation is modernized, label it as a pedagogical derivation

### 11.6 Citation rules
- cite non-obvious factual claims
- keep citations light inside short content
- give fuller references outside the story body
- distinguish primary, textbook, and secondary references where possible

### 11.7 What not to do
- do not imitate textbook language
- do not dump formulas without meaning
- do not over-compress difficult topics into misleading analogies
- do not sound like generic AI educational content
- do not copy source phrasing

---

## 12. Research Protocol

For each topic, the system must answer five questions before writing:

1. What problem was people trying to solve?
2. Who are the key historical figures?
3. What was the earliest useful form of the equation or concept?
4. How did the derivation or reasoning emerge?
5. How is the concept formulated in modern postgraduate teaching?

Each topic should ideally use:
- one primary or historically close source
- one standard textbook
- one modern explanatory or historical source

The system should store:
- bibliographic metadata
- source type
- citation format
- claims supported by each source

---

## 13. Recommended Data Model

Suggested main tables or collections:

## 13.1 subjects
Fields:
- id
- name
- description

## 13.2 modules
Fields:
- id
- subject_id
- name
- ordering

## 13.3 topics
Fields:
- id
- module_id
- slug
- name
- description
- difficulty
- historical_importance
- visual_potential
- platform_fit_score
- status

## 13.4 sources
Fields:
- id
- topic_id
- title
- author
- year
- source_type
- url_or_file_path
- citation_text
- trust_score

## 13.5 research_dossiers
Fields:
- id
- topic_id
- version
- json_payload
- created_at

## 13.6 episode_plans
Fields:
- id
- topic_id
- episode_number
- objective
- historical_context
- analogy
- key_claims
- references
- hook

## 13.7 scripts
Fields:
- id
- topic_id
- episode_number
- platform
- version
- content
- status

## 13.8 media_assets
Fields:
- id
- topic_id
- episode_number
- platform
- asset_type
- file_path
- status

## 13.9 publication_jobs
Fields:
- id
- topic_id
- episode_number
- platform
- scheduled_at
- published_at
- remote_post_id
- status
- disclosure_flags

## 13.10 analytics
Fields:
- id
- publication_job_id
- metric_name
- metric_value
- captured_at

---

## 14. Automation Rules

## 14.1 Hard fail conditions
The system must not publish if:
- there are fewer than two credible sources for a topic
- historical origin claims are unsupported
- citation mapping fails
- script length constraints are broken
- disclosure status is unknown
- asset generation failed
- the output is too similar to recent outputs
- the topic is missing required metadata

## 14.2 Soft warnings
Warn but allow review if:
- historical accounts differ across sources
- analogy fidelity is imperfect but acceptable
- the script is accurate but not vivid enough
- the content is too similar in tone to recent uploads

## 14.3 Versioning
Store versions for:
- prompts
- dossiers
- scripts
- media assets
- publication payloads

This is necessary for debugging and quality iteration.

---

## 15. Media Production Plan

## 15.1 Narration
Use AI voice narration with a stable brand voice.

Narration style:
- calm
- intelligent
- clear
- story-like
- not overdramatic

Generate:
- full narration audio
- sentence timestamps if possible
- alternate short-form pacing version

## 15.2 Visual style
Prefer a consistent and trustworthy visual identity:
- equation cards
- simple diagrams
- text overlays
- subtle motion graphics
- recurring layout
- controlled color palette
- historical portrait slides only where permitted and appropriate

Avoid a chaotic “AI slop” look.

## 15.3 Video structure
Short-form:
- hook
- mystery
- one idea
- one image
- one takeaway
- CTA

Long-form:
- opening question
- historical setup
- problem
- step-by-step conceptual explanation
- selected derivation section
- meaning and interpretation
- references and next topic teaser

---

## 16. Platform Publishing Plan

## 16.1 X
Use for:
- serialized written episodes
- authority building
- audience testing
- driving traffic to longer content

Suggested cadence:
- frequent
- short
- highly consistent

## 16.2 TikTok
Use for:
- short discovery videos
- highly compressed narrative hooks
- broad top-of-funnel reach

Suggested style:
- visual clarity
- quick opening
- one strong metaphor
- fast payoff

## 16.3 YouTube Shorts
Use for:
- discovery
- educational teaser content
- gateway to long-form channel

## 16.4 Long-form YouTube
Use for:
- core archive
- trust building
- deeper retention
- stronger long-term monetization potential

---

## 17. Analytics Loop

The system should collect and analyze:
- impressions
- views
- watch time
- completion rate
- retention curve
- reposts/shares
- comments
- saves
- click-through to long-form content
- follower/subscriber growth

Claude can then be used to generate:
- hook performance summaries
- analogy performance summaries
- topic cluster performance summaries
- recommendations for the next topic queue

---

## 18. Monetization Alignment

The system should be designed not only for publishing but for long-term monetization.

Potential monetization layers:
- platform creator revenue
- subscriptions
- premium notes
- paid newsletters
- courses
- ebooks
- curriculum bundles
- school/teacher resources
- sponsored educational partnerships later

To support monetization, the project must optimize for:
- originality
- consistency
- trust
- reference quality
- evergreen utility

---

## 19. Rollout Plan

## Phase 1: Foundation
- finalize house style
- define syllabus backbone
- build database schema
- build prompt stack
- choose first subject

## Phase 2: Prototype
- automate one subject only
- produce 5–10 topics
- generate drafts and assets
- publish manually or semi-manually
- refine prompts and QA rules

## Phase 3: Semi-automated publishing
- enable scheduled uploads
- maintain human review gate
- collect analytics
- improve system stability

## Phase 4: Expanded automation
- add all target platforms
- automate backlog management
- improve feedback loop
- reduce manual work to exception handling

## Phase 5: Full-scale operation
- run continuous content generation
- performance-based topic selection
- multilingual or multi-voice expansion if desired
- premium product generation from the same core research base

---

## 20. MVP Recommendation

To reduce complexity, the first version should include:

- one subject only: Statistics or Machine Learning
- one topic queue
- one dossier format
- one episode template
- one short-form video template
- one long-form script template
- uploads to X and YouTube first
- TikTok after the pipeline is stable

This is the fastest path to a working system.

---

## 21. Definition of Done

A topic is complete only when all of the following are true:

- research dossier exists
- references are stored
- episode arc is approved
- scripts for all target platforms are generated
- citation checks pass
- media assets are rendered
- compliance checks pass
- content is uploaded or scheduled
- analytics logging is enabled

---

## 22. Immediate Next Steps

1. Finalize the initial syllabus scope for the first subject.
2. Define the database schema.
3. Write the Claude prompt pack:
   - Research Agent
   - Historian Agent
   - Story Architect Agent
   - Scriptwriter Agent
   - Citation Auditor Agent
   - Repurposing Agent
   - Compliance Agent
4. Build the dossier JSON schema.
5. Build the episode planning schema.
6. Build the first end-to-end workflow.
7. Test on one concept such as:
   - Bayes' theorem
   - variance
   - gradient descent
   - entropy
8. Refine based on actual outputs before scaling.

---

## 23. Suggested Directory Structure for Claude Code Project

```text
project/
  README.md
  docs/
    project-plan.md
    house-style.md
    prompt-pack.md
    syllabus.md
    data-model.md
    qa-rules.md
  prompts/
    research-agent.md
    historian-agent.md
    story-architect.md
    scriptwriter.md
    citation-auditor.md
    repurposer.md
    compliance-agent.md
  data/
    subjects.json
    modules.json
    topics.json
  schemas/
    research-dossier.schema.json
    episode-plan.schema.json
    script.schema.json
    publication-job.schema.json
  src/
    orchestrator/
    agents/
    retrieval/
    media/
    publishing/
    analytics/
  storage/
    sources/
    assets/
    renders/
  tests/
```

---

## 24. Final Operating Principle

The system should follow this rule:

> Research deeply. Write simply. Cite carefully. Publish consistently. Improve continuously.

And the editorial identity should remain:

> Tell the idea like a story. Teach the subject like a postgraduate course.
