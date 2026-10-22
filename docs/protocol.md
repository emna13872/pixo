# App ↔ brain protocol, version 0.1

Status: **draft**, frozen as v1 once Prototype 0 plays session 1.1 on the phone.
The brain decides everything; the app displays, speaks, listens and reports what the child did.

## 1. Transport

- **WebSocket**, JSON text messages, one message per frame.
- Address: `ws://<pc>:8000/ws`
  - over USB (development): `adb reverse tcp:8000 tcp:8000`, then the app uses `ws://127.0.0.1:8000/ws`;
  - over Wi-Fi: start the brain with `--host 0.0.0.0`, the app uses the PC's IP address.
- Every message is an object with a `type`.
- **Later (LiveKit):** the same JSON messages will travel over the LiveKit data channel, and `say` /
  `listen` will be replaced by the brain's own audio (Azure voice, Deepgram recognition). The message
  types and the request/answer pattern stay the same.

## 2. The pattern: command → answer

The brain sends **commands**, one at a time. Each command has a number `id`. The app does it, then
answers with the **same `id`**. The brain waits for that answer before sending the next command.

```
brain → app   {"type": "say", "id": 7, "text": "Hello, Sara!"}
app → brain   {"type": "done", "id": 7}            (after the sentence was fully spoken)
```

So the app never needs to know what comes next, and never decides anything.

## 3. Connection and session

```
app → brain   {"type": "hello", "protocol": "0.1", "app": "pixo-android 0.1.0"}
brain → app   {"type": "welcome", "protocol": "0.1", "sessions": [{"id": "1.1", "title": "Hello!"}]}

app → brain   {"type": "start_session", "session": "1.1", "nickname": "Sara"}
brain → app   {"type": "session_started", "session": "1.1", "title": "Hello!",
               "words": {"hello": {"text": "hello", "image": "word_hello"}, ...}}
   ... commands and answers ...
brain → app   {"type": "session_ended", "session": "1.1", "successes": 4, "asks": 4}
```

- `hello` must be the first message. If the `protocol` versions don't match, the brain answers with an
  `error` and closes the connection.
- `words` in `session_started` lists every word of the session (`words` + `review`) with its image id,
  so commands can refer to words by id.
- After `session_ended`, the app may send another `start_session`.
- The app may send `{"type": "stop_session"}` at any time. The brain stops and answers
  `session_ended` with `"stopped": true`.

## 4. Commands (brain → app)

| type | fields | the app… | answer |
|---|---|---|---|
| `say` | `text` | speaks `text` (American English, slow) | `done` when finished speaking |
| `show` | `words` (list of word ids), `highlight` (word id or `null`) | displays those images, the highlighted one glowing | `done` |
| `clear` | – | removes the images | `done` |
| `animate` | `name`: `show`, `happy`, `dance` | plays Pixo's animation | `done` (may answer right away) |
| `listen` | `language` (`"en-US"`), `timeout_ms` | listens to the child | `heard` |
| `wait_tap` | `choices` (word ids), `timeout_ms` | waits for the child to touch one image | `tapped` |

## 5. Answers (app → brain)

| type | fields | meaning |
|---|---|---|
| `done` | `id` | the command is finished |
| `heard` | `id`, `transcripts` (list of strings, best first) | what the recognizer heard; `[]` = silence or nothing understood |
| `tapped` | `id`, `word` (word id or `null`) | the touched image; `null` = nothing touched before `timeout_ms` |

An answer whose `id` is not the one the brain is waiting for is ignored (and logged).

## 6. Errors

```
brain → app   {"type": "error", "code": "unknown_session", "message": "..."}
```

| code | when |
|---|---|
| `bad_message` | not JSON, or no / unknown `type` |
| `protocol_mismatch` | `hello` with another protocol version (the brain closes the connection) |
| `hello_first` | any message before `hello` |
| `unknown_session` | `start_session` with a session id that doesn't exist |

If the connection drops in the middle of a session, the brain stops the session and writes it in the log.

## 7. Changelog
- **0.1** (2026-10-22): first draft.
