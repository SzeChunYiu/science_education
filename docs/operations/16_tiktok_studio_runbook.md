# 16. TikTok Studio Runbook

This runbook documents the current browser-assisted TikTok operating model for this project.

TikTok is not as automation-friendly as YouTube for the exact "shared internal uploader" use case. For this project, TikTok Studio should be treated as the main operating surface for uploads, post management, and backstage performance review.

Related docs:

- `14_end_to_end_pipeline_runbook.md`
- `15_social_media_operations_playbook.md`
- `../foundation/09_media_and_publishing.md`
- `src/publishing/tiktok_cli.py`

---

## What TikTok Studio Is

TikTok officially describes TikTok Studio as a content creation and management environment for creators to:

- grow their accounts
- manage their content
- get insights into performance

TikTok says Studio is available:

- as a standalone app
- with limited creator tools in the TikTok app
- in a web browser

For this project, the web browser version is the most important operating surface.

Official source:

- `https://support.tiktok.com/en/using-tiktok/creating-videos/tiktok-studio/`

---

## Why Studio Matters For This Project

Inference from TikTok's official product design:

- Studio is the closest thing to a unified creator back office on TikTok
- it is where browser-assisted posting and post-level review can be coordinated
- it is the correct place to inspect account performance and individual post performance without relying on unofficial automation

That makes TikTok Studio the practical counterpart to YouTube Studio in this repo.

---

## Studio Areas Future Sessions Should Know

TikTok's official help page lists these main Studio areas:

### Home

Used for inspiration and trend discovery:

- `Trending`
- `Inspiration`

TikTok says these feeds can surface content by region and topic, and can show inspiration plus performance signals for ideas.

### Analytics

Used to inspect account and post performance.

Officially listed analytics areas:

- account overview
- content analytics
- viewer metrics, demographics, and activity times
- follower demographics and follower insights
- video analytics overview
- video viewer metrics
- engagement analytics
- comment insights

### Create

Used for browser/app-side creation and upload workflow.

Officially listed creation features:

- auto captions
- photo editor
- AutoCut
- camera
- upload

Important behavior:

- if you upload or delete in TikTok Studio, that action also applies to TikTok
- post setting changes apply across TikTok and TikTok Studio

### Monetize

Used to inspect monetization state and rewards where eligible.

Officially listed monetization surfaces:

- estimated rewards
- balance
- rewards analytics
- programs for you
- active programs
- monetization trends/resources

### Manage

Used for post and comment operations.

Officially listed management functions:

- search/filter/sort posts
- see post metrics such as views, likes, and shares
- adjust privacy settings
- delete posts
- delete/like/dislike/reply to comments

### Inbox

Used for creator/account notifications.

Officially listed notification types:

- creator notifications
- account notifications
- notification settings

Important limitation:

- direct messaging is not available in TikTok Studio

---

## Browser Access

TikTok officially documents web browser access for both posting and Studio analytics/comment insights.

Relevant web entry points:

- `https://www.tiktok.com/tiktokstudio`
- `https://www.tiktok.com/upload`

Project helper commands:

```bash
cd /Users/billy/Desktop/projects/science_education
python3 -m src.publishing.tiktok_cli status
python3 -m src.publishing.tiktok_cli open --page studio
python3 -m src.publishing.tiktok_cli open --page upload
python3 -m src.publishing.tiktok_cli open --page analytics
python3 -m src.publishing.tiktok_cli open --page posts
python3 -m src.publishing.tiktok_cli open --page comments
```

Official support also says browser upload will upload the entire selected video. If length changes are needed, TikTok says to upload in the app instead.

Source:

- `https://support.tiktok.com/en/using-tiktok/creating-videos/making-a-post`

---

## Backstage Information Available In Studio

From TikTok's official help pages, Studio gives access to backstage information in at least these categories:

- account-level overview metrics
- post-level analytics
- viewer metrics
- follower demographics
- viewer activity times
- engagement data
- comment insights
- monetization/reward analytics where available
- creator/account notifications

Comment insights are especially useful for editorial iteration. TikTok says comment insights can:

- summarize frequently discussed topics
- surface audience suggestions
- identify positive sentiment or viewer questions
- help decide which comments and viewers to engage with

TikTok also says comment insights can be viewed:

- in the TikTok app
- in the TikTok Studio app
- in a web browser via TikTok Studio

Official source:

- `https://support.tiktok.com/en/using-tiktok/growing-your-audience/comment-insights-on-tiktok`

---

## Discovery And Ideation Signals

TikTok also offers Creator Search Insights, which is relevant for topic selection and packaging.

TikTok says Creator Search Insights provides:

- personalized information on what people are searching for
- popular search topics
- topics that may be underserved by existing content

This is useful for:

- choosing future episode topics
- shaping hooks and titles
- identifying concepts with strong search demand

Official source:

- `https://support.tiktok.com/en/using-tiktok/growing-your-audience/creator-search-insights`

---

## Recommended Operational Model For This Repo

For now, future sessions should treat TikTok like this:

1. Prepare the media and metadata locally in the repo.
2. Use TikTok Studio in the browser as the publication and review surface.
3. Use Studio analytics, comment insights, and search insights to refine later content.
4. Avoid relying on TikTok API posting for the internal shared-uploader use case unless policy/compliance is revisited.

This is the pragmatic route because TikTok's official developer rules are stricter than YouTube's for internal posting tools.

---

## Posting Workflow Through Studio Or Web

Baseline workflow:

1. Confirm the video is TikTok-ready.
2. Open TikTok Studio or the TikTok upload page in the logged-in browser session.
3. Upload the file.
4. Set caption, hashtags, privacy, and interaction settings.
5. Publish or save as draft if available in the current flow.
6. Recheck the post inside Studio.
7. Return later to review performance and comment insights.

Important privacy note:

TikTok allows per-post visibility such as public, friends, or private, depending on account state and eligibility.

Official privacy source:

- `https://support.tiktok.com/en/account-and-privacy/account-privacy-settings/video-visibility`

---

## What Future Sessions Should Inspect In Studio

When evaluating post performance, check:

- views
- likes
- shares
- comment volume and themes
- follower growth effects
- viewer activity times
- which topics get stronger engagement

When inspecting individual posts, pay attention to:

- whether the hook attracted comments/questions
- whether viewers misunderstood the science
- whether the post should be expanded into long-form YouTube content

---

## Current Project Position

Current state of this project:

- YouTube has working auth and upload tooling
- TikTok now has a shared browser helper CLI for Studio/web access
- TikTok does not yet have equivalent direct upload automation
- TikTok should currently be treated as a browser-assisted platform

So the next sensible TikTok work items are:

1. Add a shared TikTok posting checklist and metadata template.
2. Expand the helper command set if TikTok Studio web flows become more stable.
3. Add a manual analytics logging format for TikTok posts.
4. If needed, later evaluate whether a compliant TikTok API integration is worth pursuing.
