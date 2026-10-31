# Atwood development instructions

## Project baseline

- Atwood is a Python application targeting Python 3.14.
- Use `uv` for all environment and dependency operations. Do not invoke `pip` directly.
- The package uses the `src/` layout; application code belongs in `src/atwood/`.
- The current executable is `atwood`, invoked with `uv run atwood`.

## Working conventions

- Start by reading `README.md`, `docs/project-structure.md`, and the relevant source and test files.
- Keep changes focused on the requested behavior. Do not add a framework, persistence layer, or external service unless the task requires it.
- Put tests in `tests/`, mirroring the package path and using `test_<behavior>.py` names.
- Prefer typed, small functions and explicit error handling. Avoid hidden global state and broad exception handling.
- Add dependencies only through `uv add` or `uv add --dev`, then commit the resulting `pyproject.toml` and `uv.lock` changes.
- Keep user-facing documentation in `README.md`; record architectural decisions in `docs/decisions/` only when a consequential choice is made.

## Commands

```bash
# Create or update the local environment
uv sync

# Run the application
uv run atwood

# Run tests once the test suite exists
uv run pytest
```

Run the narrowest relevant validation after a change. If a task adds tests or tooling, document its command here.
