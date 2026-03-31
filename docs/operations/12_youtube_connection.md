# 12. YouTube Connection, Uploads, Studio Access, and Analytics

This project now includes a shared YouTube integration layer under:

- `src/publishing/youtube_cli.py`
- `src/publishing/youtube_auth.py`
- `src/publishing/youtube_api.py`
- `src/publishing/youtube_config.py`

The goal is simple:

- one OAuth connection for the machine
- reusable by future agent sessions
- API-based uploads and analytics
- shared browser profile for Studio-only actions like Community posts

Operational handoff for future sessions lives in:

- `13_youtube_operations_runbook.md`

---

## What Is Supported

### API-backed

- upload long-form videos
- upload Shorts (Shorts are still normal video uploads; the main content requirement is format, not a separate upload API)
- set thumbnails
- fetch authenticated channel metadata
- fetch channel analytics summary
- fetch top-video analytics reports

### Browser-backed

YouTube Studio actions that are not cleanly exposed through the public API should use the shared Chrome profile:

- Community posts
- Studio-only dashboard review
- manual checks on comments, monetization, or experiments

---

## Important API Reality

Use the API where Google supports it, and Studio/browser automation where it does not.

- Video upload is officially supported through `videos.insert`.
- Analytics is officially supported through the YouTube Analytics API.
- The public YouTube Data API reference does not expose a first-class Community-post creation method. For those actions, use Studio in the shared Chrome profile.

---

## One-Time Setup

### 1. Install Google client libraries

```bash
python3 -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2
```

### 2. Create a Google Cloud OAuth client

In Google Cloud Console:

- create one project for this publishing client
- enable:
  - YouTube Data API v3
  - YouTube Analytics API
- create an OAuth client for a Desktop app
- download the OAuth client JSON

### 3. Initialize the shared config

```bash
python3 -m src.publishing.youtube_cli init \
  --client-secrets /ABS/PATH/client_secret.json \
  --chrome-user-data-dir "/Users/billy/Library/Application Support/Google/Chrome" \
  --chrome-profile-directory Default
```

This writes shared settings to:

```text
~/.config/science_education/youtube/settings.json
```

### 4. Authorize the YouTube account

```bash
python3 -m src.publishing.youtube_cli auth
```

This stores a reusable OAuth token at:

```text
~/.config/science_education/youtube/oauth_token.json
```

Any future local session/agent on this machine can reuse that token.

### 5. Sync the channel ID

```bash
python3 -m src.publishing.youtube_cli channel
```

That also stores the authenticated channel ID in shared settings.

---

## Example Commands

### Upload a long-form video

```bash
python3 -m src.publishing.youtube_cli upload-video \
  --file /abs/path/video.mp4 \
  --title "The Ultraviolet Catastrophe" \
  --description "..." \
  --privacy private \
  --tags physics,quantum,blackbody \
  --thumbnail /abs/path/thumb.png
```

### Upload a scheduled video

```bash
python3 -m src.publishing.youtube_cli upload-video \
  --file /abs/path/video.mp4 \
  --title "..." \
  --description "..." \
  --privacy private \
  --publish-at 2026-04-05T09:00:00Z
```

### Pull a channel summary report

```bash
python3 -m src.publishing.youtube_cli analytics-summary \
  --start-date 2026-03-01 \
  --end-date 2026-03-31 \
  --csv /abs/path/march_channel_summary.csv
```

### Pull top videos for a period

```bash
python3 -m src.publishing.youtube_cli analytics-top-videos \
  --start-date 2026-03-01 \
  --end-date 2026-03-31 \
  --max-results 20 \
  --csv /abs/path/march_top_videos.csv
```

### Open Studio in the shared Chrome profile

```bash
python3 -m src.publishing.youtube_cli studio-open --page analytics
python3 -m src.publishing.youtube_cli studio-open --page content
python3 -m src.publishing.youtube_cli studio-open --page posts
```

---

## Shared-Credential Policy

These credentials are for agents/sessions operating solely on the owner's behalf on this machine. Do not commit:

- `client_secret.json`
- `oauth_token.json`
- the contents of `~/.config/science_education/youtube/`

---

## How Future Sessions Should Use This

1. Use API commands first for uploads and analytics.
2. Use the shared Chrome profile for Studio-only actions.
3. Keep all auth state in the shared config dir, not in ad hoc temp files.
4. Treat the channel as a single managed publishing client.
5. Read `13_youtube_operations_runbook.md` before making live channel changes.
