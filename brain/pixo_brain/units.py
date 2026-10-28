"""Check the v1 content files: program.yaml, media.yaml and units/<unit>/s<n>.yaml.

Two layers:
  1. JSON Schema (protocol/v1/content/*.schema.json) checks the shape of each file.
  2. Cross-checks here check what a schema cannot: that every word, phrase category,
     image, song and video a session cites exists, and the pedagogical rules.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from jsonschema import Draft202012Validator
from jsonschema.exceptions import best_match

from .content import Content, Issue, load_yaml, unit_number

SCHEMAS = Path(__file__).resolve().parents[2] / "protocol" / "v1" / "content"
MAX_WORDS_PER_LINE = 5
MIN_NAME_PER_SESSION = 3

_PLACEHOLDER = re.compile(r"\{([^}]*)\}")
_WORD = re.compile(r"[A-Za-z']+")


@dataclass
class Media:
    images: set[str] = field(default_factory=set)
    songs: set[str] = field(default_factory=set)
    videos: set[str] = field(default_factory=set)


def _schema(name: str) -> Draft202012Validator:
    return Draft202012Validator(json.loads((SCHEMAS / name).read_text(encoding="utf-8")))


def _shape_issues(data: object, schema: str, file: str) -> list[Issue]:
    """V01: every JSON Schema error, with the path where it happened."""
    issues = []
    for err in sorted(_schema(schema).iter_errors(data), key=lambda e: list(e.absolute_path)):
        # "not valid under any of the given schemas" says nothing: show the closest reason
        while err.validator == "oneOf" and err.context:
            err = best_match(err.context)
        where = ".".join(str(p) for p in err.absolute_path)
        issues.append(Issue("V01", file, where, err.message))
    return issues


def _load(root: Path, rel: str, schema: str, issues: list[Issue]) -> object | None:
    path = root / rel
    if not path.exists():
        return None
    try:
        data = load_yaml(path)
    except Exception as exc:  # malformed YAML: report it, keep checking the rest
        issues.append(Issue("V01", rel, "", f"not valid YAML: {exc}"))
        return None
    found = _shape_issues(data, schema, rel)
    issues += found
    return None if found else data


def line_words(text: str) -> int:
    """Words in a whole line, a placeholder counting as one word."""
    return len(_WORD.findall(_PLACEHOLDER.sub("X", text)))


def check_v1(root: Path, content: Content) -> tuple[list[str], list[Issue]]:
    """Check the v1 files under `root`. Returns the session files found and the issues."""
    issues: list[Issue] = []

    for rel, schema in (
        ("words.yaml", "words.schema.json"),
        ("phrases.yaml", "phrases.schema.json"),
    ):
        _load(root, rel, schema, issues)

    media = Media()
    raw_media = _load(root, "media.yaml", "media.schema.json", issues)
    if isinstance(raw_media, dict):
        media.images = {m["id"] for key in ("images", "other") for m in raw_media.get(key, [])}
        media.songs = {m["id"] for m in raw_media["songs"]}
        media.videos = {m["id"] for m in raw_media["videos"]}
        for word in content.words.values():
            if word.image not in media.images:
                issues.append(
                    Issue("V03", "media.yaml", word.id, f'image "{word.image}" is not listed')
                )

    program = _load(root, "program.yaml", "program.schema.json", issues)
    planned: dict[str, list[str]] = {}  # "u1-s1" -> words
    unit_dirs: dict[str, str] = {}  # "u1" -> "u1-hello"
    if isinstance(program, dict):
        for unit in program["units"]:
            short = unit["id"].split("-")[0]
            if short in unit_dirs:
                issues.append(
                    Issue("V08", "program.yaml", unit["id"], f"unit {short} appears twice")
                )
            unit_dirs[short] = unit["id"]
            for session in unit["sessions"]:
                planned[f"{short}-{session['id']}"] = session["words"]
                for word_id in session["words"]:
                    word = content.words.get(word_id)
                    if word is None:
                        issues.append(
                            Issue("V02", "program.yaml", unit["id"], f'unknown word "{word_id}"')
                        )
                    elif word.unit != short:
                        issues.append(
                            Issue(
                                "V02",
                                "program.yaml",
                                unit["id"],
                                f'"{word_id}" belongs to unit {word.unit}',
                            )
                        )

    files = sorted((root / "units").glob("*/s*.yaml"))
    for path in files:
        rel = path.relative_to(root).as_posix()
        data = _load(root, rel, "session.schema.json", issues)
        if isinstance(data, dict):
            issues += _check_session(content, media, planned, unit_dirs, rel, data)
    return [p.relative_to(root).as_posix() for p in files], issues


def _check_session(
    content: Content,
    media: Media,
    planned: dict[str, list[str]],
    unit_dirs: dict[str, str],
    file: str,
    s: dict,
) -> list[Issue]:
    issues: list[Issue] = []

    def add(code: str, where: str, message: str) -> None:
        issues.append(Issue(code, file, where, message))

    unit = s["id"].split("-")[0]
    unit_dir = unit_dirs.get(unit, s["unit"])
    expected = f"units/{unit_dir}/{s['id'].split('-')[1]}.yaml"
    if s["unit"] != unit_dir or not s["unit"].startswith(f"{unit}-") or file != expected:
        add("V08", "id", f'session "{s["id"]}" must live in {expected}')
    if s["id"] in planned and planned[s["id"]] != s["words"]:
        add("V08", "words", f"words differ from program.yaml: {planned[s['id']]}")
    elif planned and s["id"] not in planned:
        add("V08", "id", f'"{s["id"]}" is not in program.yaml')

    declared = set(s["words"]) | set(s.get("review", []))
    for key in ("words", "review"):
        for word_id in s.get(key, []):
            word = content.words.get(word_id)
            if word is None:
                add("V02", key, f'unknown word "{word_id}"')
            elif (
                word.unit != unit if key == "words" else unit_number(word.unit) > unit_number(unit)
            ):
                add("V02", key, f'"{word_id}" belongs to unit {word.unit}')

    shown: set[str] = set()  # images shown so far
    name_count = 0

    def check_word(where: str, word_id: str, must_be_shown: bool) -> None:
        word = content.words.get(word_id)
        if word is None:
            add("V02", where, f'unknown word "{word_id}"')
            return
        if word_id not in declared:
            add("V02", where, f'"{word_id}" is not declared in `words` or `review`')
        if must_be_shown and word_id in s["words"] and word.image not in shown:
            add("V07", where, f'"{word_id}" is asked before its picture is shown')

    def check_category(where: str, category: str) -> None:
        if category not in content.categories:
            add("V04", where, f'unknown phrase category "{category}"')

    def check_text(where: str, text: str) -> None:
        if line_words(text) > MAX_WORDS_PER_LINE:
            add("V05", where, f'"{text}" has more than {MAX_WORDS_PER_LINE} words')
        for placeholder in _PLACEHOLDER.findall(text):
            if placeholder != "name":
                add("V05", where, f"unknown placeholder {{{placeholder}}} in a written line")

    for step, actions in s["steps"].items():
        for i, action in enumerate(actions):
            ((kind, a),) = action.items()
            where = f"steps.{step}[{i}] ({kind})"
            if kind in ("say", "celebrate") and "text" in a:
                check_text(where, a["text"])
                name_count += "{name}" in a["text"]
            if kind == "say" and "phrase" in a:
                check_category(where, a["phrase"])
                variants = content.categories.get(a["phrase"], [])
                if any("{word}" in p.text for p in variants):
                    add("V04", where, f'"{a["phrase"]}" uses {{word}} but `say` has no word')
                name_count += bool(variants) and all("{name}" in p.text for p in variants)
            if kind == "show":
                if a["image"] not in media.images:
                    add("V03", where, f'image "{a["image"]}" is not in media.yaml')
                shown.add(a["image"])
            if kind == "ask_say":
                check_category(where, a["prompt"])
                check_word(where, a["word"], must_be_shown=True)
            if kind == "ask_touch":
                check_category(where, a["prompt"])
                for word_id in a["options"]:
                    check_word(where, word_id, must_be_shown=False)
                check_word(where, a["answer"], must_be_shown=True)
                if a["answer"] not in a["options"]:
                    add("V06", where, f'answer "{a["answer"]}" is not one of the options')
            if kind == "sing" and a["song"] not in media.songs:
                add("V03", where, f'song "{a["song"]}" is not in media.yaml')
            if kind == "video" and a["video"] not in media.videos:
                add("V03", where, f'video "{a["video"]}" is not in media.yaml')

    if name_count < MIN_NAME_PER_SESSION:
        add(
            "V09",
            "steps",
            f"the nickname is guaranteed {name_count} time(s), expected at least "
            f"{MIN_NAME_PER_SESSION}: write {{name}} in `say` text or use a category "
            "whose lines all contain it",
        )
    return issues
