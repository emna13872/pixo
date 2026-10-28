# Protocol v1 (draft)

Status: **draft**, to be frozen with Viven. It replaces [protocol.md](protocol.md) (0.1,
WebSocket) once the app and the brain talk over LiveKit.

- **Transport:** LiveKit data channel, topic `pixo`, reliable delivery. Pixo's voice is an
  audio track published by the brain (Azure), not a message.
- **Envelope:** `{"v": 1, "type": "...", "id": "<uuid>", "ts": <unix ms>, "data": {...}}`.
- **Schema:** [`protocol/v1/messages.schema.json`](../protocol/v1/messages.schema.json), with
  one example per message in [`protocol/v1/examples/`](../protocol/v1/examples/). The brain's
  tests check every example against the schema.

| Direction | Type | data |
|---|---|---|
| brain → app | `face` | `state`: idle, talking, listening, thinking, happy, celebrate, encourage, surprised, sleeping |
| brain → app | `gesture` (**proposal**) | `gesture`: wave, thumbs_up, count_1 … count_5, point_nose, clap… |
| brain → app | `say_start` / `say_end` | `utterance_id`, `text` (start only) |
| brain → app | `visemes` | `utterance_id`, `frames`: [{`t_ms`, `viseme` 0–21}] (Azure viseme ids, for lip sync) |
| brain → app | `listening` | `open` |
| brain → app | `show` / `hide` | `image`, `layout`: full or with_pixo |
| brain → app | `ask_touch` | `activity_id`, `options` (image ids), `timeout_s` |
| brain → app | `award` | `kind`: star or sticker, `count` |
| brain → app | `play_video` | `video` |
| brain → app | `session_state` | `session_id`, `step` |
| brain → app | `sleep` | `reason` |
| app → brain | `hello` | `app_version`, `protocol_v`, `content_version` |
| app → brain | `touch` | `activity_id`, `choice` |
| app → brain | `video_ended` | `video` |
| app → brain | `app_state` | `state`: foreground or background |
| both | `error` | `code`, `message` |

## Open points for Viven

- The `gesture` message, for Pixo's on-screen hands.
- The fields inside each `data` above are our reading of the mission; the mission names them
  but does not define them all.
