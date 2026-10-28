# Pixo

Pixo is a talking mascot that teaches spoken American English to children aged 5 to 8,
on an Android phone or tablet. V1 covers 3 units ("Hello!", "Colors", "My body") in 12 sessions.

- **How sessions are written:** [docs/content-v1.md](docs/content-v1.md) (v1 draft), [docs/schema.md](docs/schema.md) (v0.1, used by the app today)
- **How the app and the brain talk:** [docs/protocol.md](docs/protocol.md)

A full guide (setup, how to test, and the decisions behind the design) will be added here once
Prototype 0 works.

## Repository layout

| Folder | What's inside | Owner |
|---|---|---|
| `content/` | Pedagogical content: `words.yaml`, `phrases.yaml`, `sessions/*.yaml` | emna |
| `brain/` | Python brain: loads and checks the content, runs sessions (the only part that decides) | emna (Viven later) |
| `app/` | Android app (Kotlin, Jetpack Compose): displays, speaks, listens, never decides | (Step 4) |
| `docs/` | Technical references: session schema, app ↔ brain protocol | everyone |

## Everyday commands

From the `brain/` folder, in PowerShell:

```powershell
uv sync                 # first time (and after a dependency change): install the brain's libraries
uv run pixo-validate    # check all the content, after every edit in content/
uv run pixo-play 1.1 --name Sara   # play a session in the terminal: you type the child's answers
uv run pixo-serve       # run the brain as a server; test page at http://127.0.0.1:8000
uv run pytest           # run the tests
uv run ruff check .     # lint (code style and common mistakes)
```

## How we work

1. `main` always works. New work goes on a branch: `git switch -c step1-schema`.
2. Commit small steps with a clear message: `git commit -m "Add session 1.1"`.
3. Before merging: `uv run pixo-validate` and `uv run pytest` must pass.
4. Push the branch and open a pull request on GitHub, then merge it into `main`.

Never commit API keys: they go in a `.env` file, which Git ignores.
