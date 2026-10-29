# Content format, version 1 (draft)

Status: **draft**, to be frozen with Viven (mission task 3). Units are open-ended (u1, u2, … u50): the program grows until the child is fluent, so nothing in the format or the validator fixes their number. It replaces [schema.md](schema.md)
(version 0.1) once the brain plays v1 sessions. Until then, both formats are validated.

The shape of each file is defined by a JSON Schema in
[`protocol/v1/content/`](../protocol/v1/content/). The validator applies the schemas
to the YAML files, then runs the cross-checks listed below.

```sh
cd brain
uv run pixo-validate      # checks ../content, also run by CI on every pull request
```

## Files

| File | Schema | What it holds |
|---|---|---|
| `content/words.yaml` | `words.schema.json` | the words: id, text, unit, image id, 3 to 5 accepted forms |
| `content/phrases.yaml` | `phrases.schema.json` | Pixo's reusable lines, by category |
| `content/program.yaml` | `program.schema.json` | the units and their sessions, in play order, with the new words of each |
| `content/media.yaml` | `media.schema.json` | every image, song and video, with its file, source, licence and status |
| `content/units/<unit>/s<n>.yaml` | `session.schema.json` | one session, e.g. `units/u1-hello/s1.yaml` |
| `content/safety.yaml` | (milestone 2) | |

## A session

```yaml
schema_version: "1.0-draft"
id: u1-s1                 # <unit>-s<n>, matches the file path
unit: u1-hello
title: "Hello!"
words: [hello, bye]       # new words, the same as in program.yaml
review: []                # optional: earlier words practised again
duration_min: 8           # optional
steps:                    # all 7, in this order, each a list of actions
  hello:   [...]
  song:    [...]
  review:  [...]
  new:     [...]
  game:    [...]
  catchup: []             # always empty: the engine fills it with the words not yet validated
  bye:     [...]
```

An action is one key, the action's name, followed by its fields:

| Action | Fields | Meaning |
|---|---|---|
| `say` | `text` or `phrase` (a category), `face`, `gesture` (optional) | Pixo says a line |
| `show` | `image`, `face`, `gesture`, `layout` (`full` or `with_pixo`) (optional) | shows a picture |
| `ask_say` | `word`, `prompt` (a category) | asks the child to say a word, then listens |
| `ask_touch` | `prompt`, `options` (2 to 4 words), `answer`, `rounds` (1 to 5, optional) | asks the child to touch a picture |
| `sing` | `song` | Pixo sings a recorded song |
| `video` | `video` | reward video |
| `celebrate` | `text` (optional) | stars and a cheer |
| `gesture` | `gesture`, `face` (optional) | Pixo's on-screen hands make a gesture |

`face`: idle, talking, listening, thinking, happy, celebrate, encourage, surprised, sleeping.

`gesture` (**proposal**, not yet in protocol v1): wave, thumbs_up, thumbs_down,
count_1 … count_5, nod, head_shake, wave_bye, finger_wag, point, point_head, point_eyes, point_nose, point_mouth, point_ears,
show_hands, point_feet, clap, hands_up, high_five.

## Song lyrics on screen

A song in `media.yaml` may carry `timing`: one entry per lyrics line, with the second it starts
(`at`), its `text`, an optional picture shown beside it (`image`) and, optionally, the start of each
word (`words`) so the app can light words up as they are sung. Times are seconds from the start of
the audio file. The same timings are kept as a standard karaoke file next to the audio
(`songs/<id>.lrc`).

```yaml
timing:
  - at: 3.10
    text: "Hello, hello! Hello, hello!"
    image: word_hello
    words: [{at: 3.22, text: "Hello,"}, {at: 5.22, text: "hello!"}, ...]
```

## Cross-checks

| Code | Rule |
|---|---|
| V01 | the file matches its JSON Schema |
| V02 | every word exists, belongs to the right unit, and is declared in `words` or `review` |
| V03 | every image, song and video is listed in `media.yaml`, including each word's image |
| V04 | every phrase category exists; a `say` category never uses `{word}` |
| V05 | a written line has at most 5 words (the whole line) and no placeholder but `{name}` |
| V06 | an `ask_touch` answer is one of its options |
| V07 | a new word's picture is shown before the child is asked for it |
| V08 | the file path matches the session id, and its words match `program.yaml` |
| V09 | the nickname is guaranteed at least 3 times |
| V10 | a song's `timing` matches its `lyrics`, runs forward in time, and its pictures exist |

## Open points for Viven

- The `gesture` action and fields, and a matching `gesture` message in protocol v1.
- Whether an empty `review` step is allowed for a unit's first session (it is, for now).
- The 5-word rule on phrase templates: emna decided (2026-10-29) to keep it per sentence, so
  "Welcome back, {name}! Let's go on!" (6 words) passes there.
