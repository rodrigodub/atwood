# Atwood

Every place has a story

> <small>Version 0.3</small> | <small>Copyright &copy; 2026 Rodrigo Nobrega. All rights reserved.</small>

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

## Profile storage

Profiles are stored server-side in `datasets/profiles.parquet`, including the
source configuration, field mapping, and cached GeoJSON features. Creating or
refreshing a profile reads its source; loading an existing profile uses the
cache and does not contact the original source. Delete and refresh actions
update the same store.

Set `ATWOOD_PROFILE_STORE` to use an explicit Parquet file. Otherwise, the
store resolves to `ATWOOD_DATA_ROOT/datasets/profiles.parquet`; if
`ATWOOD_DATA_ROOT` is unset, it resolves from the project working directory.
The application serializes mutations, atomically replaces the store, and
refuses to overwrite a corrupt or unsupported file.

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
grant that user write access), including permission to create the adjacent
lock and temporary files. Do not copy a runtime profile store into the image;
always preserve it through the mounted `datasets/` directory.
