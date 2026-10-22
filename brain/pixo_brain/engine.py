"""The session engine: plays a session step by step and applies the pedagogy rules.

Rules applied here, so that session files don't have to repeat them (see docs/schema.md):
- show before asking: `show` = attention phrase, image, the word said twice, Pixo's demo animation;
- never "No!": a miss gets an encouragement, the word is modelled again, and the child retries;
  after the last try Pixo says "Good try!" and the session goes on;
- variety: a category never gives the same variant twice in a row;
- combo: 3 right answers in a row make Pixo dance.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from .channels import Channel
from .content import (
    AskSayStep,
    AskTouchStep,
    Content,
    Phrase,
    SayStep,
    Session,
    ShowStep,
    Word,
)
from .matching import matches

COMBO_FOR_DANCE = 3
LAST_TRY_PHRASE = "encourage_good_try"  # "Good try!"
# Categories the engine picks from by itself (checked by the validator, rule P05).
REQUIRED_CATEGORIES = ("attention", "your_turn", "ask_say", "ask_touch", "praise", "encourage")


@dataclass
class AskResult:
    step: int
    type: str
    word: str
    success: bool
    attempts: int


@dataclass
class SessionReport:
    session: str
    nickname: str
    results: list[AskResult] = field(default_factory=list)
    nickname_count: int = 0

    @property
    def successes(self) -> int:
        return sum(r.success for r in self.results)


class SessionRunner:
    def __init__(
        self,
        content: Content,
        session: Session,
        nickname: str,
        channel: Channel,
        rng: random.Random | None = None,
    ) -> None:
        self.content = content
        self.session = session
        self.nickname = nickname
        self.io = channel
        self.rng = rng or random.Random()
        self.report = SessionReport(session.id, nickname)
        self._combo = 0
        self._last_variant: dict[str, str] = {}  # category -> id of the last variant used

    # --- Phrases --------------------------------------------------------------------------

    def _pick(self, category: str) -> Phrase:
        variants = self.content.categories[category]
        fresh = [p for p in variants if p.id != self._last_variant.get(category)] or variants
        phrase = self.rng.choice(fresh)
        self._last_variant[category] = phrase.id
        return phrase

    def _fill(self, phrase: Phrase, word: Word | None = None) -> str:
        text = phrase.text
        if "{name}" in text:
            self.report.nickname_count += text.count("{name}")
            text = text.replace("{name}", self.nickname)
        if word is not None:
            text = text.replace("{word}", word.text)
        return text

    async def _say_from(self, category: str, word: Word | None = None) -> None:
        await self.io.say(self._fill(self._pick(category), word))

    async def _say_id(self, phrase_id: str, word: Word | None = None) -> None:
        await self.io.say(self._fill(self.content.phrases[phrase_id], word))

    # --- Feedback -------------------------------------------------------------------------

    async def _praise(self) -> None:
        self._combo += 1
        await self.io.animate("happy")
        await self._say_from("praise")
        if self._combo >= COMBO_FOR_DANCE:
            await self.io.animate("dance")
            self._combo = 0

    def _miss(self) -> None:
        self._combo = 0

    # --- Steps ----------------------------------------------------------------------------

    async def _say(self, step: SayStep) -> None:
        if step.phrase is not None:
            await self._say_id(step.phrase)
        else:
            await self._say_from(step.category or "")

    async def _show(self, step: ShowStep) -> None:
        word = self.content.words[step.word]
        await self._say_from("attention")
        await self.io.show([word.id])
        await self.io.say(f"{word.text.capitalize()}!")
        await self.io.animate("show")
        await self.io.say(f"{word.text.capitalize()}!")

    async def _ask_say(self, index: int, step: AskSayStep) -> AskResult:
        word = self.content.words[step.word]
        await self.io.show([word.id])
        await self._say_from("your_turn")
        await self._say_from("ask_say", word)
        for attempt in range(1, step.tries + 1):
            heard = await self.io.listen()
            if matches(word, heard):
                await self._praise()
                return AskResult(index, step.type, word.id, True, attempt)
            self._miss()
            if attempt == step.tries:
                break
            # Model the word again, then let the child retry.
            await self._say_from("your_turn" if not heard else "encourage")
            await self.io.say(f"{word.text.capitalize()}!")
            await self._say_from("ask_say", word)
        await self._say_id(LAST_TRY_PHRASE)
        return AskResult(index, step.type, word.id, False, step.tries)

    async def _ask_touch(self, index: int, step: AskTouchStep) -> AskResult:
        word = self.content.words[step.word]
        await self.io.show(step.choices)
        await self._say_from("ask_touch", word)
        for attempt in range(1, step.tries + 1):
            tapped = await self.io.wait_tap(step.choices)
            if tapped == word.id:
                await self._praise()
                return AskResult(index, step.type, word.id, True, attempt)
            self._miss()
            if attempt == step.tries:
                break
            # Show the right answer, then let the child retry.
            await self._say_from("encourage")
            await self.io.show(step.choices, highlight=word.id)
            await self._say_from("ask_touch", word)
        await self.io.show(step.choices, highlight=word.id)
        await self._say_id(LAST_TRY_PHRASE)
        return AskResult(index, step.type, word.id, False, step.tries)

    # --- Session --------------------------------------------------------------------------

    async def run(self) -> SessionReport:
        for index, step in enumerate(self.session.steps):
            match step:
                case SayStep():
                    await self._say(step)
                case ShowStep():
                    await self._show(step)
                case AskSayStep():
                    self.report.results.append(await self._ask_say(index, step))
                    await self.io.clear()
                case AskTouchStep():
                    self.report.results.append(await self._ask_touch(index, step))
                    await self.io.clear()
        return self.report
