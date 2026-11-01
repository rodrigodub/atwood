# Project structure

Atwood starts as a small Python application. Keep the current layout until a feature establishes a need for a new boundary:

```text
.
├── AGENTS.md                          # Agent roles and delivery workflow
├── .github/
│   ├── agents/                        # Specialized Copilot agent profiles
│   │   ├── planner.agent.md           # Breaks features into tasks, no code edits
│   │   ├── implementer.agent.md       # Writes code from the plan
│   │   ├── web-designer.agent.md      # Designs map and settings interactions
│   │   ├── reviewer.agent.md          # Reviews for quality, security, tests
│   │   └── tester.agent.md            # Writes and runs tests
│   ├── copilot-instructions.md        # Shared agent conventions
│   ├── instructions/
│   │   ├── frontend.instructions.md   # Applies only to matching files (applyTo glob)
│   │   └── backend.instructions.md
│   ├── prompts/
│   │   ├── new-feature.prompt.md      # Reusable /new-feature slash command
│   │   └── fix-bug.prompt.md
│   ├── skills/
│   │   └── python-delivery/SKILL.md   # Portable feature-delivery workflow
│   └── workflows/                     # Cloud-agent setup and CI workflows
├── docs/
│   ├── decisions/                     # Accepted architecture decision records
│   ├── project-structure.md    # This guide
│   ├── product-brief.md        # What you're building and why
│   ├── architecture.md         # Stack, structure, key decisions
│   └── plans/                  # Planner agent writes its output here
├── src/
│   └── atwood/                 # Application package
│       ├── domain/             # Business entities and rules
│       ├── services/           # Use cases that coordinate domain work
│       ├── adapters/           # CLI, HTTP, storage, and external integrations
│       └── __init__.py         # Public package entry point
├── tests/                      # Tests mirroring src/atwood/
├── pyproject.toml              # Python metadata and dependencies
└── uv.lock                     # Resolved dependency lockfile
```

## Boundary rules

- `domain/` must not import delivery or infrastructure code.
- `services/` coordinates domain behavior and depends on abstractions, not concrete adapters.
- `adapters/` translates external input and output and owns integration-specific concerns.
- Keep the package flat while the application is small; create a boundary only when it has a concrete responsibility.
- Create `docs/decisions/` and add a short decision record when selecting a framework, database, external API, or deployment model.
