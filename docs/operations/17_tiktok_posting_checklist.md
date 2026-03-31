# 17. TikTok Posting Checklist

Use this checklist when posting through the TikTok website or TikTok Studio.

---

## Before Upload

- confirm the video is the correct final export
- confirm the first `1-2s` contain the hook
- confirm subtitles are readable on a phone screen
- confirm the video is vertical if intended for TikTok-first publishing
- confirm the science is still accurate after compression

---

## Metadata

- write a short caption with one strong idea
- avoid overloading the caption with too many concepts
- keep hashtags focused and limited
- set the intended visibility correctly
- decide whether comments, duet, and stitch should be enabled

---

## In TikTok Studio / Web

1. Open the upload surface:

```bash
cd /Users/billy/Desktop/projects/science_education
python3 -m src.publishing.tiktok_cli open --page upload
```

2. Upload the video file.
3. Review preview, caption, visibility, and interaction settings.
4. Publish only after final review.

---

## After Posting

- confirm the post is visible on the correct account
- open Studio to review the new post
- note the publish time
- return later to inspect analytics and comment insights

Open Studio:

```bash
python3 -m src.publishing.tiktok_cli open --page studio
```

Open comments/analytics workspace:

```bash
python3 -m src.publishing.tiktok_cli open --page comments
python3 -m src.publishing.tiktok_cli open --page analytics
```
