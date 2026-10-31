# Architecture

## Current state

Atwood is a Python 3.14 console application packaged with uv. The `atwood` command invokes `atwood:main`.

## Application boundaries

Introduce boundaries only when a feature requires them:

- `domain/` for business rules and entities.
- `services/` for use cases that coordinate domain behavior.
- `adapters/` for CLI, HTTP, storage, and external integrations.

## Decisions

Record consequential technology, persistence, integration, or deployment choices in `docs/decisions/`.
