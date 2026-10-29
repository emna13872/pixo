"""Plays a v1 session (units/<unit>/s<n>.yaml, 7 steps) and applies the teaching rulebook.

The session file says what happens; the rulebook (docs/content-v1.md) says how Pixo reacts,
so files don't repeat it:
- ask_say: the child gets up to 3 tries. A first silence only gets the question again.
  1st miss: "Almost!", then Pixo says the word again, slowly.
  2nd miss: "Say it with me!", then the word again.
  3rd miss: "Good try!", and the word goes to the catch-up step.
- the praise (`say: {phrase: praise}`) and `celebrate` written right after an ask_say are
  for a success: they are skipped when the child missed.
- ask_touch: each round shows the options in a new order. A wrong touch gets an
  encouragement, the answer glows, and the child tries once more.
- catchup: the engine fills it with the words missed in `new`.
- variety: a category never gives the same variant twice in a row.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Any

from .channels import Channel
from .content import Content, Word
from .engine import AskResult, SessionReport
from .matching import matches

SAY_TRIES = 3
TOUCH_TRIES = 2
STEPS = ("hello", "song", "review", "new", "game", "catchup", "bye")


@dataclass
class Song:
    id: str
    file: str
    timing: list[dict[str, Any]]


class SessionPlayer:
    def __init__(
        self,
        content: Content,
        session: dict[str, Any],
        media: dict[str, Any],
        nickname: str,
        channel: Channel,
        rng: random.Random | None = None,
    ) -> None:
        self.content = content
        self.session = session
        self.nickname = nickname
        self.io = channel
        self.rng = rng or random.Random()
        self.report = SessionReport(session["id"], nickname)
        self.songs = {
            s["id"]: Song(s["id"], s.get("file", ""), s.get("timing", []))
            for s in media.get("songs", [])
        }
        self.videos = {v["id"]: v.get("file", "") for v in media.get("videos", [])}
        # image id -> word id, so `show: {image: word_hello}` can be shown as the word card
        self.image_words = {w.image: w.id for w in content.words.values()}
        self.missed: list[str] = []  # words to catch up, in order
        self._last_variant: dict[str, str] = {}
        self._ask = 0

    # --- Phrases --------------------------------------------------------------------------

    def _line(self, text: str, word: Word | None = None) -> str:
        if "{name}" in text:
            self.report.nickname_count += text.count("{name}")
            text = text.replace("{name}", self.nickname)
        if word is not None:
            text = text.replace("{word}", word.text)
        return text

    def _pick(self, category: str) -> str:
        variants = self.content.categories[category]
        fresh = [p for p in variants if p.id != self._last_variant.get(category)] or variants
        phrase = self.rng.choice(fresh)
        self._last_variant[category] = phrase.id
        return phrase.text

    async def _say_from(self, category: str, word: Word | None = None) -> None:
        await self.io.say(self._line(self._pick(category), word))

    async def _model(self, word: Word, slow: bool = False) -> None:
        """Pixo says the word on its own, as the model the child repeats."""
        text = f"{word.text.capitalize()}!"
        await (self.io.say_slowly(text) if slow else self.io.say(text))

    # --- Actions --------------------------------------------------------------------------

    async def _say(self, a: dict[str, Any]) -> None:
        if a.get("gesture"):
            await self.io.animate(a["gesture"])
        if "text" in a:
            await self.io.say(self._line(a["text"]))
        else:
            await self._say_from(a["phrase"])

    async def _show(self, a: dict[str, Any]) -> None:
        word = self.image_words.get(a["image"])
        if word is not None:
            await self.io.show([word])
        if a.get("gesture"):
            await self.io.animate(a["gesture"])

    async def _ask_say(self, a: dict[str, Any], step: str) -> bool:
        word = self.content.words[a["word"]]
        await self.io.show([word.id])
        await self._say_from(a["prompt"], word)
        attempt, reprompted = 0, False
        while attempt < SAY_TRIES:
            heard = await self.io.listen()
            if matches(word, heard):
                self._result(step, "ask_say", word.id, True, attempt + 1)
                return True
            if not heard and not reprompted:
                reprompted = True  # a first silence is not a miss: ask once more
                await self._say_from(a["prompt"], word)
                continue
            attempt += 1
            if attempt == 1:
                await self.io.say("Almost!")
                await self._model(word, slow=True)
            elif attempt == 2:
                await self.io.say("Say it with me!")
                await self._model(word)
        await self.io.say("Good try!")
        self._result(step, "ask_say", word.id, False, SAY_TRIES)
        if step != "catchup" and word.id not in self.missed:
            self.missed.append(word.id)
        return False

    async def _ask_touch(self, a: dict[str, Any], step: str) -> None:
        answer = self.content.words[a["answer"]]
        for _ in range(a.get("rounds", 1)):
            options = list(a["options"])
            self.rng.shuffle(options)
            await self.io.show(options)
            await self._say_from(a["prompt"], answer)
            for attempt in range(1, TOUCH_TRIES + 1):
                tapped = await self.io.wait_tap(options)
                if tapped == answer.id:
                    await self.io.animate("happy")
                    await self._say_from("praise")
                    self._result(step, "ask_touch", answer.id, True, attempt)
                    break
                if attempt == TOUCH_TRIES:
                    await self.io.show(options, highlight=answer.id)
                    await self.io.say("Good try!")
                    self._result(step, "ask_touch", answer.id, False, attempt)
                    break
                await self._say_from("encourage")
                await self.io.show(options, highlight=answer.id)
                await self._say_from(a["prompt"], answer)
            await self.io.clear()

    async def _sing(self, a: dict[str, Any]) -> None:
        song = self.songs[a["song"]]
        await self.io.sing(song.id, song.file, song.timing)

    async def _video(self, a: dict[str, Any]) -> None:
        file = self.videos.get(a["video"], "")
        if file:
            await self.io.play_video(a["video"], file)
        else:  # not made yet: Pixo dances instead
            await self.io.animate("dance")

    async def _celebrate(self, a: dict[str, Any]) -> None:
        await self.io.animate("dance")
        await self.io.say(
            self._line(a["text"]) if a.get("text") else self._line(self._pick("celebrate"))
        )

    def _result(self, step: str, kind: str, word: str, success: bool, attempts: int) -> None:
        self._ask += 1
        self.report.results.append(AskResult(self._ask, kind, word, success, attempts))

    # --- Steps ----------------------------------------------------------------------------

    async def _play(self, step: str, actions: list[dict[str, Any]]) -> None:
        skipping = False  # after a missed ask_say: skip the success-only feedback
        for action in actions:
            ((kind, a),) = action.items()
            if skipping and (
                kind == "celebrate" or (kind == "say" and a.get("phrase") == "praise")
            ):
                continue
            skipping = False
            match kind:
                case "say":
                    await self._say(a)
                case "show":
                    await self._show(a)
                case "ask_say":
                    skipping = not await self._ask_say(a, step)
                    await self.io.clear()
                case "ask_touch":
                    await self._ask_touch(a, step)
                case "sing":
                    await self._sing(a)
                case "video":
                    await self._video(a)
                case "celebrate":
                    await self._celebrate(a)
                case "gesture":
                    await self.io.animate(a["gesture"])

    def _catchup(self) -> list[dict[str, Any]]:
        """One more short try for each word missed in `new`."""
        if not self.missed:
            return []
        actions: list[dict[str, Any]] = [{"say": {"phrase": "catchup_intro"}}]
        for word_id in self.missed:
            word = self.content.words[word_id]
            actions += [
                {"show": {"image": word.image}},
                {"say": {"text": f"{word.text.capitalize()}!"}},
                {"ask_say": {"word": word_id, "prompt": "ask_say"}},
                {"say": {"phrase": "praise"}},
            ]
        return actions

    async def run(self) -> SessionReport:
        for step in STEPS:
            actions = self.session["steps"].get(step, [])
            await self._play(step, self._catchup() if step == "catchup" else actions)
        return self.report
