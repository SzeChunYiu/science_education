# 13. YouTube Operations Runbook

This document is the handoff note for future sessions that need to operate the connected YouTube channel from this machine.

Use this together with:

- `12_youtube_connection.md` for setup and command reference
- `src/publishing/youtube_cli.py` for the actual CLI entrypoint

---

## Current Machine State

As of `2026-03-30`, the shared YouTube connection is already established on this machine.

Connected channel:

- channel title: `S Y`
- handle: `@billyyiu8140`
- channel ID: `UChY6fOmTBglrNnG8553_qOQ`

Verified working:

- OAuth browser auth
- reusable token save
- channel lookup
- private video upload

Test upload already completed:

- video title: `YouTube Connection Test - 2026-03-30`
- video ID: `3kiNYnPWFoU`
- URL: `https://www.youtube.com/watch?v=3kiNYnPWFoU`
- privacy: `private`

Known limitation at handoff:

- `analytics-summary` and `analytics-top-videos` currently authenticate successfully but the YouTube Analytics API returned HTTP `500 internalError` on `2026-03-30`

---

## Shared Auth And Config Paths

Project-local secret:

- OAuth client JSON: `/Users/billy/Desktop/projects/science_education/.secrets/youtube/client_secret.json`

Machine-level shared config:

- settings: `/Users/billy/.config/science_education/youtube/settings.json`
- token: `/Users/billy/.config/science_education/youtube/oauth_token.json`

Current Chrome Studio profile:

- user data dir: `/Users/billy/Library/Application Support/Google/Chrome`
- profile directory: `Default`

These paths are intentionally reusable across future sessions on the same machine.

---

## Default Operating Policy

Future sessions should assume:

1. Uploads default to `private`.
2. Do not publish anything `public` without explicit instruction.
3. Do not replace channel branding, name, or handle without explicit instruction.
4. Prefer API operations first.
5. Use YouTube Studio in the shared Chrome profile for actions that are not cleanly supported by the API.

This keeps the channel usable by multiple sessions without accidental public changes.

---

## Fast Start Checklist

From `/Users/billy/Desktop/projects/science_education`:

1. Confirm the channel connection:

```bash
python3 -m src.publishing.youtube_cli channel
```

2. If token problems appear, re-run auth:

```bash
python3 -m src.publishing.youtube_cli auth
```

3. Upload a video privately:

```bash
python3 -m src.publishing.youtube_cli upload-video \
  --file /ABS/PATH/video.mp4 \
  --title "Video Title" \
  --description "Video description" \
  --privacy private
```

4. Open Studio manually if needed:

```bash
python3 -m src.publishing.youtube_cli studio-open --page home
python3 -m src.publishing.youtube_cli studio-open --page content
python3 -m src.publishing.youtube_cli studio-open --page analytics
```

---

## Standard Upload Workflow

For normal production uploads, use this sequence:

1. Validate the local media file exists.
2. Prepare title, description, tags, thumbnail, and intended privacy.
3. Upload as `private`.
4. Confirm returned `video id`, `privacyStatus`, and `uploadStatus`.
5. Open Studio if manual review is needed.
6. Only switch to `unlisted` or `public` after explicit confirmation.

Recommended metadata minimum:

- title with one clear promise, not stuffed with keywords
- first two description lines that explain the value of the video
- source/reference section for science videos
- 3 to 8 focused tags, not a giant tag dump

---

## Known Commands

Show channel and sync channel ID:

```bash
python3 -m src.publishing.youtube_cli channel
```

Upload video:

```bash
python3 -m src.publishing.youtube_cli upload-video \
  --file /ABS/PATH/video.mp4 \
  --title "Title" \
  --description "Description" \
  --privacy private \
  --tags physics,science,education
```

Upload with thumbnail:

```bash
python3 -m src.publishing.youtube_cli upload-video \
  --file /ABS/PATH/video.mp4 \
  --title "Title" \
  --description "Description" \
  --privacy private \
  --thumbnail /ABS/PATH/thumbnail.png
```

Open Studio:

```bash
python3 -m src.publishing.youtube_cli studio-open --page home
python3 -m src.publishing.youtube_cli studio-open --page content
python3 -m src.publishing.youtube_cli studio-open --page analytics
python3 -m src.publishing.youtube_cli studio-open --page posts
```

Try analytics:

```bash
python3 -m src.publishing.youtube_cli analytics-summary \
  --start-date 2026-03-01 \
  --end-date 2026-03-30
```

```bash
python3 -m src.publishing.youtube_cli analytics-top-videos \
  --start-date 2026-03-01 \
  --end-date 2026-03-30
```

---

## Failure Modes

If `channel` fails:

- token may be missing, expired, or revoked
- rerun `python3 -m src.publishing.youtube_cli auth`

If upload fails:

- check the local file path first
- confirm the authenticated channel is still correct
- check whether the token was revoked

If analytics fails with HTTP `500`:

- treat it as an upstream/API issue first
- retry later
- confirm the same token still works for `channel` and `upload-video`

If Studio opens but shows the wrong account:

- the shared Chrome profile may have multiple signed-in Google accounts
- verify the active YouTube account in Studio before making profile or publish changes

---

## Security And Git Hygiene

Do not commit any of the following:

- `.secrets/youtube/client_secret.json`
- `~/.config/science_education/youtube/oauth_token.json`
- any exported token JSON

Do not paste OAuth client secrets or tokens into markdown docs, issues, or commits.

If credentials are suspected to be exposed:

1. revoke the token in Google account security settings
2. rotate the OAuth client secret if needed
3. rerun auth locally

---

## Current Improvement Backlog

These are sensible next improvements for future sessions:

1. Add a metadata template generator for title, description, and tags from episode scripts.
2. Add batch upload support from manifest files.
3. Add safer publish-state transitions such as `private -> unlisted -> public`.
4. Investigate the analytics API `500 internalError` and add retry/backoff handling.
5. Add explicit profile-management scripts only where the API cleanly supports them.
