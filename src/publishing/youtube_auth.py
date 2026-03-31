from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .youtube_config import YouTubeSettings, load_settings


DEFAULT_SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def _require_google_deps() -> None:
    try:
        import google.oauth2.credentials  # noqa: F401
        import google_auth_oauthlib.flow  # noqa: F401
        import google.auth.transport.requests  # noqa: F401
    except ModuleNotFoundError as exc:  # pragma: no cover - user environment
        raise RuntimeError(
            "Missing Google API dependencies. Install with:\n"
            "python3 -m pip install google-api-python-client "
            "google-auth-oauthlib google-auth-httplib2"
        ) from exc


@dataclass
class AuthSummary:
    token_path: Path
    channel_id: str


def authorize_interactively(
    scopes: Iterable[str] | None = None,
    settings: YouTubeSettings | None = None,
) -> AuthSummary:
    _require_google_deps()

    from google_auth_oauthlib.flow import InstalledAppFlow

    settings = settings or load_settings()
    if not settings.client_secrets_path:
        raise RuntimeError(
            "No OAuth client secrets configured. Run:\n"
            "python3 -m src.publishing.youtube_cli init "
            "--client-secrets /abs/path/client_secret.json"
        )

    token_path = Path(settings.token_path).expanduser()
    flow = InstalledAppFlow.from_client_secrets_file(
        settings.client_secrets_path,
        scopes=list(scopes or DEFAULT_SCOPES),
    )
    creds = flow.run_local_server(port=0)
    token_path.parent.mkdir(parents=True, exist_ok=True)
    token_path.write_text(creds.to_json())
    return AuthSummary(token_path=token_path, channel_id=settings.channel_id)


def load_credentials(
    scopes: Iterable[str] | None = None,
    settings: YouTubeSettings | None = None,
):
    _require_google_deps()

    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials

    settings = settings or load_settings()
    token_path = Path(settings.token_path).expanduser()

    if not token_path.exists():
        raise RuntimeError(
            f"Token file not found at {token_path}. Run:\n"
            "python3 -m src.publishing.youtube_cli auth"
        )

    creds = Credentials.from_authorized_user_file(
        str(token_path),
        scopes=list(scopes or DEFAULT_SCOPES),
    )

    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token_path.write_text(creds.to_json())

    if not creds.valid:
        raise RuntimeError(
            "Stored YouTube OAuth credentials are invalid. Re-run:\n"
            "python3 -m src.publishing.youtube_cli auth"
        )

    return creds
