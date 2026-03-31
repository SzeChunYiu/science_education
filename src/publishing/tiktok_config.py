from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


CONFIG_ENV = "SCIENCE_EDUCATION_TIKTOK_CONFIG_DIR"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "science_education" / "tiktok"
DEFAULT_CHROME_USER_DATA_DIR = Path.home() / "Library" / "Application Support" / "Google" / "Chrome"


@dataclass
class TikTokSettings:
    chrome_user_data_dir: str = str(DEFAULT_CHROME_USER_DATA_DIR)
    chrome_profile_directory: str = "Default"
    studio_url: str = "https://www.tiktok.com/tiktokstudio"
    upload_url: str = "https://www.tiktok.com/upload"
    profile_url: str = ""


def config_dir() -> Path:
    raw = os.environ.get(CONFIG_ENV)
    return Path(raw).expanduser() if raw else DEFAULT_CONFIG_DIR


def settings_path() -> Path:
    return config_dir() / "settings.json"


def ensure_config_dir() -> Path:
    path = config_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _inherit_youtube_chrome_defaults(settings: TikTokSettings) -> TikTokSettings:
    try:
        from .youtube_config import load_settings as load_youtube_settings
    except Exception:
        return settings

    try:
        youtube_settings = load_youtube_settings()
    except Exception:
        return settings

    if youtube_settings.chrome_user_data_dir and not settings.chrome_user_data_dir:
        settings.chrome_user_data_dir = youtube_settings.chrome_user_data_dir
    if youtube_settings.chrome_profile_directory and not settings.chrome_profile_directory:
        settings.chrome_profile_directory = youtube_settings.chrome_profile_directory
    return settings


def load_settings() -> TikTokSettings:
    path = settings_path()
    if not path.exists():
        settings = _inherit_youtube_chrome_defaults(TikTokSettings())
        save_settings(settings)
        return settings

    payload = json.loads(path.read_text())
    settings = TikTokSettings(**payload)
    if not settings.chrome_user_data_dir:
        settings.chrome_user_data_dir = str(DEFAULT_CHROME_USER_DATA_DIR)
    if not settings.chrome_profile_directory:
        settings.chrome_profile_directory = "Default"
    return _inherit_youtube_chrome_defaults(settings)


def save_settings(settings: TikTokSettings) -> None:
    ensure_config_dir()
    settings_path().write_text(json.dumps(asdict(settings), indent=2) + "\n")
