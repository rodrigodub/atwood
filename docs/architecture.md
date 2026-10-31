# Architecture

## Current state

Atwood is a Python 3.14 FastAPI application packaged with uv. The ASGI entry
point is `atwood.api:app`; `create_app()` constructs the application and
defines the health endpoint.

The production container installs the generated runtime-only `requirements.txt`
in a build stage, runs as a non-root user, and serves the ASGI application with
Uvicorn on port 8000.

## Application boundaries

Introduce boundaries only when a feature requires them:

- `domain/` for business rules and entities.
- `services/` for use cases that coordinate domain behavior.
- `adapters/` for CLI, HTTP, storage, and external integrations.

## Decisions

Record consequential technology, persistence, integration, or deployment choices in `docs/decisions/`.
