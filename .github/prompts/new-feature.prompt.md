---
description: Plan and implement a small Atwood feature through the repository agent workflow.
---

Use the workflow in `AGENTS.md`.

Feature request: ${input:feature}

First, use the `planner` agent to write a scoped plan in `docs/plans/`. After the plan is approved, use the `implementer` agent for the smallest complete change. Then use `reviewer` and `tester` to validate it. Report the plan, changed files, and validation results.
