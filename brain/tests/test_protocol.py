from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

PROTOCOL = Path(__file__).resolve().parents[2] / "protocol" / "v1"


def validator() -> Draft202012Validator:
    schemas = [PROTOCOL / "messages.schema.json", *sorted((PROTOCOL / "content").glob("*.json"))]
    resources = [Resource.from_contents(json.loads(p.read_text(encoding="utf-8"))) for p in schemas]
    registry = Registry().with_resources((r.contents["$id"], r) for r in resources)
    return Draft202012Validator(resources[0].contents, registry=registry)


EXAMPLES = sorted((PROTOCOL / "examples").glob("*.json"))


@pytest.mark.parametrize("path", EXAMPLES, ids=[p.stem for p in EXAMPLES])
def test_examples_are_valid(path):
    message = json.loads(path.read_text(encoding="utf-8"))
    assert [e.message for e in validator().iter_errors(message)] == []


def test_wrong_data_for_type_is_rejected():
    message = {"v": 1, "type": "face", "id": "x", "ts": 0, "data": {"state": "angry"}}
    assert list(validator().iter_errors(message))


def test_unknown_gesture_is_rejected():
    message = {"v": 1, "type": "gesture", "id": "x", "ts": 0, "data": {"gesture": "moonwalk"}}
    assert list(validator().iter_errors(message))
