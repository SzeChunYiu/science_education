from __future__ import annotations

import subprocess

from .tiktok_config import TikTokSettings


PAGE_URLS = {
    "studio": "https://www.tiktok.com/tiktokstudio",
    "upload": "https://www.tiktok.com/upload",
    "posts": "https://www.tiktok.com/tiktokstudio",
    "analytics": "https://www.tiktok.com/tiktokstudio",
    "comments": "https://www.tiktok.com/tiktokstudio",
    "inspiration": "https://www.tiktok.com/tiktokstudio",
    "settings": "https://www.tiktok.com/tiktokstudio",
}

PAGE_NOTES = {
    "studio": "Studio home is the main creator back office.",
    "upload": "Use browser upload for posting prepared videos.",
    "posts": "Open Studio, then use the Posts sidebar section.",
    "analytics": "Open Studio, then use the Analytics sidebar section.",
    "comments": "Open Studio, then use Posts -> View analytics for comment insights.",
    "inspiration": "Open Studio, then use the Inspiration sidebar section if available on the account.",
    "settings": "Open Studio, click the profile image, then open Settings.",
}


def page_url(page: str, settings: TikTokSettings) -> str:
    if page == "studio":
        return settings.studio_url
    if page == "upload":
        return settings.upload_url
    return PAGE_URLS[page]


def page_note(page: str) -> str:
    return PAGE_NOTES[page]


def launch_tiktok(page: str, settings: TikTokSettings) -> None:
    url = page_url(page, settings)
    command = ["open", "-na", "Google Chrome", "--args"]
    if settings.chrome_user_data_dir:
        command.append(f"--user-data-dir={settings.chrome_user_data_dir}")
    if settings.chrome_profile_directory:
        command.append(f"--profile-directory={settings.chrome_profile_directory}")
    command.append(url)
    subprocess.Popen(command)
