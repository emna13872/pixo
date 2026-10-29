"""Secrets and service settings, read from the environment or from brain/.env.

brain/.env is never committed: copy brain/.env.example and fill it in.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

DEFAULT_ENV_FILE = Path(__file__).resolve().parents[1] / ".env"


def read_env_file(path: Path) -> dict[str, str]:
    """KEY=value lines; blank lines and # comments are skipped, quotes are stripped."""
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip("'\"")
    return values


@dataclass(frozen=True)
class Settings:
    livekit_url: str = ""
    livekit_api_key: str = ""
    livekit_api_secret: str = ""
    azure_speech_key: str = ""
    azure_speech_region: str = ""
    azure_speech_voice: str = "en-US-AnaNeural"

    @property
    def livekit_ready(self) -> bool:
        return bool(self.livekit_url and self.livekit_api_key and self.livekit_api_secret)

    @property
    def azure_ready(self) -> bool:
        return bool(self.azure_speech_key and self.azure_speech_region)


def load_settings(env_file: Path = DEFAULT_ENV_FILE) -> Settings:
    """The environment wins over the .env file, so CI and production can override it."""
    values = {**read_env_file(env_file), **os.environ}
    defaults = Settings()
    return Settings(
        livekit_url=values.get("LIVEKIT_URL", ""),
        livekit_api_key=values.get("LIVEKIT_API_KEY", ""),
        livekit_api_secret=values.get("LIVEKIT_API_SECRET", ""),
        azure_speech_key=values.get("AZURE_SPEECH_KEY", ""),
        azure_speech_region=values.get("AZURE_SPEECH_REGION", ""),
        azure_speech_voice=values.get("AZURE_SPEECH_VOICE") or defaults.azure_speech_voice,
    )
