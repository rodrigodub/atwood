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

# Run the source-data API coverage
uv run pytest tests/test_point_sources.py

# Build the source distribution and wheel
uv build

# Regenerate the runtime-only compatibility requirements file
uv export --no-hashes --no-emit-project --no-dev -o requirements.txt

# Refresh the Docker image and persistent container
docker build --tag atwood:local .
docker rm --force atwood 2>/dev/null || true
docker run --detach --name atwood --restart unless-stopped \
  --publish 127.0.0.1:8080:8000 atwood:local
```

## Architecture

- The project is a Python 3.14 FastAPI application managed and built with `uv`; `pyproject.toml` configures the `uv_build` backend.
- The package uses the `src/` layout. `src/atwood/api.py` exposes the ASGI application as `atwood.api:app`, and `create_app()` builds it.
- The MapLibre templates and local static assets are under `src/atwood/templates/` and `src/atwood/static/`. Preserve their browser-side configuration and profile behavior when changing the map UI.
- Use the `web-designer` agent for settings-panel and map-interface redesigns before implementation. Preserve IDs, Bootstrap attributes, local-storage keys, endpoint paths, and MapLibre identifiers unless their dependent JavaScript changes together.
- `atwood.services.point_sources` implements the Google Sheet, CSV, and SQLite inspection and GeoJSON endpoints. It resolves local files from the current working directory or `ATWOOD_DATA_ROOT`.
- Copilot cloud sessions reproduce the local environment with `uv sync --locked` in `.github/workflows/copilot-setup-steps.yml`.

## Repository conventions

- Use `uv` for Python environments and dependencies. Add dependencies with `uv add` or `uv add --dev`; do not edit `uv.lock` manually.
- `pyproject.toml` and `uv.lock` are authoritative. Regenerate the committed runtime-only `requirements.txt` with `uv export`.
- Keep package code under `src/atwood/`, matching the configured package layout.
- Python compatibility is `>=3.14`; `.python-version` selects Python 3.14 for local tooling.
- A `refresh container` or `testux` request rebuilds `atwood:local` and
  replaces the persistent `atwood` Docker container; do not use a container
  restart because it does not apply the rebuilt image.
