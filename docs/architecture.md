# Architecture

## Current state

Atwood is a Python 3.14 FastAPI application packaged with uv. The ASGI entry
point is `atwood.api:app`; `create_app()` constructs the application and
defines the health endpoint, the MapLibre page, and the source-data API.

The MapLibre interface is rendered with Jinja templates in
`src/atwood/templates/` and local Bootstrap and custom assets in
`src/atwood/static/`. It preserves browser-local configuration and profiles.
`atwood.services.point_sources` reads Google Sheets, CSV, and SQLite sources,
validates field mappings, and produces GeoJSON for the map. The source root is
the current working directory by default and can be overridden with
`ATWOOD_DATA_ROOT`.

The production container installs the generated runtime-only `requirements.txt`
in a build stage, copies the bundled datasets and SQLite database, runs as a
non-root user, and serves the ASGI application with Uvicorn on port 8000.

## Application boundaries

Introduce boundaries only when a feature requires them:

- `domain/` for business rules and entities.
- `services/` for use cases that coordinate domain behavior.
- `adapters/` for CLI, HTTP, storage, and external integrations.

## Decisions

Record consequential technology, persistence, integration, or deployment choices in `docs/decisions/`.
