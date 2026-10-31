---
applyTo: "src/atwood/**/*.py,tests/**/*.py"
---

# Python application instructions

- Keep application behavior in `src/atwood/`; tests belong in the matching path below `tests/`.
- Add a `domain`, `services`, or `adapters` package only when the feature has a concrete responsibility for that boundary.
- Keep domain code independent of CLI, HTTP, storage, and external-service concerns.
- Use `uv add` or `uv add --dev` for dependency changes and update the lockfile through uv.
