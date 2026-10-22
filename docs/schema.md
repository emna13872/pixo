# Session schema, version 0.1

Status: **draft**. It gets frozen (becomes v1) when Prototype 0 plays session 1.1 end to end.
Owner: emna (covering for Viven). Any change to this file goes in the same pull request as the code that implements it.

A session is a YAML file in `content/sessions/<id>.yaml`. The brain reads it, together with
`content/words.yaml` and `content/phrases.yaml`. The validator checks all three files
(see "Validation" below).

## 1. Session file

```yaml
schema_version: "0.1"   # always "0.1" for now
id: "1.1"               # unique, quoted, matches the file name
unit: u1                # u1 | u2 | u3
title: "Hello!"         # shown to the parent/teacher, not to the child
words: [hello, bye]     # NEW words taught in this session (from words.yaml)
review: []              # optional: words from earlier sessions used again here
steps:                  # played top to bottom
  - type: show
    word: hello
```

| Field | Required | Rule |
|---|---|---|
| `schema_version` | yes | `"0.1"` |
| `id` | yes | Same as the file name without `.yaml` |
| `unit` | yes | `u1`, `u2` or `u3` |
| `title` | yes | Free text |
| `words` | yes | At least 1 word id, all from this session's unit |
| `review` | no | Word ids from this unit or earlier units |
| `steps` | yes | At least 1 step |

Unknown fields are refused, so a typo like `wrod:` is caught instead of silently ignored.

## 2. Step types

Every step has a `type`. Version 0.1 has the 4 core types. The game mechanics (Silly Pixo,
Paint Pixo, etc.) come in 0.2, once emna has chosen them.

### `say`: Pixo says a phrase
```yaml
- type: say
  phrase: greet_hello      # a phrase id → exactly that phrase
- type: say
  category: praise         # a category → one variant picked at random
```
A `say` step has exactly one of `phrase` or `category`. They are separate keys because
`phrases.yaml` uses some names both ways (the category `again` contains the phrase id `again`), so a
single key would be ambiguous.

### `show`: introduce a word (the "show before asking" rule)
```yaml
- type: show
  word: hello
```
At runtime: an attention phrase ("Look!"), then the word's image appears, Pixo says the word **twice**
and does the matching animation.

### `ask_say`: the child says the word
```yaml
- type: ask_say
  word: hello
  tries: 3                 # optional, default 3, between 1 and 3
```
At runtime: "Your turn!" + an `ask_say` phrase ("Say hello!"), then Pixo listens. The answer counts as
right if the speech recognizer returns the word or one of its `accepted` variants.
- Right: a `praise` phrase.
- Not right / silence: an `encourage` phrase, Pixo shows and says the word again, and the child tries again.
- After the last try: "Good try!" and the session goes on. The child is never blocked, and Pixo never says "No!".

### `ask_touch`: the child touches the right image
```yaml
- type: ask_touch
  word: hello
  choices: [hello, bye]    # 2 to 4 images, including `word`
  tries: 3                 # optional, default 3
```
At runtime: the images appear, Pixo says an `ask_touch` phrase ("Touch hello!"). Right image → praise.
Wrong image → encourage, Pixo says the word again and highlights the right image.

## 3. Placeholders in phrases
- `{name}`: the child's nickname
- `{word}`: the word of the current step (only allowed in steps that have a `word`)

## 4. Validation

Run from the `brain/` folder:
```powershell
uv run pixo-validate
```
It prints every problem with its file and place, and exits with an error if there is any.
Each rule has a code, so the tests and the docs can refer to it.

| Code | Rule |
|---|---|
| **Words** | |
| W01 | Word ids are unique |
| W02 | 3 to 5 `accepted` variants per word, including the word itself |
| W03 | No variant matches another word of the list (e.g. `no` must not accept `nose`) |
| **Phrases** | |
| P01 | Phrase ids are unique |
| P02 | 1 to 5 words per sentence (`{name}` / `{word}` count as one word) |
| P03 | Never "No!" or "Wrong!" in `praise` or `encourage` |
| P04 | Only `{name}` and `{word}` placeholders |
| **Sessions** | |
| S01 | Structure matches this document (types, required fields, no unknown fields) |
| S02 | `id` matches the file name, and ids are unique |
| S03 | Every word used exists in `words.yaml`; `words` are from the session's unit, `review` from this or an earlier unit |
| S04 | Every word used in a step is declared in `words` or `review` |
| S05 | Show before asking: a word in `words` gets a `show` step before any `ask_say` / `ask_touch` on it |
| S06 | `ask_touch`: 2 to 4 different `choices`, and `word` is one of them |
| S07 | Every `phrase` is a known phrase id, every `category` a known category; a `say` step has exactly one of them |
| S08 | `{word}` is only used in steps that have a word |
| S09 | The nickname is **guaranteed** at least 3 times: count of `say` steps whose phrase (or every variant of whose category) contains `{name}` |

Not checked automatically yet: "only words of the unit or phrase templates" (needs an allowed-vocabulary
list), "slow speech rate" (a voice setting).

## 5. Changelog
- **0.1** (2026-10-22): first draft. Core step types `say`, `show`, `ask_say`, `ask_touch`.
