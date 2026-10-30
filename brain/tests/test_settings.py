from __future__ import annotations

from pixo_brain.settings import load_settings, read_env_file


def test_env_file_is_read(tmp_path, monkeypatch):
    for key in ("LIVEKIT_URL", "LIVEKIT_API_KEY", "LIVEKIT_API_SECRET", "AZURE_SPEECH_VOICE"):
        monkeypatch.delenv(key, raising=False)
    env = tmp_path / ".env"
    env.write_text(
        "# comment\nLIVEKIT_URL='wss://x'\nLIVEKIT_API_KEY=k\nLIVEKIT_API_SECRET=s\n\nnot a line\n",
        encoding="utf-8",
    )
    assert read_env_file(env)["LIVEKIT_URL"] == "wss://x"
    settings = load_settings(env)
    assert settings.livekit_ready and not settings.azure_ready
    assert settings.azure_speech_voice == "en-US-AnaNeural"


def test_environment_wins_over_file(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("LIVEKIT_URL=wss://file\n", encoding="utf-8")
    monkeypatch.setenv("LIVEKIT_URL", "wss://env")
    assert load_settings(env).livekit_url == "wss://env"


def test_missing_file_gives_empty_settings(tmp_path, monkeypatch):
    monkeypatch.delenv("LIVEKIT_URL", raising=False)
    assert load_settings(tmp_path / "nope").livekit_url == ""
