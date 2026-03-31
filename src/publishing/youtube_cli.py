from __future__ import annotations

import argparse
from pathlib import Path

from .youtube_api import (
    channel_summary_report,
    fetch_own_channel,
    launch_studio,
    print_json,
    sync_channel_id,
    top_videos_report,
    upload_video,
    write_report_csv,
    UploadRequest,
)
from .youtube_auth import authorize_interactively
from .youtube_config import YouTubeSettings, load_settings, save_settings


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared YouTube management CLI.")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Configure shared YouTube settings.")
    init_cmd.add_argument("--client-secrets", type=Path, help="Path to Google OAuth client secret JSON.")
    init_cmd.add_argument("--channel-id", help="YouTube channel ID.")
    init_cmd.add_argument("--chrome-user-data-dir", help="Shared Chrome user data dir for Studio actions.")
    init_cmd.add_argument("--chrome-profile-directory", default=None, help="Chrome profile directory name, e.g. Default.")

    sub.add_parser("auth", help="Run OAuth browser flow and cache reusable token.")
    sub.add_parser("channel", help="Show authenticated channel info and sync channel ID.")

    upload_cmd = sub.add_parser("upload-video", help="Upload a video or Short.")
    upload_cmd.add_argument("--file", type=Path, required=True)
    upload_cmd.add_argument("--title", required=True)
    upload_cmd.add_argument("--description", required=True)
    upload_cmd.add_argument("--category-id", default="27")
    upload_cmd.add_argument("--privacy", default="private", choices=["private", "unlisted", "public"])
    upload_cmd.add_argument("--tags", default="")
    upload_cmd.add_argument("--publish-at", default=None)
    upload_cmd.add_argument("--thumbnail", type=Path, default=None)
    upload_cmd.add_argument("--notify-subscribers", action="store_true")
    upload_cmd.add_argument("--made-for-kids", action="store_true")

    analytics_cmd = sub.add_parser("analytics-summary", help="Fetch channel analytics summary.")
    analytics_cmd.add_argument("--start-date", required=True)
    analytics_cmd.add_argument("--end-date", required=True)
    analytics_cmd.add_argument("--csv", type=Path, default=None)

    top_cmd = sub.add_parser("analytics-top-videos", help="Fetch top videos report.")
    top_cmd.add_argument("--start-date", required=True)
    top_cmd.add_argument("--end-date", required=True)
    top_cmd.add_argument("--max-results", type=int, default=10)
    top_cmd.add_argument("--csv", type=Path, default=None)

    studio_cmd = sub.add_parser("studio-open", help="Open YouTube Studio in the shared Chrome profile.")
    studio_cmd.add_argument("--page", choices=["home", "analytics", "content", "posts"], default="home")

    return parser


def _cmd_init(args: argparse.Namespace) -> None:
    settings = load_settings()
    if args.client_secrets:
        settings.client_secrets_path = str(args.client_secrets.expanduser().resolve())
    if args.channel_id:
        settings.channel_id = args.channel_id
    if args.chrome_user_data_dir:
        settings.chrome_user_data_dir = args.chrome_user_data_dir
    if args.chrome_profile_directory:
        settings.chrome_profile_directory = args.chrome_profile_directory
    save_settings(settings)
    print("Saved YouTube settings to shared config.")


def _cmd_auth(_: argparse.Namespace) -> None:
    summary = authorize_interactively()
    print(f"Saved reusable OAuth token to {summary.token_path}")


def _cmd_channel(_: argparse.Namespace) -> None:
    channel = fetch_own_channel()
    sync_channel_id()
    print_json(channel)


def _cmd_upload_video(args: argparse.Namespace) -> None:
    request = UploadRequest(
        file_path=args.file.expanduser().resolve(),
        title=args.title,
        description=args.description,
        category_id=args.category_id,
        privacy_status=args.privacy,
        tags=[tag.strip() for tag in args.tags.split(",") if tag.strip()],
        publish_at=args.publish_at,
        thumbnail_path=args.thumbnail.expanduser().resolve() if args.thumbnail else None,
        notify_subscribers=args.notify_subscribers,
        made_for_kids=args.made_for_kids,
    )
    response = upload_video(request)
    print_json(response)


def _cmd_analytics_summary(args: argparse.Namespace) -> None:
    report = channel_summary_report(args.start_date, args.end_date)
    if args.csv:
        write_report_csv(report, args.csv.expanduser().resolve())
    print_json(report)


def _cmd_analytics_top_videos(args: argparse.Namespace) -> None:
    report = top_videos_report(args.start_date, args.end_date, max_results=args.max_results)
    if args.csv:
        write_report_csv(report, args.csv.expanduser().resolve())
    print_json(report)


def _cmd_studio_open(args: argparse.Namespace) -> None:
    settings = load_settings()
    if not settings.chrome_user_data_dir:
        raise SystemExit(
            "No shared Chrome profile configured. Run:\n"
            "python3 -m src.publishing.youtube_cli init "
            "--chrome-user-data-dir '/Users/you/Library/Application Support/Google/Chrome' "
            "--chrome-profile-directory Default"
        )
    launch_studio(page=args.page, settings=settings)
    print(f"Opened YouTube Studio ({args.page}) in the shared Chrome profile.")


def main() -> None:
    parser = _parser()
    args = parser.parse_args()

    handlers = {
        "init": _cmd_init,
        "auth": _cmd_auth,
        "channel": _cmd_channel,
        "upload-video": _cmd_upload_video,
        "analytics-summary": _cmd_analytics_summary,
        "analytics-top-videos": _cmd_analytics_top_videos,
        "studio-open": _cmd_studio_open,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
