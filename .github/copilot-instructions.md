# Atwood development instructions

## Commands

```bash
# Create or update the environment from the committed lockfile
uv sync

# Run the console application
uv run atwood

# Build the source distribution and wheel
uv build
```

## Architecture

- The project is a Python 3.14 application managed and built with `uv`; `pyproject.toml` configures the `uv_build` backend.
- The package uses the `src/` layout. The `atwood` command configured in `pyproject.toml` resolves to `atwood:main`, currently defined in `src/atwood/__init__.py`.
- Copilot cloud sessions reproduce the local environment with `uv sync --locked` in `.github/workflows/copilot-setup-steps.yml`.

## Repository conventions

- Use `uv` for Python environments and dependencies. Add dependencies with `uv add` or `uv add --dev`; do not edit `uv.lock` manually.
- Keep package code under `src/atwood/`, matching the configured package layout.
- Python compatibility is `>=3.14`; `.python-version` selects Python 3.14 for local tooling.
