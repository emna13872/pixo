"""Tests for the content validator. One test (or more) per rule code in docs/schema.md."""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from pixo_brain.content import load_content
from pixo_brain.validate import DEFAULT_CONTENT, main, sentences, validate

# --- A tiny but valid content folder, that each test breaks in one way ------------------

WORDS = [
    {
        "id": "hello",
        "text": "hello",
        "unit": "u1",
        "image": "w_hello",
        "accepted": ["hello", "hallo", "ello"],
    },
    {
        "id": "bye",
        "text": "bye",
        "unit": "u1",
        "image": "w_bye",
        "accepted": ["bye", "bye-bye", "bai"],
    },
    {"id": "red", "text": "red", "unit": "u2", "image": "w_red", "accepted": ["red", "wed", "rad"]},
]
PHRASES = {
    "greet": [{"id": "greet_hello", "text": "Hello, {name}!"}],
    "attention": [{"id": "attention_look", "text": "Look!"}],
    "your_turn": [{"id": "your_turn", "text": "Your turn!"}],
    "praise": [{"id": "praise_yes", "text": "Yes!"}, {"id": "praise_super", "text": "Super!"}],
    "encourage": [{"id": "encourage_good_try", "text": "Good try!"}],
    "ask_say": [{"id": "ask_say", "text": "Say {word}!"}],
    "ask_touch": [{"id": "ask_touch", "text": "Touch {word}!"}],
    "goodbye": [{"id": "goodbye_bye", "text": "Bye-bye, {name}!"}],
}
SESSION = {
    "schema_version": "0.1",
    "id": "1.1",
    "unit": "u1",
    "title": "Hello!",
    "words": ["hello", "bye"],
    "steps": [
        {"type": "say", "phrase": "greet_hello"},
        {"type": "show", "word": "hello"},
        {"type": "ask_say", "word": "hello"},
        {"type": "show", "word": "bye"},
        {"type": "ask_touch", "word": "bye", "choices": ["hello", "bye"]},
        {"type": "say", "category": "greet"},
        {"type": "say", "category": "praise"},
        {"type": "say", "phrase": "goodbye_bye"},
    ],
}


def write_content(root: Path, words=None, phrases=None, sessions=None) -> Path:
    (root / "sessions").mkdir(parents=True)
    (root / "words.yaml").write_text(yaml.safe_dump(words or WORDS), encoding="utf-8")
    (root / "phrases.yaml").write_text(yaml.safe_dump(phrases or PHRASES), encoding="utf-8")
    for session in sessions if sessions is not None else [SESSION]:
        path = root / "sessions" / f"{session['id']}.yaml"
        path.write_text(yaml.safe_dump(session), encoding="utf-8")
    return root


def codes(root: Path) -> list[str]:
    _, issues = validate(root)
    return [issue.code for issue in issues]


@pytest.fixture
def words():
    return copy.deepcopy(WORDS)


@pytest.fixture
def phrases():
    return copy.deepcopy(PHRASES)


@pytest.fixture
def session():
    return copy.deepcopy(SESSION)


# --- The real content ---------------------------------------------------------------------


def test_real_content_is_valid():
    _, issues = validate(DEFAULT_CONTENT)
    assert [str(i) for i in issues] == []


def test_cli_exit_codes(tmp_path, session, capsys):
    assert main([str(write_content(tmp_path / "ok"))]) == 0
    session["steps"] = session["steps"][1:3]  # no nickname at all
    assert main([str(write_content(tmp_path / "bad", sessions=[session]))]) == 1
    assert "[S09]" in capsys.readouterr().out


def test_fixture_is_valid(tmp_path):
    assert codes(write_content(tmp_path)) == []


# --- YAML loading ---------------------------------------------------------------------------


def test_yes_and_no_stay_words(tmp_path):
    root = write_content(tmp_path)
    (root / "words.yaml").write_text(
        "- {id: yes, text: yes, unit: u1, image: w, accepted: [yes, yeah, yas]}\n"
        "- {id: no, text: no, unit: u1, image: w, accepted: [no, know, noh]}\n",
        encoding="utf-8",
    )
    content, _ = load_content(root)
    assert set(content.words) == {"yes", "no"}


def test_invalid_yaml_is_reported_not_crashing(tmp_path):
    root = write_content(tmp_path)
    (root / "sessions" / "1.2.yaml").write_text("steps: [unclosed", encoding="utf-8")
    assert "S01" in codes(root)


# --- Words ----------------------------------------------------------------------------------


def test_w01_duplicate_word_id(tmp_path, words):
    words.append(dict(words[0], image="other"))
    assert "W01" in codes(write_content(tmp_path, words=words))


@pytest.mark.parametrize("accepted", [["hello", "hallo"], ["hello", "a", "b", "c", "d", "e"]])
def test_w02_variant_count(tmp_path, words, accepted):
    words[0]["accepted"] = accepted
    assert "W02" in codes(write_content(tmp_path, words=words))


def test_w02_word_itself_accepted(tmp_path, words):
    words[0]["accepted"] = ["hallo", "ello", "hullo"]
    assert "W02" in codes(write_content(tmp_path, words=words))


def test_w03_variant_matches_another_word(tmp_path, words):
    words[0]["accepted"] = ["hello", "hallo", "bye"]
    assert "W03" in codes(write_content(tmp_path, words=words))


def test_w03_shared_variant(tmp_path, words):
    words[0]["accepted"] = ["hello", "hallo", "rad"]
    assert "W03" in codes(write_content(tmp_path, words=words))


# --- Phrases --------------------------------------------------------------------------------


def test_sentences_split_and_placeholders():
    assert sentences("Welcome back, {name}! Let's go on!") == ["Welcome back, X", "Let's go on"]
    assert sentences("Look…") == ["Look"]


def test_p01_duplicate_phrase_id(tmp_path, phrases):
    phrases["praise"].append({"id": "praise_yes", "text": "Wow!"})
    assert "P01" in codes(write_content(tmp_path, phrases=phrases))


def test_p02_too_many_words(tmp_path, phrases):
    phrases["praise"].append({"id": "praise_long", "text": "You are a very good friend!"})
    assert "P02" in codes(write_content(tmp_path, phrases=phrases))


def test_p02_two_short_sentences_are_fine(tmp_path, phrases):
    phrases["greet"].append({"id": "greet_two", "text": "Welcome back, {name}! Let's go on!"})
    assert codes(write_content(tmp_path, phrases=phrases)) == []


@pytest.mark.parametrize("text", ["No!", "Wrong!", "No, try again!"])
def test_p03_no_negative_feedback(tmp_path, phrases, text):
    phrases["encourage"].append({"id": "encourage_bad", "text": text})
    assert "P03" in codes(write_content(tmp_path, phrases=phrases))


def test_p03_only_applies_to_feedback(tmp_path, phrases):
    phrases["ask_say"].append({"id": "ask_say_no", "text": "Say no!"})
    assert "P03" not in codes(write_content(tmp_path, phrases=phrases))


def test_p04_unknown_placeholder(tmp_path, phrases):
    phrases["greet"].append({"id": "greet_typo", "text": "Hello, {nmae}!"})
    assert "P04" in codes(write_content(tmp_path, phrases=phrases))


# --- Sessions -------------------------------------------------------------------------------


def test_s01_unknown_field(tmp_path, session):
    session["steps"][1]["wrod"] = "hello"
    assert "S01" in codes(write_content(tmp_path, sessions=[session]))


def test_s01_unknown_step_type(tmp_path, session):
    session["steps"].append({"type": "dance"})
    assert "S01" in codes(write_content(tmp_path, sessions=[session]))


@pytest.mark.parametrize("step", [{"type": "say"}, {"type": "say", "phrase": "a", "category": "b"}])
def test_s01_say_needs_exactly_one_source(tmp_path, session, step):
    session["steps"].append(step)
    assert "S01" in codes(write_content(tmp_path, sessions=[session]))


def test_s02_id_matches_file_name(tmp_path, session):
    root = write_content(tmp_path, sessions=[])
    (root / "sessions" / "1.2.yaml").write_text(yaml.safe_dump(session), encoding="utf-8")
    assert "S02" in codes(root)


def test_s03_unknown_word(tmp_path, session):
    session["words"].append("banana")
    assert "S03" in codes(write_content(tmp_path, sessions=[session]))


def test_s03_word_from_wrong_unit(tmp_path, session):
    session["words"].append("red")
    assert "S03" in codes(write_content(tmp_path, sessions=[session]))


def test_s03_review_from_later_unit(tmp_path, session):
    session["review"] = ["red"]
    assert "S03" in codes(write_content(tmp_path, sessions=[session]))


def test_s03_review_from_earlier_unit_is_fine(tmp_path, session):
    session.update(id="2.1", unit="u2", words=["red"], review=["hello", "bye"])
    session["steps"].insert(0, {"type": "show", "word": "red"})
    assert codes(write_content(tmp_path, sessions=[session])) == []


def test_s04_undeclared_word(tmp_path, session):
    session["words"] = ["hello"]
    assert "S04" in codes(write_content(tmp_path, sessions=[session]))


def test_s05_ask_before_show(tmp_path, session):
    session["steps"][1], session["steps"][2] = session["steps"][2], session["steps"][1]
    assert "S05" in codes(write_content(tmp_path, sessions=[session]))


def test_s05_review_words_need_no_show(tmp_path, session):
    session.update(words=["hello"], review=["bye"])
    del session["steps"][3]  # the `show: bye`
    assert codes(write_content(tmp_path, sessions=[session])) == []


@pytest.mark.parametrize(
    "choices", [["bye"], ["hello", "bye", "bye"], ["hello", "hello"], ["hello", "red"]]
)
def test_s06_touch_choices(tmp_path, session, choices):
    session["steps"][4]["choices"] = choices
    assert "S06" in codes(write_content(tmp_path, sessions=[session]))


@pytest.mark.parametrize(
    "step", [{"type": "say", "phrase": "nope"}, {"type": "say", "category": "nope"}]
)
def test_s07_unknown_phrase(tmp_path, session, step):
    session["steps"].append(step)
    assert "S07" in codes(write_content(tmp_path, sessions=[session]))


def test_s08_word_placeholder_in_say(tmp_path, session):
    session["steps"].append({"type": "say", "category": "ask_say"})
    assert "S08" in codes(write_content(tmp_path, sessions=[session]))


def test_s09_nickname_three_times(tmp_path, session):
    session["steps"] = [s for s in session["steps"] if s.get("phrase") != "goodbye_bye"]
    assert "S09" in codes(write_content(tmp_path, sessions=[session]))


def test_s09_category_counts_only_if_every_variant_has_name(tmp_path, phrases, session):
    phrases["greet"].append({"id": "greet_hi", "text": "Hi!"})
    assert "S09" in codes(write_content(tmp_path, phrases=phrases, sessions=[session]))


@pytest.mark.parametrize("category", ["attention", "your_turn", "praise", "encourage"])
def test_p05_engine_categories_exist(tmp_path, phrases, category):
    del phrases[category]
    assert "P05" in codes(write_content(tmp_path, phrases=phrases))


def test_p05_last_try_phrase_exists(tmp_path, phrases):
    phrases["encourage"] = [{"id": "encourage_other", "text": "Almost!"}]
    assert "P05" in codes(write_content(tmp_path, phrases=phrases))
