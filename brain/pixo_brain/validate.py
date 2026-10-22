"""Check the pedagogical content against the rules in docs/schema.md.

Usage (from the brain/ folder):
    uv run pixo-validate                 # checks ../content
    uv run pixo-validate path/to/content
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from .content import (
    ASK_STEPS,
    UNITS,
    WORD_STEPS,
    AskTouchStep,
    Content,
    Issue,
    SayStep,
    Session,
    ShowStep,
    load_content,
)

DEFAULT_CONTENT = Path(__file__).resolve().parents[2] / "content"

MIN_VARIANTS, MAX_VARIANTS = 3, 5
MAX_WORDS_PER_SENTENCE = 5
MIN_NAME_PER_SESSION = 3
MIN_CHOICES, MAX_CHOICES = 2, 4
ALLOWED_PLACEHOLDERS = {"name", "word"}
FEEDBACK_CATEGORIES = {"praise", "encourage"}

_PLACEHOLDER = re.compile(r"\{([^}]*)\}")
_SENTENCE_END = re.compile(r"[.!?…]+")
_FORBIDDEN_FEEDBACK = re.compile(r"\b(no|wrong)\b", re.IGNORECASE)


# --- Words ----------------------------------------------------------------------------


def check_words(content: Content) -> list[Issue]:
    issues = []
    owner: dict[str, str] = {}  # spoken form -> word id
    for word in content.words.values():
        for form in {word.text.lower(), *(v.lower() for v in word.accepted)}:
            other = owner.setdefault(form, word.id)
            if other != word.id:
                issues.append(
                    Issue("W03", "words.yaml", word.id, f'"{form}" also matches the word "{other}"')
                )
        if not MIN_VARIANTS <= len(word.accepted) <= MAX_VARIANTS:
            issues.append(
                Issue(
                    "W02",
                    "words.yaml",
                    word.id,
                    f"{len(word.accepted)} accepted variants, expected "
                    f"{MIN_VARIANTS} to {MAX_VARIANTS}",
                )
            )
        if word.text not in word.accepted:
            issues.append(
                Issue("W02", "words.yaml", word.id, f'"{word.text}" itself must be accepted')
            )
    return issues


# --- Phrases --------------------------------------------------------------------------


def sentences(text: str) -> list[str]:
    """Split a phrase into sentences, with placeholders replaced by a single word."""
    text = _PLACEHOLDER.sub("X", text)
    return [s.strip() for s in _SENTENCE_END.split(text) if s.strip()]


def check_phrases(content: Content) -> list[Issue]:
    issues = []
    for phrase in content.phrases.values():
        for sentence in sentences(phrase.text):
            count = len(sentence.split())
            if count > MAX_WORDS_PER_SENTENCE:
                issues.append(
                    Issue(
                        "P02",
                        "phrases.yaml",
                        phrase.id,
                        f'"{sentence}" has {count} words (max {MAX_WORDS_PER_SENTENCE})',
                    )
                )
        if phrase.category in FEEDBACK_CATEGORIES and _FORBIDDEN_FEEDBACK.search(phrase.text):
            issues.append(
                Issue("P03", "phrases.yaml", phrase.id, 'feedback must never say "No" or "Wrong"')
            )
        for placeholder in _PLACEHOLDER.findall(phrase.text):
            if placeholder not in ALLOWED_PLACEHOLDERS:
                issues.append(
                    Issue(
                        "P04", "phrases.yaml", phrase.id, f"unknown placeholder {{{placeholder}}}"
                    )
                )
    return issues


# --- Sessions -------------------------------------------------------------------------


def _always_has(content: Content, step: SayStep, placeholder: str) -> bool:
    variants = content.phrases_for(step)
    return bool(variants) and all(placeholder in p.text for p in variants)


def _sometimes_has(content: Content, step: SayStep, placeholder: str) -> bool:
    return any(placeholder in p.text for p in content.phrases_for(step))


def check_session(content: Content, session: Session) -> list[Issue]:
    file = content.session_files[session.id]
    issues: list[Issue] = []

    def add(code: str, where: str, message: str) -> None:
        issues.append(Issue(code, file, where, message))

    # S03: words exist, and come from the right unit
    unit_index = UNITS.index(session.unit)
    for field_name, ids, allowed_units in (
        ("words", session.words, {session.unit}),
        ("review", session.review, set(UNITS[: unit_index + 1])),
    ):
        for word_id in ids:
            word = content.words.get(word_id)
            if word is None:
                add("S03", field_name, f'unknown word "{word_id}"')
            elif word.unit not in allowed_units:
                add("S03", field_name, f'"{word_id}" is from {word.unit}, not allowed here')

    declared = set(session.words) | set(session.review)
    shown: set[str] = set()
    name_count = 0

    for i, step in enumerate(session.steps):
        where = f"steps[{i}] ({step.type})"

        if isinstance(step, WORD_STEPS):
            used = [step.word, *(step.choices if isinstance(step, AskTouchStep) else [])]
            for word_id in used:
                if word_id not in content.words:
                    add("S03", where, f'unknown word "{word_id}"')
                elif word_id not in declared:
                    add("S04", where, f'"{word_id}" is not declared in `words` or `review`')

        if isinstance(step, ShowStep):
            shown.add(step.word)

        if isinstance(step, ASK_STEPS) and step.word in session.words and step.word not in shown:
            add("S05", where, f'"{step.word}" is asked before any `show` step for it')

        if isinstance(step, AskTouchStep):
            if not MIN_CHOICES <= len(step.choices) <= MAX_CHOICES:
                add(
                    "S06",
                    where,
                    f"{len(step.choices)} choices, expected {MIN_CHOICES} to {MAX_CHOICES}",
                )
            if len(set(step.choices)) != len(step.choices):
                add("S06", where, "the same choice appears twice")
            if step.word not in step.choices:
                add("S06", where, f'"{step.word}" must be one of the choices')

        if isinstance(step, SayStep):
            if not content.phrases_for(step):
                kind = "phrase id" if step.phrase is not None else "category"
                add("S07", where, f'unknown {kind} "{step.ref}"')
            if _sometimes_has(content, step, "{word}"):
                add("S08", where, f'"{step.ref}" uses {{word}} but a `say` step has no word')
            if _always_has(content, step, "{name}"):
                name_count += 1

    if name_count < MIN_NAME_PER_SESSION:
        add(
            "S09",
            "steps",
            f"the nickname is guaranteed {name_count} time(s), expected at least "
            f"{MIN_NAME_PER_SESSION}: use `say` steps whose phrase always contains {{name}}",
        )
    return issues


# --- Entry points ---------------------------------------------------------------------


def validate(root: Path) -> tuple[Content, list[Issue]]:
    """Load the content folder `root` and return it with every issue found."""
    content, issues = load_content(root)
    issues += check_words(content)
    issues += check_phrases(content)
    for session in content.sessions.values():
        issues += check_session(content, session)
    return content, issues


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check Pixo's pedagogical content.")
    parser.add_argument("content", nargs="?", type=Path, default=DEFAULT_CONTENT)
    args = parser.parse_args(argv)

    content, issues = validate(args.content)
    for issue in issues:
        print(issue)
    summary = (
        f"{len(content.words)} words, {len(content.phrases)} phrases, "
        f"{len(content.sessions)} session(s)"
    )
    if issues:
        print(f"\nFAILED: {len(issues)} problem(s) found ({summary})")
        return 1
    print(f"OK: content is valid ({summary})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
