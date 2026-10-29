"""Tests for the v1 session player (units/u1-hello/s1.yaml), using a scripted child."""

from __future__ import annotations

import asyncio
import random

from test_engine import CONTENT, ScriptedChild

from pixo_brain.content import load_yaml
from pixo_brain.player import SessionPlayer
from pixo_brain.validate import DEFAULT_CONTENT

S1 = load_yaml(DEFAULT_CONTENT / "units/u1-hello/s1.yaml")
MEDIA = load_yaml(DEFAULT_CONTENT / "media.yaml")
GAME_TAPS = ["hello", "hello", "bye", "bye", "yes", "yes", "no", "no"]


class V1Child(ScriptedChild):
    async def say_slowly(self, text):
        self.events.append(("say_slowly", text))

    async def sing(self, song, file, timing):
        self.events.append(("sing", song, file, len(timing)))

    async def play_video(self, video, file):
        self.events.append(("play_video", video))


def play(answers: list[str | None], seed: int = 0) -> tuple:
    child = V1Child(answers)
    player = SessionPlayer(CONTENT, S1, MEDIA, "Sara", child, random.Random(seed))
    report = asyncio.run(player.run())
    assert child.answers == [], "the player did not ask for every scripted answer"
    return report, child


def test_all_right_plays_every_step():
    report, child = play(["hello", "bye", "yes", "no", *GAME_TAPS])
    assert report.successes == len(report.results) == 12
    assert ("sing", "song_hello", "media/songs/song_hello.mp3", 4) in child.events
    assert report.nickname_count >= 3
    assert not any("wrong" in line.lower() for line in child.said)  # "No!" is taught here
    assert child.said[-1] == "Bye-bye, Sara!"
    # no catch-up when nothing was missed
    catchup = ("One more time!", "Let's try again!", "Again, with me!")
    assert not any(line in catchup for line in child.said)


def test_three_misses_follow_the_rulebook_then_catch_up():
    report, child = play(["cat", "cat", "cat", "bye", "yes", "no", *GAME_TAPS, "hello"])
    said = child.said
    almost = said.index("Almost!")
    assert ("say_slowly", "Hello!") in child.events
    assert said[almost + 1] == "Say it with me!"
    assert said[almost + 3] == "Good try!"
    # the praise and the star written after the ask are skipped after a miss
    assert child.events[child.events.index(("say", "Good try!")) + 1] == ("clear",)
    # catch-up: hello is asked again at the end, and this time it works
    hello = [r for r in report.results if r.word == "hello" and r.type == "ask_say"]
    assert [r.success for r in hello] == [False, True]


def test_a_first_silence_only_repeats_the_question():
    report, _ = play(["", "hello", "bye", "yes", "no", *GAME_TAPS])
    first = report.results[0]
    assert first.success and first.attempts == 1


def test_wrong_touch_shows_the_answer():
    taps = ["bye", "hello", *GAME_TAPS[1:]]
    report, child = play(["hello", "bye", "yes", "no", *taps])
    assert any(e[0] == "show" and e[2] == "hello" for e in child.events)
    first_touch = next(r for r in report.results if r.type == "ask_touch")
    assert first_touch.success and first_touch.attempts == 2


def test_missing_video_becomes_a_dance():
    _, child = play(["hello", "bye", "yes", "no", *GAME_TAPS])
    assert not any(e[0] == "play_video" for e in child.events)
    bye = child.said.index("Great job today!")
    assert ("animate", "dance") in child.events[child.events.index(("say", child.said[bye])) :]
