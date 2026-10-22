"""Tests for the WebSocket server, with a fake app that follows docs/protocol.md."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from pixo_brain.server import PROTOCOL_VERSION, InvalidContentError, create_app
from pixo_brain.validate import DEFAULT_CONTENT


@pytest.fixture
def logs(tmp_path):
    return tmp_path / "logs"


@pytest.fixture
def client(logs):
    return TestClient(create_app(DEFAULT_CONTENT, logs))


def connect(client):
    ws = client.websocket_connect("/ws").__enter__()
    ws.send_json({"type": "hello", "protocol": PROTOCOL_VERSION, "app": "test"})
    welcome = ws.receive_json()
    assert welcome["type"] == "welcome"
    return ws


class FakeApp:
    """Answers every command; `child` gives the answers to `listen` / `wait_tap`, in order."""

    def __init__(self, ws, child: list):
        self.ws = ws
        self.child = list(child)
        self.commands: list[dict] = []

    def play(self) -> dict:
        while True:
            msg = self.ws.receive_json()
            if msg["type"] in ("session_ended", "error"):
                return msg
            if msg["type"] == "session_started":
                self.words = msg["words"]
                continue
            self.commands.append(msg)
            if msg["type"] == "listen":
                said = self.child.pop(0)
                self.ws.send_json({"type": "heard", "id": msg["id"], "transcripts": said})
            elif msg["type"] == "wait_tap":
                self.ws.send_json({"type": "tapped", "id": msg["id"], "word": self.child.pop(0)})
            else:
                self.ws.send_json({"type": "done", "id": msg["id"]})


# --- HTTP -------------------------------------------------------------------------------


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["protocol"] == PROTOCOL_VERSION
    assert {"id": "1.1", "title": "Hello!"} in body["sessions"]


def test_test_page_is_served(client):
    response = client.get("/")
    assert response.status_code == 200 and "Pixo test app" in response.text


def test_refuses_to_start_with_invalid_content(tmp_path):
    (tmp_path / "sessions").mkdir()
    (tmp_path / "words.yaml").write_text("[]", encoding="utf-8")
    (tmp_path / "phrases.yaml").write_text("{}", encoding="utf-8")
    with pytest.raises(InvalidContentError):
        create_app(tmp_path, tmp_path / "logs")


# --- Handshake --------------------------------------------------------------------------


def test_welcome_lists_sessions(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "hello", "protocol": PROTOCOL_VERSION})
        assert ws.receive_json()["sessions"][0]["id"] == "1.1"


def test_hello_must_come_first(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "start_session", "session": "1.1"})
        assert ws.receive_json()["code"] == "hello_first"


def test_protocol_mismatch(client):
    with client.websocket_connect("/ws") as ws:
        ws.send_json({"type": "hello", "protocol": "9.9"})
        assert ws.receive_json()["code"] == "protocol_mismatch"


def test_bad_json_is_reported_and_connection_survives(client):
    ws = connect(client)
    ws.send_text("not json")
    assert ws.receive_json()["code"] == "bad_message"
    ws.send_json({"type": "start_session", "session": "nope"})
    assert ws.receive_json()["code"] == "unknown_session"
    ws.close()


# --- Sessions ---------------------------------------------------------------------------

PERFECT = [["hello"], ["bye"], "hello", "bye"]


def test_full_session_1_1(client, logs):
    ws = connect(client)
    ws.send_json({"type": "start_session", "session": "1.1", "nickname": "Sara"})
    app = FakeApp(ws, PERFECT)
    end = app.play()
    assert end == {
        "type": "session_ended",
        "session": "1.1",
        "successes": 4,
        "asks": 4,
        "stopped": False,
    }
    assert app.words["hello"] == {"text": "hello", "image": "word_hello"}
    ids = [c["id"] for c in app.commands]
    assert ids == list(range(1, len(ids) + 1)), "ids must be 1, 2, 3…"
    says = [c["text"] for c in app.commands if c["type"] == "say"]
    assert says[0] == "Hello, Sara!" and says[-1] == "Bye-bye, Sara!"
    listen = next(c for c in app.commands if c["type"] == "listen")
    assert listen["language"] == "en-US" and listen["timeout_ms"] > 0
    ws.close()
    log = (logs / next(p.name for p in logs.iterdir())).read_text(encoding="utf-8")
    kinds = [json.loads(line)["kind"] for line in log.splitlines()]
    assert kinds[0] == "start" and kinds[-1] == "end" and "heard" in kinds


def test_two_sessions_on_one_connection(client):
    ws = connect(client)
    for _ in range(2):
        ws.send_json({"type": "start_session", "session": "1.1", "nickname": "Sara"})
        assert FakeApp(ws, PERFECT).play()["successes"] == 4
    ws.close()


def test_silent_child_and_nothing_touched(client):
    ws = connect(client)
    ws.send_json({"type": "start_session", "session": "1.1", "nickname": "Sara"})
    end = FakeApp(ws, [[]] * 6 + [None] * 6).play()
    assert (end["successes"], end["asks"]) == (0, 4)
    ws.close()


def test_tap_outside_choices_counts_as_nothing(client):
    ws = connect(client)
    ws.send_json({"type": "start_session", "session": "1.1", "nickname": "Sara"})
    end = FakeApp(ws, [["hello"], ["bye"], "banana", "hello", "bye"]).play()
    assert end["successes"] == 4  # the first touch question needed a 2nd try
    ws.close()


def test_stop_session(client):
    ws = connect(client)
    ws.send_json({"type": "start_session", "session": "1.1", "nickname": "Sara"})
    assert ws.receive_json()["type"] == "session_started"
    assert ws.receive_json()["type"] == "say"
    ws.send_json({"type": "stop_session"})
    end = ws.receive_json()
    assert end["type"] == "session_ended" and end["stopped"] is True
    ws.close()


def test_wrong_id_is_ignored(client):
    ws = connect(client)
    ws.send_json({"type": "start_session", "session": "1.1", "nickname": "Sara"})
    ws.receive_json()  # session_started
    first = ws.receive_json()
    ws.send_json({"type": "done", "id": first["id"] + 99})
    ws.send_json({"type": "done", "id": first["id"]})
    assert ws.receive_json()["id"] == first["id"] + 1
    ws.close()


def test_empty_nickname_falls_back(client):
    ws = connect(client)
    ws.send_json({"type": "start_session", "session": "1.1", "nickname": "  "})
    ws.receive_json()
    assert ws.receive_json()["text"] == "Hello, friend!"
    ws.close()


def test_disconnect_mid_session_is_logged(client, logs):
    ws = connect(client)
    ws.send_json({"type": "start_session", "session": "1.1", "nickname": "Sara"})
    ws.receive_json()
    ws.receive_json()
    ws.close()
    client.get("/health")  # let the server notice the disconnect
    log = next(logs.iterdir()).read_text(encoding="utf-8")
    assert '"kind": "disconnected"' in log
