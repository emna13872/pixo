"""Decide whether what the speech recognizer heard counts as the expected word."""

from __future__ import annotations

import re

from .content import Word

_NOT_SPOKEN = re.compile(r"[^\w\s'-]")


def normalize(text: str) -> str:
    """Lowercase and drop punctuation, keeping hyphens and apostrophes ("bye-bye", "let's")."""
    return " ".join(_NOT_SPOKEN.sub(" ", text.lower()).split())


def matches(word: Word, transcripts: list[str]) -> bool:
    """True if any transcript contains the word or one of its accepted variants.

    The recognizer returns several guesses (best first); the child counts as right if any guess
    matches. A transcript matches when one of its words is accepted ("hello pixo"), or when the
    whole transcript is ("bye bye" for "bye-bye").
    """
    accepted = {normalize(v) for v in [word.text, *word.accepted]}
    for transcript in transcripts:
        heard = normalize(transcript)
        if heard in accepted or any(token in accepted for token in heard.split()):
            return True
        if heard.replace(" ", "-") in accepted:
            return True
    return False
