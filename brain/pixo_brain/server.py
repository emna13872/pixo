"""The brain as a server: the Android app connects over WebSocket (protocol: docs/protocol.md).

Usage (from the brain/ folder):
    uv run pixo-serve                  # http://127.0.0.1:8000 (USB with adb reverse, or this PC)
    uv run pixo-serve --host 0.0.0.0   # also reachable from the phone over Wi-Fi
Open http://127.0.0.1:8000 in a browser for the test page (a fake app).
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from datetime import datetime
from importlib.resources import files
from pathlib import Path
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from .channels import LoggingChannel
from .content import Content, load_yaml
from .engine import SessionRunner
from .play import DEFAULT_LOGS
from .player import SessionPlayer
from .settings import load_settings
from .validate import DEFAULT_CONTENT, validate
from .voice import AzureVoice

PROTOCOL_VERSION = "0.1"
LISTEN_TIMEOUT_MS = 5000  # teaching rulebook: the child gets 5 seconds to answer
TAP_TIMEOUT_MS = 10000
MAX_NICKNAME_LENGTH = 30


class SessionStopped(Exception):
    """The app asked to stop the session."""


class InvalidContentError(Exception):
    def __init__(self, issues: list) -> None:
        super().__init__(f"{len(issues)} problem(s) in the content")
        self.issues = issues


async def receive(ws: WebSocket) -> dict[str, Any] | None:
    """Next message from the app, or None (after answering `bad_message`) if it isn't valid."""
    raw = await ws.receive_text()
    try:
        msg = json.loads(raw)
    except json.JSONDecodeError:
        msg = None
    if not isinstance(msg, dict) or not isinstance(msg.get("type"), str):
        await send_error(ws, "bad_message", "expected a JSON object with a `type`")
        return None
    return msg


async def send_error(ws: WebSocket, code: str, message: str) -> None:
    await ws.send_json({"type": "error", "code": code, "message": message})


class WebSocketChannel:
    """A Channel whose every call is a command to the app, answered with the same `id`."""

    def __init__(self, ws: WebSocket, voice: AzureVoice | None = None) -> None:
        self._ws = ws
        self._voice = voice
        self._next_id = 0
        self.ignored: list[dict[str, Any]] = []  # answers that didn't match (for the log)

    async def _command(self, type_: str, answer: str, **fields: Any) -> dict[str, Any]:
        self._next_id += 1
        command_id = self._next_id
        await self._ws.send_json({"type": type_, "id": command_id, **fields})
        while True:
            msg = await receive(self._ws)
            if msg is None:
                continue
            if msg["type"] == "stop_session":
                raise SessionStopped
            if msg["type"] == answer and msg.get("id") == command_id:
                return msg
            self.ignored.append(msg)

    async def _audio(self, text: str, slow: bool) -> dict[str, str]:
        """Pixo's natural voice for this line, if Azure is set up (else the phone speaks)."""
        if self._voice is None:
            return {}
        name = await self._voice.audio(text, slow)
        return {"audio_url": f"voice/{name}"} if name else {}

    async def say(self, text: str) -> None:
        await self._command("say", "done", text=text, **await self._audio(text, False))

    async def say_slowly(self, text: str) -> None:
        audio = await self._audio(text, True)
        await self._command("say", "done", text=text, slow=True, **audio)

    async def sing(self, song: str, file: str, timing: list[dict]) -> None:
        await self._command("sing", "done", song=song, url=file, timing=timing)

    async def play_video(self, video: str, file: str) -> None:
        await self._command("play_video", "done", video=video, url=file)

    async def show(self, words: list[str], highlight: str | None = None) -> None:
        await self._command("show", "done", words=words, highlight=highlight)

    async def clear(self) -> None:
        await self._command("clear", "done")

    async def animate(self, name: str) -> None:
        await self._command("animate", "done", name=name)

    async def listen(self) -> list[str]:
        msg = await self._command("listen", "heard", language="en-US", timeout_ms=LISTEN_TIMEOUT_MS)
        transcripts = msg.get("transcripts")
        if not isinstance(transcripts, list):
            return []
        return [t for t in transcripts if isinstance(t, str)]

    async def wait_tap(self, choices: list[str]) -> str | None:
        msg = await self._command("wait_tap", "tapped", choices=choices, timeout_ms=TAP_TIMEOUT_MS)
        word = msg.get("word")
        return word if word in choices else None


def session_words(content: Content, session_id: str) -> dict[str, dict[str, str]]:
    session = content.sessions[session_id]
    return {
        word_id: {"text": content.words[word_id].text, "image": content.words[word_id].image}
        for word_id in [*session.words, *session.review]
    }


IMAGE_TYPES = (".png", ".jpg", ".jpeg", ".webp")


def v1_session_words(
    content: Content, session: dict[str, Any], media: dict[str, Any]
) -> dict[str, dict[str, str]]:
    """Like session_words, plus the picture's address on this server (empty until it exists)."""
    files_by_image = {m["id"]: m.get("file", "") for m in media.get("images", [])}
    words = {}
    for word_id in [*session["words"], *session.get("review", [])]:
        word = content.words[word_id]
        file = files_by_image.get(word.image, "")
        words[word_id] = {
            "text": word.text,
            "image": word.image,
            "image_url": file if file.lower().endswith(IMAGE_TYPES) else "",
        }
    return words


def create_app(
    content_root: Path = DEFAULT_CONTENT,
    logs: Path = DEFAULT_LOGS,
    voice: AzureVoice | None = None,
) -> FastAPI:
    """Build the server. Refuses to start (InvalidContentError) if the content is not valid.

    With a [voice], `say` carries the line as an MP3 served at /voice (Pixo's natural voice).
    """
    content, issues = validate(content_root)
    if issues:
        raise InvalidContentError(issues)

    app = FastAPI(title="Pixo brain", version=PROTOCOL_VERSION)
    # v1 sessions (units/<unit>/s<n>.yaml), played by SessionPlayer
    v1: dict[str, dict[str, Any]] = {}
    for rel in content.unit_files:
        data = load_yaml(content_root / rel)
        v1[data["id"]] = data
    media_path = content_root / "media.yaml"
    media = load_yaml(media_path) if media_path.exists() else {}
    sessions = [{"id": s.id, "title": s.title} for s in content.sessions.values()]
    sessions += [{"id": s["id"], "title": s["title"]} for s in v1.values()]
    # pictures and songs, at the paths media.yaml gives (media/images/word_hello.png…)
    if (content_root / "media").is_dir():
        app.mount("/media", StaticFiles(directory=content_root / "media"), name="media")
    if voice is not None:
        app.mount("/voice", StaticFiles(directory=voice.cache), name="voice")

    @app.get("/", response_class=HTMLResponse)
    async def test_page() -> str:
        return files("pixo_brain").joinpath("static/test_app.html").read_text(encoding="utf-8")

    @app.get("/health")
    async def health() -> dict[str, Any]:
        return {"status": "ok", "protocol": PROTOCOL_VERSION, "sessions": sessions}

    async def run_session(ws: WebSocket, msg: dict[str, Any]) -> None:
        session_id = msg.get("session")
        if session_id not in content.sessions and session_id not in v1:
            await send_error(ws, "unknown_session", f"unknown session {session_id!r}")
            return
        nickname = str(msg.get("nickname") or "").strip()[:MAX_NICKNAME_LENGTH] or "friend"

        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        inner = WebSocketChannel(ws, voice)
        channel = LoggingChannel(inner, logs / f"{stamp}_session-{session_id}.jsonl")
        channel.log("start", session=session_id, nickname=nickname, mode="websocket")
        runner: SessionRunner | SessionPlayer
        if session_id in v1:
            title = v1[session_id]["title"]
            words = v1_session_words(content, v1[session_id], media)
            runner = SessionPlayer(
                content, v1[session_id], media, nickname, channel, random.Random()
            )
        else:
            title = content.sessions[session_id].title
            words = session_words(content, session_id)
            runner = SessionRunner(
                content, content.sessions[session_id], nickname, channel, random.Random()
            )
        await ws.send_json(
            {"type": "session_started", "session": session_id, "title": title, "words": words}
        )

        def log_ignored() -> None:
            for ignored in inner.ignored:
                channel.log("ignored", message=ignored)
            inner.ignored.clear()

        stopped = False
        try:
            report = await runner.run()
        except SessionStopped:
            stopped, report = True, runner.report
        except WebSocketDisconnect:
            log_ignored()
            channel.log("disconnected")
            channel.close()
            raise
        log_ignored()
        end = {
            "type": "session_ended",
            "session": session_id,
            "successes": report.successes,
            "asks": len(report.results),
            "stopped": stopped,
        }
        channel.log("end", **{k: v for k, v in end.items() if k != "type"})
        channel.close()
        await ws.send_json(end)

    @app.websocket("/ws")
    async def websocket(ws: WebSocket) -> None:
        await ws.accept()
        try:
            hello = await receive(ws)
            if hello is None:
                await ws.close()
                return
            if hello["type"] != "hello":
                await send_error(ws, "hello_first", "the first message must be `hello`")
                await ws.close()
                return
            if hello.get("protocol") != PROTOCOL_VERSION:
                await send_error(
                    ws,
                    "protocol_mismatch",
                    f"brain speaks protocol {PROTOCOL_VERSION}, app sent {hello.get('protocol')!r}",
                )
                await ws.close()
                return
            await ws.send_json(
                {"type": "welcome", "protocol": PROTOCOL_VERSION, "sessions": sessions}
            )
            while True:
                msg = await receive(ws)
                if msg is None or msg["type"] == "stop_session":
                    continue  # nothing to stop outside a session
                if msg["type"] == "start_session":
                    await run_session(ws, msg)
                else:
                    await send_error(ws, "bad_message", f"unexpected message {msg['type']!r}")
        except WebSocketDisconnect:
            return

    return app


def main(argv: list[str] | None = None) -> int:
    import uvicorn

    parser = argparse.ArgumentParser(description="Run Pixo's brain as a server for the app.")
    parser.add_argument(
        "--host", default="127.0.0.1", help="0.0.0.0 to accept the phone over Wi-Fi"
    )
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--content", type=Path, default=DEFAULT_CONTENT)
    parser.add_argument("--logs", type=Path, default=DEFAULT_LOGS)
    args = parser.parse_args(argv)
    try:
        voice = AzureVoice.from_settings(load_settings(), args.logs / "voice-cache")
        app = create_app(args.content, args.logs, voice)
    except InvalidContentError as err:
        for issue in err.issues:
            print(issue)
        print("\nThe content has problems: fix them first (uv run pixo-validate).")
        return 1
    print(f"Pixo brain, protocol {PROTOCOL_VERSION}")
    print(f"  voice: {voice.voice + ' (Azure)' if voice else 'the phone (no Azure key in .env)'}")
    print(f"  test page: http://127.0.0.1:{args.port}")
    print(f"  app connects to: ws://<this PC>:{args.port}/ws")
    uvicorn.run(app, host=args.host, port=args.port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
