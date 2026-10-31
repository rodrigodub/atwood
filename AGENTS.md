# Atwood agent workflow

Use the agents in this order for feature work:

1. **planner** clarifies the outcome and writes an implementation plan in `docs/plans/`.
2. **implementer** delivers the smallest change that satisfies the approved plan.
3. **reviewer** examines the implementation for correctness, boundaries, and regressions.
4. **tester** adds or improves focused automated coverage and runs the relevant tests.

All agents must follow `.github/copilot-instructions.md`. See `docs/product-brief.md` for the product context and `docs/architecture.md` for current architectural decisions.
