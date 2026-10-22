# Pixo brain

The Python part of Pixo: it loads `../content/`, checks it, and (from Step 2) runs the sessions.
See the root `README.md` for setup.

```powershell
uv sync                 # create the environment from uv.lock
uv run pixo-validate    # check content/ (words, phrases, sessions)
uv run pytest           # run the tests
uv run ruff check .     # lint
```

## Code map

| File | Role |
|---|---|
| `pixo_brain/content.py` | Reads `content/*.yaml` into typed objects |
| `pixo_brain/validate.py` | The pedagogy rules (`pixo-validate`) |
| `pixo_brain/engine.py` | Plays a session step by step: the only place that decides |
| `pixo_brain/matching.py` | Is what the recognizer heard the expected word? |
| `pixo_brain/channels.py` | How the engine talks to the outside: terminal, tests, the app |
| `pixo_brain/play.py` | Text mode (`pixo-play`) |
| `pixo_brain/server.py` | WebSocket server for the app (`pixo-serve`), protocol in `docs/protocol.md` |
| `pixo_brain/static/test_app.html` | Test page: a fake app in the browser, served at `/` |

Every session played writes a log to `../logs/` (one JSON line per event). Logs are never committed.
