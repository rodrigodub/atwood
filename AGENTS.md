# Atwood agent workflow

Use the agents in this order for feature work:

1. **planner** clarifies the outcome and writes an implementation plan in `docs/plans/`.
2. **implementer** delivers the smallest change that satisfies the approved plan.
3. **reviewer** examines the implementation for correctness, boundaries, and regressions.
4. **tester** adds or improves focused automated coverage and runs the relevant tests.

All agents must follow `.github/copilot-instructions.md`. See `docs/product-brief.md` for the product context and `docs/architecture.md` for current architectural decisions.

## Container refresh

When instructed to **refresh container**, rebuild the image from the current
workspace, replace the `atwood` container, and verify its health endpoint:

```bash
docker build --tag atwood:local .
docker rm --force atwood 2>/dev/null || true
docker run --detach --name atwood --restart unless-stopped \
  --publish 127.0.0.1:8080:8000 atwood:local
curl --fail --silent --show-error http://127.0.0.1:8080/health
```

Keep the container's internal port at 8000 and use host port 8080 unless the
user requests a different available host port.
