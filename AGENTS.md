# Atwood agent workflow

Use the agents in this order for feature work:

1. **planner** clarifies the outcome and writes an implementation plan in `docs/plans/`.
2. **web-designer** defines the user task and interaction design before visual changes to the map or settings area.
3. **implementer** delivers the smallest change that satisfies the approved plan.
4. **reviewer** examines the implementation for correctness, boundaries, and regressions.
5. **tester** adds or improves focused automated coverage and runs the relevant tests.

All agents must follow `.github/copilot-instructions.md`. See `docs/product-brief.md` for the product context and `docs/architecture.md` for current architectural decisions.

Use **web-designer** only when a request changes the map UI, settings panel,
responsive layout, or interaction design. It must preserve the frontend
contracts identified in `.github/instructions/frontend.instructions.md`.

## Container refresh

When instructed to **refresh container** or **testux**, rebuild the image from
the current workspace, replace the `atwood` container, and verify its health
endpoint:

```bash
docker build --tag atwood:local .
docker rm --force atwood 2>/dev/null || true
docker run --detach --name atwood --restart unless-stopped \
  --publish 127.0.0.1:8080:8000 \
  --mount type=bind,src="$(pwd)/datasets",dst=/app/datasets \
  atwood:local
curl --fail --silent --show-error http://127.0.0.1:8080/health
```

Keep the container's internal port at 8000 and use host port 8080 unless the
user requests a different available host port.
