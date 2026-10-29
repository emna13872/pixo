from __future__ import annotations

import shutil
from pathlib import Path

import pytest
import yaml

from pixo_brain.content import load_yaml
from pixo_brain.units import line_words
from pixo_brain.validate import DEFAULT_CONTENT, validate


@pytest.fixture
def root(tmp_path) -> Path:
    """A copy of the real content, so each test can break one thing."""
    dest = tmp_path / "content"
    shutil.copytree(DEFAULT_CONTENT, dest)
    return dest


S1 = Path("units/u1-hello/s1.yaml")


def read(root: Path, rel: Path | str) -> dict:
    return load_yaml(root / rel)  # keeps yes/no as words


def write(root: Path, rel: Path | str, data: object) -> None:
    (root / rel).write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def codes(root: Path) -> list[str]:
    _, issues = validate(root)
    return [i.code for i in issues]


def session(root: Path) -> dict:
    return read(root, S1)


def test_real_s1_is_valid():
    content, issues = validate(DEFAULT_CONTENT)
    assert [str(i) for i in issues] == []
    assert "units/u1-hello/s1.yaml" in content.unit_files


def test_round_trip_fixture_is_valid(root):
    write(root, S1, session(root))
    assert codes(root) == []


def test_line_words_counts_the_whole_line():
    assert line_words("Welcome back, {name}! Let's go on!") == 6
    assert line_words("Hello, {name}!") == 2


def test_v01_missing_step(root):
    s = session(root)
    del s["steps"]["game"]
    write(root, S1, s)
    assert "V01" in codes(root)


def test_v01_catchup_must_be_empty(root):
    s = session(root)
    s["steps"]["catchup"] = [{"say": {"phrase": "praise"}}]
    write(root, S1, s)
    assert "V01" in codes(root)


def test_v01_say_needs_text_or_phrase_not_both(root):
    s = session(root)
    s["steps"]["hello"][0] = {"say": {"text": "Hi!", "phrase": "greet"}}
    write(root, S1, s)
    assert "V01" in codes(root)


def test_v01_unknown_action(root):
    s = session(root)
    s["steps"]["hello"].append({"dance": {}})
    write(root, S1, s)
    assert "V01" in codes(root)


def test_v02_unknown_word(root):
    s = session(root)
    s["steps"]["game"][1]["ask_touch"]["options"][-1] = "cat"
    write(root, S1, s)
    assert "V02" in codes(root)


def test_v02_word_from_a_later_unit(root):
    s = session(root)
    s["words"].append("red")
    write(root, S1, s)
    assert "V02" in codes(root)


def test_v03_image_not_in_media(root):
    s = session(root)
    s["steps"]["new"][1]["show"]["image"] = "word_unknown"
    write(root, S1, s)
    assert "V03" in codes(root)


def test_v03_song_not_in_media(root):
    s = session(root)
    s["steps"]["song"][1]["sing"]["song"] = "song_unknown"
    write(root, S1, s)
    assert "V03" in codes(root)


def test_v03_word_image_missing_from_media(root):
    media = read(root, "media.yaml")
    media["images"] = media["images"][1:]
    write(root, "media.yaml", media)
    assert "V03" in codes(root)


def test_v04_unknown_category(root):
    s = session(root)
    s["steps"]["hello"][1] = {"say": {"phrase": "nope"}}
    write(root, S1, s)
    assert "V04" in codes(root)


def test_v05_line_too_long(root):
    s = session(root)
    s["steps"]["hello"][0] = {"say": {"text": "Hello my very good friend {name}!"}}
    write(root, S1, s)
    assert "V05" in codes(root)


def test_v06_answer_not_in_options(root):
    s = session(root)
    s["steps"]["game"][1]["ask_touch"]["answer"] = "no"
    s["steps"]["game"][1]["ask_touch"]["options"] = ["hello", "bye"]
    write(root, S1, s)
    assert "V06" in codes(root)


def test_v07_ask_before_show(root):
    s = session(root)
    s["steps"]["new"] = [a for a in s["steps"]["new"] if "show" not in a]
    write(root, S1, s)
    assert "V07" in codes(root)


def test_v08_words_differ_from_program(root):
    s = session(root)
    s["words"] = s["words"][:2]
    write(root, S1, s)
    assert "V08" in codes(root)


def test_v08_wrong_folder(root):
    s = session(root)
    (root / "units" / "u2-colors").mkdir()
    write(root, "units/u2-colors/s1.yaml", s)
    assert "V08" in codes(root)


def test_v09_nickname_too_rare(root):
    s = session(root)
    s["steps"]["hello"][0] = {"say": {"text": "Hello!"}}
    s["steps"]["song"] = [a for a in s["steps"]["song"] if "{name}" not in str(a)]
    write(root, S1, s)
    assert "V09" in codes(root)


def test_program_unknown_word(root):
    program = read(root, "program.yaml")
    program["units"][1]["sessions"][0]["words"].append("purple")
    write(root, "program.yaml", program)
    assert "V02" in codes(root)


def test_units_are_not_limited_to_three(root):
    """The program grows until fluency: a unit 12 needs no code change."""
    words = read(root, "words.yaml")
    words.append(
        {
            "id": "apple",
            "text": "apple",
            "unit": "u12",
            "image": "word_apple",
            "accepted": ["apple", "apples", "appel"],
        }
    )
    write(root, "words.yaml", words)
    media = read(root, "media.yaml")
    media["images"].append(
        {
            "id": "word_apple",
            "unit": "u12",
            "file": "",
            "source": "",
            "license": "",
            "status": "todo",
        }
    )
    write(root, "media.yaml", media)
    program = read(root, "program.yaml")
    program["units"].append(
        {"id": "u12-food", "title": "Food", "sessions": [{"id": "s1", "words": ["apple"]}]}
    )
    write(root, "program.yaml", program)
    s = session(root)
    s.update(id="u12-s1", unit="u12-food", words=["apple"], review=["hello"])
    s["steps"]["new"] = [
        {"show": {"image": "word_apple"}},
        {"ask_say": {"word": "apple", "prompt": "ask_say"}},
        {"say": {"text": "Good job, {name}!"}},
    ]
    s["steps"]["game"] = [
        {"ask_touch": {"prompt": "ask_touch", "options": ["apple", "hello"], "answer": "apple"}}
    ]
    (root / "units" / "u12-food").mkdir()
    write(root, "units/u12-food/s1.yaml", s)
    _, issues = validate(root)
    assert [str(i) for i in issues] == []
