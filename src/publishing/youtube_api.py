from __future__ import annotations

import csv
import json
import mimetypes
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .youtube_auth import DEFAULT_SCOPES, load_credentials
from .youtube_config import YouTubeSettings, load_settings, save_settings


def _require_google_api_client() -> None:
    try:
        import googleapiclient.discovery  # noqa: F401
        import googleapiclient.http  # noqa: F401
    except ModuleNotFoundError as exc:  # pragma: no cover - user environment
        raise RuntimeError(
            "Missing Google API client libraries. Install with:\n"
            "python3 -m pip install google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        ) from exc


def youtube_service(settings: YouTubeSettings | None = None):
    _require_google_api_client()
    from googleapiclient.discovery import build

    creds = load_credentials(DEFAULT_SCOPES, settings=settings)
    return build("youtube", "v3", credentials=creds)


def youtube_analytics_service(settings: YouTubeSettings | None = None):
    _require_google_api_client()
    from googleapiclient.discovery import build

    creds = load_credentials(DEFAULT_SCOPES, settings=settings)
    return build("youtubeAnalytics", "v2", credentials=creds)


@dataclass
class UploadRequest:
    file_path: Path
    title: str
    description: str
    category_id: str = "27"
    privacy_status: str = "private"
    tags: list[str] | None = None
    publish_at: str | None = None
    thumbnail_path: Path | None = None
    notify_subscribers: bool = False
    made_for_kids: bool = False


def upload_video(request: UploadRequest, settings: YouTubeSettings | None = None) -> dict[str, Any]:
    _require_google_api_client()
    from googleapiclient.http import MediaFileUpload

    service = youtube_service(settings)
    mime_type = mimetypes.guess_type(str(request.file_path))[0] or "application/octet-stream"

    body: dict[str, Any] = {
        "snippet": {
            "title": request.title,
            "description": request.description,
            "categoryId": request.category_id,
        },
        "status": {
            "privacyStatus": request.privacy_status,
            "selfDeclaredMadeForKids": request.made_for_kids,
        },
    }
    if request.tags:
        body["snippet"]["tags"] = request.tags
    if request.publish_at:
        body["status"]["publishAt"] = request.publish_at

    media = MediaFileUpload(
        str(request.file_path),
        mimetype=mime_type,
        chunksize=-1,
        resumable=True,
    )
    response = (
        service.videos()
        .insert(
            part="snippet,status",
            body=body,
            notifySubscribers=request.notify_subscribers,
            media_body=media,
        )
        .execute()
    )

    if request.thumbnail_path:
        set_thumbnail(response["id"], request.thumbnail_path, settings=settings)

    return response


def set_thumbnail(video_id: str, image_path: Path, settings: YouTubeSettings | None = None) -> dict[str, Any]:
    _require_google_api_client()
    from googleapiclient.http import MediaFileUpload

    service = youtube_service(settings)
    mime_type = mimetypes.guess_type(str(image_path))[0] or "application/octet-stream"
    media = MediaFileUpload(str(image_path), mimetype=mime_type, resumable=False)
    return service.thumbnails().set(videoId=video_id, media_body=media).execute()


def fetch_own_channel(settings: YouTubeSettings | None = None) -> dict[str, Any]:
    service = youtube_service(settings)
    response = service.channels().list(part="id,snippet,statistics,contentDetails", mine=True).execute()
    items = response.get("items", [])
    if not items:
        raise RuntimeError("No authenticated YouTube channel found for the current credentials.")
    return items[0]


def sync_channel_id(settings: YouTubeSettings | None = None) -> str:
    settings = settings or load_settings()
    channel = fetch_own_channel(settings)
    settings.channel_id = channel["id"]
    save_settings(settings)
    return channel["id"]


def channel_summary_report(
    start_date: str,
    end_date: str,
    settings: YouTubeSettings | None = None,
) -> dict[str, Any]:
    analytics = youtube_analytics_service(settings)
    return (
        analytics.reports()
        .query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics=(
                "views,estimatedMinutesWatched,averageViewDuration,"
                "subscribersGained,subscribersLost,likes,comments,shares"
            ),
        )
        .execute()
    )


def top_videos_report(
    start_date: str,
    end_date: str,
    max_results: int = 10,
    settings: YouTubeSettings | None = None,
) -> dict[str, Any]:
    analytics = youtube_analytics_service(settings)
    return (
        analytics.reports()
        .query(
            ids="channel==MINE",
            startDate=start_date,
            endDate=end_date,
            metrics="views,estimatedMinutesWatched,averageViewDuration,likes,comments,shares",
            dimensions="video",
            sort="-views",
            maxResults=max_results,
        )
        .execute()
    )


def write_report_csv(report: dict[str, Any], destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    columns = [item["name"] for item in report.get("columnHeaders", [])]
    rows = report.get("rows", [])

    with destination.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)


def launch_studio(page: str = "home", settings: YouTubeSettings | None = None) -> None:
    settings = settings or load_settings()

    url = "https://studio.youtube.com/"
    channel_id = settings.channel_id
    if page == "analytics" and channel_id:
        url = f"https://studio.youtube.com/channel/{channel_id}/analytics/tab-overview/period-default"
    elif page == "content" and channel_id:
        url = f"https://studio.youtube.com/channel/{channel_id}/videos/upload?d=ud"
    elif page == "posts":
        url = "https://studio.youtube.com/"

    command = ["open", "-na", "Google Chrome", "--args"]
    if settings.chrome_user_data_dir:
        command.append(f"--user-data-dir={settings.chrome_user_data_dir}")
    if settings.chrome_profile_directory:
        command.append(f"--profile-directory={settings.chrome_profile_directory}")
    command.append(url)
    subprocess.Popen(command)


def print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, indent=2, sort_keys=True))
