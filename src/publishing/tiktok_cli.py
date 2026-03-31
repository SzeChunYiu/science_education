from __future__ import annotations

import argparse

from .tiktok_config import TikTokSettings, load_settings, save_settings, settings_path
from .tiktok_web import launch_tiktok, page_note


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Shared TikTok Studio browser helper.")
    sub = parser.add_subparsers(dest="command", required=True)

    init_cmd = sub.add_parser("init", help="Configure shared TikTok browser settings.")
    init_cmd.add_argument("--chrome-user-data-dir", default=None, help="Shared Chrome user data dir.")
    init_cmd.add_argument("--chrome-profile-directory", default=None, help="Chrome profile directory, e.g. Default.")
    init_cmd.add_argument("--profile-url", default=None, help="Optional TikTok profile URL for the managed account.")

    sub.add_parser("status", help="Show current TikTok browser settings.")

    open_cmd = sub.add_parser("open", help="Open TikTok Studio/web in the shared Chrome profile.")
    open_cmd.add_argument(
        "--page",
        choices=["studio", "upload", "posts", "analytics", "comments", "inspiration", "settings"],
        default="studio",
    )

    return parser


def _cmd_init(args: argparse.Namespace) -> None:
    settings = load_settings()
    if args.chrome_user_data_dir:
        settings.chrome_user_data_dir = args.chrome_user_data_dir
    if args.chrome_profile_directory:
        settings.chrome_profile_directory = args.chrome_profile_directory
    if args.profile_url:
        settings.profile_url = args.profile_url
    save_settings(settings)
    print(f"Saved TikTok settings to {settings_path()}")


def _cmd_status(_: argparse.Namespace) -> None:
    settings = load_settings()
    print("TikTok browser settings")
    print(f"  config: {settings_path()}")
    print(f"  chrome_user_data_dir: {settings.chrome_user_data_dir}")
    print(f"  chrome_profile_directory: {settings.chrome_profile_directory}")
    print(f"  studio_url: {settings.studio_url}")
    print(f"  upload_url: {settings.upload_url}")
    if settings.profile_url:
        print(f"  profile_url: {settings.profile_url}")


def _cmd_open(args: argparse.Namespace) -> None:
    settings = load_settings()
    launch_tiktok(page=args.page, settings=settings)
    print(f"Opened TikTok {args.page} in the shared Chrome profile.")
    print(page_note(args.page))


def main() -> None:
    parser = _parser()
    args = parser.parse_args()

    handlers = {
        "init": _cmd_init,
        "status": _cmd_status,
        "open": _cmd_open,
    }
    handlers[args.command](args)


if __name__ == "__main__":
    main()
