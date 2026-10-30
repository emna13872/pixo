"""Pixo's natural voice: Azure neural text-to-speech, made by the brain, played by the app.

Each line is made once and kept as an MP3 in the voice cache (named after the voice, speed and
text), so a session replays from disk. Without an Azure key, or if Azure fails, `say` carries no
audio and the app falls back to the phone's own voice.

Usage (from the brain/ folder), to hear the candidate voices before choosing one:
    uv run pixo-voice-samples              # writes ../notes/voice-samples/<voice>.mp3
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import logging
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from pathlib import Path
from xml.sax.saxutils import escape

from .settings import Settings, load_settings

log = logging.getLogger("pixo.voice")

OUTPUT_FORMAT = "audio-24khz-48kbitrate-mono-mp3"
RATE = "-10%"  # the pedagogy rules ask for a slow, clear pace
SLOW_RATE = "-40%"  # rulebook: after a first miss, the word is modelled slowly
TIMEOUT_S = 10

# Voices to compare (American English unless noted); Ana and Maisie are child voices.
CANDIDATES = (
    "en-US-AnaNeural",
    "en-GB-MaisieNeural",
    "en-US-JennyNeural",
    "en-US-AriaNeural",
    "en-US-EmmaNeural",
    "en-US-AvaNeural",
)
SAMPLE = "Hello, friend! I'm Pixo. Can you say hello? Hello! Yes! Great job!"

Fetch = Callable[[str, dict[str, str], bytes], bytes]


def ssml(text: str, voice: str, rate: str) -> str:
    lang = "-".join(voice.split("-")[:2])
    return (
        f"<speak version='1.0' xml:lang='{lang}'><voice name='{voice}'>"
        f"<prosody rate='{rate}'>{escape(text)}</prosody></voice></speak>"
    )


def http_fetch(url: str, headers: dict[str, str], body: bytes) -> bytes:
    request = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=TIMEOUT_S) as response:
        return response.read()


class AzureVoice:
    def __init__(
        self,
        key: str,
        region: str,
        voice: str,
        cache: Path,
        fetch: Fetch = http_fetch,
    ) -> None:
        self.url = f"https://{region}.tts.speech.microsoft.com/cognitiveservices/v1"
        self.key = key
        self.voice = voice
        self.cache = cache
        self.fetch = fetch
        cache.mkdir(parents=True, exist_ok=True)

    @classmethod
    def from_settings(cls, settings: Settings, cache: Path) -> AzureVoice | None:
        if not settings.azure_ready:
            return None
        return cls(
            settings.azure_speech_key,
            settings.azure_speech_region,
            settings.azure_speech_voice,
            cache,
        )

    def synthesize(self, text: str, voice: str, rate: str) -> bytes:
        headers = {
            "Ocp-Apim-Subscription-Key": self.key,
            "Content-Type": "application/ssml+xml",
            "X-Microsoft-OutputFormat": OUTPUT_FORMAT,
            "User-Agent": "pixo-brain",
        }
        return self.fetch(self.url, headers, ssml(text, voice, rate).encode("utf-8"))

    async def audio(self, text: str, slow: bool = False) -> str:
        """The cached MP3's file name for this line, made first if needed; "" if Azure fails."""
        rate = SLOW_RATE if slow else RATE
        digest = hashlib.sha1(f"{self.voice}|{rate}|{text}".encode()).hexdigest()[:16]
        name = f"{digest}.mp3"
        path = self.cache / name
        if path.exists():
            return name
        try:
            data = await asyncio.to_thread(self.synthesize, text, self.voice, rate)
        except (urllib.error.URLError, OSError) as err:
            log.warning("Azure voice failed for %r: %s", text, err)
            return ""
        tmp = path.with_suffix(".part")
        tmp.write_bytes(data)
        tmp.replace(path)
        return name


def samples(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Make one sample per candidate voice.")
    parser.add_argument("--out", type=Path, default=Path("../notes/voice-samples"))
    parser.add_argument("--text", default=SAMPLE)
    parser.add_argument("voices", nargs="*", default=list(CANDIDATES))
    args = parser.parse_args(argv)
    settings = load_settings()
    if not settings.azure_ready:
        print("Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION in brain/.env first.")
        return 1
    voice = AzureVoice.from_settings(settings, args.out)
    assert voice is not None
    for name in args.voices:
        try:
            data = voice.synthesize(args.text, name, RATE)
        except (urllib.error.URLError, OSError) as err:
            print(f"{name}: failed ({err})")
            continue
        (args.out / f"{name}.mp3").write_bytes(data)
        print(f"{name}: {args.out / (name + '.mp3')}")
    return 0


if __name__ == "__main__":
    sys.exit(samples())
