from __future__ import annotations

import asyncio

from pixo_brain.voice import RATE, SLOW_RATE, AzureVoice, ssml


def test_ssml_escapes_text_and_sets_language_and_speed():
    out = ssml("Tom & <Jerry>", "en-GB-MaisieNeural", RATE)
    assert "xml:lang='en-GB'" in out and "name='en-GB-MaisieNeural'" in out
    assert "Tom &amp; &lt;Jerry&gt;" in out and f"rate='{RATE}'" in out


def test_audio_is_cached_and_slow_is_a_different_line(tmp_path):
    bodies = []

    def fetch(url, headers, body):
        assert url == "https://westeurope.tts.speech.microsoft.com/cognitiveservices/v1"
        assert headers["Ocp-Apim-Subscription-Key"] == "k"
        bodies.append(body.decode())
        return b"mp3"

    voice = AzureVoice("k", "westeurope", "en-US-AnaNeural", tmp_path, fetch)
    first = asyncio.run(voice.audio("Hello!"))
    assert first == asyncio.run(voice.audio("Hello!"))
    slow = asyncio.run(voice.audio("Hello!", slow=True))
    assert slow != first and len(bodies) == 2 and SLOW_RATE in bodies[1]
    assert (tmp_path / first).read_bytes() == b"mp3"
