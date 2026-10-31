# Atwood development instructions

## Commands

```bash
# Create or update the environment from the committed lockfile
uv sync

# Start the FastAPI development server
uv run fastapi dev src/atwood/api.py

# Run all tests
uv run pytest

# Run one test
uv run pytest tests/test_api.py::test_health

# Build the source distribution and wheel
uv build

# Regenerate the runtime-only compatibility requirements file
uv export --no-hashes --no-emit-project --no-dev -o requirements.txt
```

## Architecture

- The project is a Python 3.14 FastAPI application managed and built with `uv`; `pyproject.toml` configures the `uv_build` backend.
- The package uses the `src/` layout. `src/atwood/api.py` exposes the ASGI application as `atwood.api:app`, and `create_app()` builds it.
- Copilot cloud sessions reproduce the local environment with `uv sync --locked` in `.github/workflows/copilot-setup-steps.yml`.

## Repository conventions

- Use `uv` for Python environments and dependencies. Add dependencies with `uv add` or `uv add --dev`; do not edit `uv.lock` manually.
- `pyproject.toml` and `uv.lock` are authoritative. Regenerate the committed runtime-only `requirements.txt` with `uv export`.
- Keep package code under `src/atwood/`, matching the configured package layout.
- Python compatibility is `>=3.14`; `.python-version` selects Python 3.14 for local tooling.
