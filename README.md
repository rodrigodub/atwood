# Atwood

Every place has a story

> <small>Version 0.1</small> | <small>&copy;2026 Rodrigo Nobrega</small>

## Development

```bash
# Create the local Python 3.14 environment
uv sync

# Start the API server
uv run fastapi dev src/atwood/api.py

# Run all tests
uv run pytest

# Run the health endpoint test
uv run pytest tests/test_api.py::test_health
```

The health endpoint is available at `GET /health`.

## Docker

```bash
docker build -t atwood:local .
docker run --detach --name atwood --restart unless-stopped \
  --publish 127.0.0.1:8080:8000 atwood:local
```

The container serves the API at `http://localhost:8080` and reports its
status at `http://localhost:8080/health`.
