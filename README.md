# Atwood

Every place has a story

> <small>Version 0.2</small> | <small>&copy;2026 Rodrigo Nobrega</small>

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

Atwood is a MapLibre map with server-saved profiles and cached data.
It can load points from a shared Google Sheet or bundled CSV and SQLite files,
then render the result as clustered GeoJSON.

- `GET /health` reports service health.
- `GET /source/inspect/` previews fields, rows, and SQLite tables for the
  selected source.
- `GET /source/data/` validates a field mapping and returns GeoJSON for the map.
- `GET`, `POST`, and `DELETE /profiles/` manage saved profiles; saved profiles
  load cached GeoJSON. `POST /profiles/{profile_id}/refresh` re-fetches a
  profile's original source.

Set `ATWOOD_DATA_ROOT` to use source data from another directory. By default,
the app reads the bundled `datasets/` directory and `db.sqlite3` from the
project root.

## Docker

```bash
docker build -t atwood:local .
mkdir -p datasets
# The container runs as UID/GID 10001 and needs to create profiles.parquet.
sudo chown 10001:10001 datasets
docker run --detach --name atwood --restart unless-stopped \
  --publish 127.0.0.1:8080:8000 \
  --mount type=bind,src="$(pwd)/datasets",dst=/app/datasets \
  atwood:local
```

The container serves the API at `http://localhost:8080` and reports its
status at `http://localhost:8080/health`.
The bind mount keeps `datasets/profiles.parquet` when the container is
replaced. The host directory must be writable by UID/GID 10001 (or otherwise
grant that user write access).
