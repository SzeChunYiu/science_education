from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path


CONFIG_ENV = "SCIENCE_EDUCATION_YOUTUBE_CONFIG_DIR"
DEFAULT_CONFIG_DIR = Path.home() / ".config" / "science_education" / "youtube"


@dataclass
class YouTubeSettings:
    client_secrets_path: str = ""
    token_path: str = ""
    channel_id: str = ""
    chrome_user_data_dir: str = ""
    chrome_profile_directory: str = "Default"


def config_dir() -> Path:
    raw = os.environ.get(CONFIG_ENV)
    return Path(raw).expanduser() if raw else DEFAULT_CONFIG_DIR


def settings_path() -> Path:
    return config_dir() / "settings.json"


def default_token_path() -> Path:
    return config_dir() / "oauth_token.json"


def ensure_config_dir() -> Path:
    path = config_dir()
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_settings() -> YouTubeSettings:
    path = settings_path()
    if not path.exists():
        settings = YouTubeSettings(token_path=str(default_token_path()))
        save_settings(settings)
        return settings

    payload = json.loads(path.read_text())
    settings = YouTubeSettings(**payload)
    if not settings.token_path:
        settings.token_path = str(default_token_path())
    return settings


def save_settings(settings: YouTubeSettings) -> None:
    ensure_config_dir()
    path = settings_path()
    path.write_text(json.dumps(asdict(settings), indent=2) + "\n")
