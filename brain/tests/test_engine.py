"""Tests for the session engine and the answer matching, using a scripted child."""

from __future__ import annotations

import asyncio
import json
import random

import pytest

from pixo_brain.channels import LoggingChannel
from pixo_brain.content import Session, Word
from pixo_brain.engine import SessionRunner
from pixo_brain.matching import matches, normalize
from pixo_brain.validate import DEFAULT_CONTENT, validate

CONTENT, _ = validate(DEFAULT_CONTENT)
NEGATIVE = ("no!", "wrong")


class ScriptedChild:
    """A Channel that records everything Pixo does and answers from a script.

    `answers` is consumed in order: a str for `listen` (what the child says, "" = silence),
    a word id or None for `wait_tap`.
    """

    def __init__(self, answers: list[str | None]) -> None:
        self.answers = list(answers)
        self.events: list[tuple] = []

    @property
    def said(self) -> list[str]:
        return [e[1] for e in self.events if e[0] == "say"]

    async def say(self, text):
        self.events.append(("say", text))

    async def show(self, words, highlight=None):
        self.events.append(("show", tuple(words), highlight))

    async def clear(self):
        self.events.append(("clear",))

    async def animate(self, name):
        self.events.append(("animate", name))

    async def listen(self):
        answer = self.answers.pop(0)
        self.events.append(("listen", answer))
        return [answer] if answer else []

    async def wait_tap(self, choices):
        answer = self.answers.pop(0)
        self.events.append(("wait_tap", tuple(choices), answer))
        return answer


def session(*steps: dict, words=("hello", "bye")) -> Session:
    return Session.model_validate(
        {
            "schema_version": "0.1",
            "id": "t",
            "unit": "u1",
            "title": "Test",
            "words": list(words),
            "steps": list(steps),
        }
    )


def run(sess: Session, answers: list[str | None], seed: int = 0) -> tuple:
    child = ScriptedChild(answers)
    runner = SessionRunner(CONTENT, sess, "Sara", child, random.Random(seed))
    report = asyncio.run(runner.run())
    assert child.answers == [], "the engine did not ask for every scripted answer"
    return report, child


def no_negative_words(lines: list[str]) -> bool:
    return not any(bad in line.lower() for line in lines for bad in NEGATIVE)


# --- Matching -----------------------------------------------------------------------------

HELLO = Word(id="hello", text="hello", unit="u1", image="w", accepted=["hello", "hallo", "ello"])
BYE = Word(id="bye", text="bye", unit="u1", image="w", accepted=["bye", "bye-bye", "bai"])


def test_normalize():
    assert normalize("  Hello, Pixo!! ") == "hello pixo"
    assert normalize("Bye-bye.") == "bye-bye"


@pytest.mark.parametrize("heard", ["hello", "Hello!", "HALLO", "hello pixo", "ello"])
def test_matches_accepted_forms(heard):
    assert matches(HELLO, [heard])


@pytest.mark.parametrize("heard", ["yellow", "hell", "", "bye"])
def test_does_not_match_other_words(heard):
    assert not matches(HELLO, [heard])


def test_matches_any_recognizer_guess():
    assert matches(HELLO, ["yellow", "hello"])


def test_matches_hyphenated_variant_heard_with_space():
    assert matches(BYE, ["bye bye"])


# --- Steps --------------------------------------------------------------------------------


def test_say_by_id_fills_nickname():
    report, child = run(session({"type": "say", "phrase": "greet_hello"}), [])
    assert child.said == ["Hello, Sara!"]
    assert report.nickname_count == 1


def test_say_by_category_picks_a_variant():
    _, child = run(session({"type": "say", "category": "praise"}), [])
    texts = {p.text for p in CONTENT.categories["praise"]}
    assert child.said[0] in {t.replace("{name}", "Sara") for t in texts}


def test_category_never_repeats_the_same_variant_twice_in_a_row():
    steps = [{"type": "say", "category": "praise"}] * 30
    _, child = run(session(*steps), [])
    assert all(a != b for a, b in zip(child.said, child.said[1:], strict=False))


def test_show_displays_image_then_says_word_twice():
    _, child = run(session({"type": "show", "word": "hello"}), [])
    kinds = [e[0] for e in child.events]
    assert kinds == ["say", "show", "say", "animate", "say"]
    assert child.events[1] == ("show", ("hello",), None)
    assert child.said[1:] == ["Hello!", "Hello!"]


def test_ask_say_right_first_time():
    report, child = run(session({"type": "ask_say", "word": "hello"}), ["hello"])
    assert (report.results[0].success, report.results[0].attempts) == (True, 1)
    assert ("animate", "happy") in child.events


def test_ask_say_wrong_then_right_models_the_word_again():
    report, child = run(session({"type": "ask_say", "word": "hello"}), ["yellow", "hello"])
    assert (report.results[0].success, report.results[0].attempts) == (True, 2)
    i = child.events.index(("listen", "yellow"))
    assert ("say", "Hello!") in child.events[i:]


def test_ask_say_silence_reprompts_with_your_turn():
    _, child = run(session({"type": "ask_say", "word": "hello"}), ["", "hello"])
    i = child.events.index(("listen", ""))
    your_turn = {p.text.replace("{name}", "Sara") for p in CONTENT.categories["your_turn"]}
    assert child.events[i + 1][1] in your_turn


def test_ask_say_never_blocks_and_never_says_no():
    report, child = run(session({"type": "ask_say", "word": "hello"}), ["no", "", "banana"])
    assert (report.results[0].success, report.results[0].attempts) == (False, 3)
    assert child.said[-1] == "Good try!"
    assert no_negative_words(child.said)


def test_ask_say_respects_tries():
    report, _ = run(session({"type": "ask_say", "word": "hello", "tries": 1}), [""])
    assert report.results[0].attempts == 1


def test_ask_touch_right():
    step = {"type": "ask_touch", "word": "bye", "choices": ["hello", "bye"]}
    report, child = run(session(step), ["bye"])
    assert report.results[0].success
    assert child.events[0] == ("show", ("hello", "bye"), None)


def test_ask_touch_wrong_highlights_the_right_image():
    step = {"type": "ask_touch", "word": "bye", "choices": ["hello", "bye"]}
    report, child = run(session(step), ["hello", "bye"])
    assert (report.results[0].success, report.results[0].attempts) == (True, 2)
    assert ("show", ("hello", "bye"), "bye") in child.events


def test_ask_touch_no_touch_at_all_shows_answer_and_moves_on():
    step = {"type": "ask_touch", "word": "bye", "choices": ["hello", "bye"]}
    report, child = run(session(step), [None, None, None])
    assert not report.results[0].success
    assert child.events[-3:-1] == [("show", ("hello", "bye"), "bye"), ("say", "Good try!")]
    assert no_negative_words(child.said)


def test_combo_dance_after_three_right_answers_in_a_row():
    steps = [{"type": "ask_say", "word": "hello"}] * 3
    _, child = run(session(*steps), ["hello", "hello", "hello"])
    assert child.events.count(("animate", "dance")) == 1


def test_a_miss_resets_the_combo():
    steps = [{"type": "ask_say", "word": "hello", "tries": 1}] * 4
    _, child = run(session(*steps), ["hello", "hello", "", "hello"])
    assert ("animate", "dance") not in child.events


# --- Whole session 1.1 --------------------------------------------------------------------

SESSION_1_1 = CONTENT.sessions["1.1"]
PERFECT_CHILD = ["hello", "bye", "hello", "bye"]  # ask_say x2, then ask_touch x2


@pytest.mark.parametrize("seed", range(5))
def test_session_1_1_perfect_child(seed):
    report, child = run(SESSION_1_1, PERFECT_CHILD, seed)
    assert report.successes == len(report.results) == 4
    assert report.nickname_count >= 3
    assert child.said[-1] == "Bye-bye, Sara!"
    assert no_negative_words(child.said)


@pytest.mark.parametrize("seed", range(5))
def test_session_1_1_silent_child_still_finishes_kindly(seed):
    report, child = run(SESSION_1_1, ["", "", "", "", "", ""] + [None] * 6, seed)
    assert report.successes == 0
    assert report.nickname_count >= 3
    assert child.said[-1] == "Bye-bye, Sara!"
    assert no_negative_words(child.said)


def test_every_line_pixo_says_is_short():
    _, child = run(SESSION_1_1, ["yellow", "hello", "", "bye", "hello", "bye"])
    for line in child.said:
        for sentence in line.replace("!", ".").replace("?", ".").replace("…", ".").split("."):
            assert len(sentence.split()) <= 5, line


# --- Logging ------------------------------------------------------------------------------


def test_logging_channel_writes_one_json_line_per_event(tmp_path):
    child = ScriptedChild(PERFECT_CHILD)
    channel = LoggingChannel(child, tmp_path / "logs" / "s.jsonl")
    asyncio.run(SessionRunner(CONTENT, SESSION_1_1, "Sara", channel, random.Random(0)).run())
    channel.close()
    lines = [json.loads(line) for line in channel.path.read_text(encoding="utf-8").splitlines()]
    kinds = [line["kind"] for line in lines]
    assert kinds.count("heard") == 2 and kinds.count("tapped") == 2
    assert {"t", "kind"} <= set(lines[0])
    assert lines[kinds.index("heard")]["transcripts"] == ["hello"]
