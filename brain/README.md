# Pixo brain

The Python part of Pixo: it loads `../content/`, checks it, and (from Step 2) runs the sessions.
See the root `README.md` for setup.

```powershell
uv sync                 # create the environment from uv.lock
uv run pixo-validate    # check content/ (words, phrases, sessions)
uv run pytest           # run the tests
uv run ruff check .     # lint
```
