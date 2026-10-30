"""How the engine talks to the outside world.

The engine never prints or reads anything itself: it calls a `Channel`. Each way of running Pixo
provides its own channel:
- `ConsoleChannel`: text mode in a terminal (Step 2), a person types what the child says or touches.
- tests use a scripted channel,
- the WebSocket server (Step 3) will send each call to the Android app.

`LoggingChannel` wraps any channel and writes every call and answer to a JSONL file.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol


class Channel(Protocol):
    async def say(self, text: str) -> None:
        """Pixo says `text` (returns once it has been said)."""

    async def say_slowly(self, text: str) -> None:
        """Pixo says `text` slowly, as a model for the child to repeat."""

    async def sing(self, song: str, file: str, timing: list[dict]) -> None:
        """Play a song (`file`, relative to content/) with its timed lyrics; returns at the end."""

    async def play_video(self, video: str, file: str) -> None:
        """Play a video (`file`, relative to content/); returns at the end."""

    async def show(self, words: list[str], highlight: str | None = None) -> None:
        """Display the images of `words` (word ids); `highlight` makes one image glow."""

    async def clear(self) -> None:
        """Remove the images from the screen."""

    async def animate(self, name: str) -> None:
        """Play one of Pixo's animations ("show", "happy", "dance")."""

    async def listen(self) -> list[str]:
        """Listen to the child. Returns the recognizer's guesses, best first; [] means silence."""

    async def wait_tap(self, choices: list[str]) -> str | None:
        """Wait for the child to touch an image. Returns its word id, or None if none was."""


class ConsoleChannel:
    """Text mode: Pixo's actions are printed, and you type the child's answers."""

    def __init__(self, words: dict[str, str]) -> None:
        self._words = words  # word id -> text, to print readable choices

    async def _input(self, prompt: str) -> str:
        return (await asyncio.to_thread(input, prompt)).strip()

    async def say(self, text: str) -> None:
        print(f"  PIXO: {text}")

    async def say_slowly(self, text: str) -> None:
        print(f"  PIXO (slowly): {text}")

    async def sing(self, song: str, file: str, timing: list[dict]) -> None:
        print(f"  [song {song}]")
        for line in timing:
            print(f"    ♪ {line['at']:5.1f}s  {line['text']}")

    async def play_video(self, video: str, file: str) -> None:
        print(f"  [video {video}]")

    async def show(self, words: list[str], highlight: str | None = None) -> None:
        images = ", ".join(f"*{w}*" if w == highlight else w for w in words)
        print(f"  [screen: {images}]")

    async def clear(self) -> None:
        print("  [screen cleared]")

    async def animate(self, name: str) -> None:
        print(f"  [pixo animation: {name}]")

    async def listen(self) -> list[str]:
        heard = await self._input("  CHILD SAYS (Enter = silence) > ")
        return [heard] if heard else []

    async def wait_tap(self, choices: list[str]) -> str | None:
        menu = "  ".join(f"{i}) {self._words.get(w, w)}" for i, w in enumerate(choices, 1))
        answer = await self._input(f"  CHILD TOUCHES {menu}  (Enter = nothing) > ")
        if answer.isdigit() and 1 <= int(answer) <= len(choices):
            return choices[int(answer) - 1]
        return answer if answer in choices else None


class LoggingChannel:
    """Wraps a channel and appends one JSON line per call to `path`."""

    def __init__(self, inner: Channel, path: Path) -> None:
        self._inner = inner
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self._file = path.open("a", encoding="utf-8")

    def log(self, kind: str, **data: object) -> None:
        line = {"t": datetime.now(UTC).isoformat(timespec="milliseconds"), "kind": kind, **data}
        self._file.write(json.dumps(line, ensure_ascii=False) + "\n")
        self._file.flush()

    def close(self) -> None:
        self._file.close()

    async def say(self, text: str) -> None:
        self.log("say", text=text)
        await self._inner.say(text)

    async def say_slowly(self, text: str) -> None:
        self.log("say_slowly", text=text)
        await self._inner.say_slowly(text)

    async def sing(self, song: str, file: str, timing: list[dict]) -> None:
        self.log("sing", song=song)
        await self._inner.sing(song, file, timing)

    async def play_video(self, video: str, file: str) -> None:
        self.log("play_video", video=video)
        await self._inner.play_video(video, file)

    async def show(self, words: list[str], highlight: str | None = None) -> None:
        self.log("show", words=words, highlight=highlight)
        await self._inner.show(words, highlight)

    async def clear(self) -> None:
        self.log("clear")
        await self._inner.clear()

    async def animate(self, name: str) -> None:
        self.log("animate", name=name)
        await self._inner.animate(name)

    async def listen(self) -> list[str]:
        self.log("listen")
        heard = await self._inner.listen()
        self.log("heard", transcripts=heard)
        return heard

    async def wait_tap(self, choices: list[str]) -> str | None:
        self.log("wait_tap", choices=choices)
        tapped = await self._inner.wait_tap(choices)
        self.log("tapped", word=tapped)
        return tapped
