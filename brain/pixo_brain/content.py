"""Load the pedagogical content (words, phrases, sessions) into typed objects.

Loading never stops at the first problem: every problem becomes an `Issue`, so the
validator can report all of them in one run.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Annotated, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, ValidationError, model_validator

Unit = Literal["u1", "u2", "u3"]
UNITS: tuple[str, ...] = ("u1", "u2", "u3")


# --- YAML -----------------------------------------------------------------------------


class _PixoLoader(yaml.SafeLoader):
    """SafeLoader where only true/false are booleans.

    Plain YAML 1.1 turns `yes`, `no`, `on`, `off` into booleans, which would break the
    words "yes" and "no". With this loader, `words: [yes, no]` stays two strings.
    """


_PixoLoader.yaml_implicit_resolvers = {
    key: [(tag, regexp) for tag, regexp in resolvers if tag != "tag:yaml.org,2002:bool"]
    for key, resolvers in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_PixoLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def load_yaml(path: Path) -> object:
    with path.open(encoding="utf-8") as f:
        return yaml.load(f, Loader=_PixoLoader)  # a SafeLoader subclass: never runs code


# --- Models ---------------------------------------------------------------------------


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Word(_Strict):
    id: str
    text: str
    unit: Unit
    image: str
    accepted: list[str]


class PhraseEntry(_Strict):
    id: str
    text: str


@dataclass(frozen=True)
class Phrase:
    id: str
    text: str
    category: str


class SayStep(_Strict):
    """Exactly one of `phrase` (a phrase id) or `category` (a random variant of a category)."""

    type: Literal["say"]
    phrase: str | None = None
    category: str | None = None

    @model_validator(mode="after")
    def _one_source(self) -> SayStep:
        if (self.phrase is None) == (self.category is None):
            raise ValueError("a `say` step needs exactly one of `phrase` or `category`")
        return self

    @property
    def ref(self) -> str:
        return self.phrase if self.phrase is not None else self.category  # type: ignore[return-value]


class ShowStep(_Strict):
    type: Literal["show"]
    word: str


class AskSayStep(_Strict):
    type: Literal["ask_say"]
    word: str
    tries: int = Field(default=3, ge=1, le=3)


class AskTouchStep(_Strict):
    type: Literal["ask_touch"]
    word: str
    choices: list[str]
    tries: int = Field(default=3, ge=1, le=3)


Step = Annotated[SayStep | ShowStep | AskSayStep | AskTouchStep, Field(discriminator="type")]
WORD_STEPS = (ShowStep, AskSayStep, AskTouchStep)
ASK_STEPS = (AskSayStep, AskTouchStep)


class Session(_Strict):
    schema_version: Literal["0.1"]
    id: str
    unit: Unit
    title: str
    words: list[str] = Field(min_length=1)
    review: list[str] = Field(default_factory=list)
    steps: list[Step] = Field(min_length=1)


# --- Issues ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Issue:
    code: str
    file: str
    where: str
    message: str

    def __str__(self) -> str:
        where = f" {self.where}:" if self.where else ""
        return f"{self.file}:{where} [{self.code}] {self.message}"


# --- Content --------------------------------------------------------------------------


@dataclass
class Content:
    root: Path
    words: dict[str, Word] = field(default_factory=dict)
    phrases: dict[str, Phrase] = field(default_factory=dict)
    categories: dict[str, list[Phrase]] = field(default_factory=dict)
    sessions: dict[str, Session] = field(default_factory=dict)
    # file name (relative to root) of each session, by session id
    session_files: dict[str, str] = field(default_factory=dict)

    def phrases_for(self, step: SayStep) -> list[Phrase]:
        """Phrases a `say` step can produce: one for a phrase id, all variants for a category."""
        if step.phrase is not None:
            return [self.phrases[step.phrase]] if step.phrase in self.phrases else []
        return self.categories.get(step.category or "", [])


def _pydantic_issues(err: ValidationError, file: str, prefix: str) -> list[Issue]:
    issues = []
    for e in err.errors():
        loc = ".".join(str(p) for p in e["loc"])
        where = f"{prefix}.{loc}" if prefix and loc else prefix or loc
        issues.append(Issue("S01", file, where, e["msg"]))
    return issues


def _load_words(content: Content, issues: list[Issue]) -> None:
    file = "words.yaml"
    raw = load_yaml(content.root / file)
    if not isinstance(raw, list):
        issues.append(Issue("S01", file, "", "expected a list of words"))
        return
    for i, item in enumerate(raw):
        try:
            word = Word.model_validate(item)
        except ValidationError as err:
            issues += _pydantic_issues(err, file, f"[{i}]")
            continue
        if word.id in content.words:
            issues.append(Issue("W01", file, word.id, "duplicate word id"))
            continue
        content.words[word.id] = word


def _load_phrases(content: Content, issues: list[Issue]) -> None:
    file = "phrases.yaml"
    raw = load_yaml(content.root / file)
    if not isinstance(raw, dict):
        issues.append(Issue("S01", file, "", "expected categories, each with a list of phrases"))
        return
    entries = TypeAdapter(list[PhraseEntry])
    for category, items in raw.items():
        try:
            parsed = entries.validate_python(items)
        except ValidationError as err:
            issues += _pydantic_issues(err, file, str(category))
            continue
        content.categories[category] = []
        for entry in parsed:
            if entry.id in content.phrases:
                issues.append(Issue("P01", file, entry.id, "duplicate phrase id"))
                continue
            phrase = Phrase(entry.id, entry.text, category)
            content.phrases[entry.id] = phrase
            content.categories[category].append(phrase)


def _load_sessions(content: Content, issues: list[Issue]) -> None:
    folder = content.root / "sessions"
    for path in sorted(folder.glob("*.yaml")):
        file = f"sessions/{path.name}"
        try:
            session = Session.model_validate(load_yaml(path))
        except yaml.YAMLError as err:
            issues.append(Issue("S01", file, "", f"invalid YAML: {err}"))
            continue
        except ValidationError as err:
            issues += _pydantic_issues(err, file, "")
            continue
        if session.id != path.stem:
            issues.append(
                Issue(
                    "S02", file, "id", f'id "{session.id}" must match the file name "{path.stem}"'
                )
            )
        if session.id in content.sessions:
            issues.append(Issue("S02", file, "id", f'duplicate session id "{session.id}"'))
            continue
        content.sessions[session.id] = session
        content.session_files[session.id] = file


def load_content(root: Path) -> tuple[Content, list[Issue]]:
    """Load everything under `root` (the `content/` folder). Returns the content and load issues."""
    content = Content(root=root)
    issues: list[Issue] = []
    for loader, name in (
        (_load_words, "words.yaml"),
        (_load_phrases, "phrases.yaml"),
        (_load_sessions, "sessions"),
    ):
        try:
            loader(content, issues)
        except FileNotFoundError:
            issues.append(Issue("S01", name, "", "not found"))
        except yaml.YAMLError as err:
            issues.append(Issue("S01", name, "", f"invalid YAML: {err}"))
    return content, issues
