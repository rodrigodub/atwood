"""Parquet-backed saved map profiles and their cached GeoJSON."""

from __future__ import annotations

import os
import tempfile
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path

import fcntl
import pyarrow as pa
import pyarrow.parquet as pq

from atwood.services.point_sources import SourceConfigurationError, build_geojson

SCHEMA_VERSION = 1
_COLUMNS = (
    "schema_version", "record_type", "profile_id", "profile_name", "source_type",
    "sheet_url", "csv_path", "sqlite_path", "sqlite_table", "header_row",
    "point_id_field", "x_coord_field", "y_coord_field", "description_field",
    "point_color", "sort_order", "longitude", "latitude", "point_id",
    "description", "display_hex_colour", "created_at", "updated_at",
)
_SCHEMA = pa.schema([
    pa.field("schema_version", pa.int32()), pa.field("record_type", pa.string()),
    pa.field("profile_id", pa.string()), pa.field("profile_name", pa.string()),
    pa.field("source_type", pa.string()), pa.field("sheet_url", pa.string()),
    pa.field("csv_path", pa.string()), pa.field("sqlite_path", pa.string()),
    pa.field("sqlite_table", pa.string()), pa.field("header_row", pa.int32()),
    pa.field("point_id_field", pa.string()), pa.field("x_coord_field", pa.string()),
    pa.field("y_coord_field", pa.string()), pa.field("description_field", pa.string()),
    pa.field("point_color", pa.string()), pa.field("sort_order", pa.int32()),
    pa.field("longitude", pa.float64()), pa.field("latitude", pa.float64()),
    pa.field("point_id", pa.string()), pa.field("description", pa.string()),
    pa.field("display_hex_colour", pa.string()), pa.field("created_at", pa.string()),
    pa.field("updated_at", pa.string()),
])


class ProfileStoreError(ValueError):
    """A saved-profile store cannot safely be read or changed."""


class DuplicateProfileNameError(ProfileStoreError):
    """A profile name is already in use."""


class ProfileNotFoundError(ProfileStoreError):
    """The requested profile does not exist."""


def resolve_store_path() -> Path:
    configured = os.environ.get("ATWOOD_PROFILE_STORE")
    if configured:
        return Path(configured).expanduser().resolve()
    root = Path(os.environ.get("ATWOOD_DATA_ROOT", Path.cwd())).resolve()
    return root / "datasets" / "profiles.parquet"


class ProfileStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or resolve_store_path()

    def list_profiles(self) -> list[dict]:
        rows = self._read_rows()
        return [
            self._profile_summary(row)
            for row in rows
            if row["record_type"] == "profile"
        ]

    def get_profile(self, profile_id: str) -> dict:
        rows = self._read_rows()
        return self._get_profile_from_rows(rows, profile_id)

    def _get_profile_from_rows(self, rows: list[dict], profile_id: str) -> dict:
        profile = next(
            (row for row in rows if row["record_type"] == "profile" and row["profile_id"] == profile_id),
            None,
        )
        if profile is None:
            raise ProfileNotFoundError("Profile not found.")
        features = [row for row in rows if row["record_type"] == "feature" and row["profile_id"] == profile_id]
        features.sort(key=lambda row: row["sort_order"])
        return {
            **self._profile_summary(profile),
            "source_config": self._source_config(profile),
            "field_mapping": self._field_mapping(profile),
            "geojson": {
                "type": "FeatureCollection",
                "features": [
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [row["longitude"], row["latitude"]]},
                        "properties": {
                            "point_id": row["point_id"],
                            "description": row["description"],
                            "display_hex_colour": row["display_hex_colour"],
                        },
                    }
                    for row in features
                ],
            },
        }

    def create(self, profile_name: str, source_config: dict, field_mapping: dict) -> dict:
        name = _profile_name(profile_name)
        with self._mutation_lock():
            rows = self._read_rows()
            if any(row["record_type"] == "profile" and row["profile_name"].casefold() == name.casefold() for row in rows):
                raise DuplicateProfileNameError(f'A profile named "{name}" already exists.')
            geojson = build_geojson(source_config, field_mapping)
            now = _timestamp()
            profile_id = str(uuid.uuid4())
            rows.extend(self._profile_rows(profile_id, name, source_config, field_mapping, geojson, now, now))
            self._write_rows(rows)
            return self._get_profile_from_rows(rows, profile_id)

    def refresh(self, profile_id: str) -> dict:
        with self._mutation_lock():
            rows = self._read_rows()
            profile = next(
                (row for row in rows if row["record_type"] == "profile" and row["profile_id"] == profile_id),
                None,
            )
            if profile is None:
                raise ProfileNotFoundError("Profile not found.")
            geojson = build_geojson(self._source_config(profile), self._field_mapping(profile))
            retained = [row for row in rows if row["profile_id"] != profile_id]
            now = _timestamp()
            retained.extend(self._profile_rows(
                profile_id, profile["profile_name"], self._source_config(profile), self._field_mapping(profile),
                geojson, profile["created_at"], now,
            ))
            self._write_rows(retained)
            return self._get_profile_from_rows(retained, profile_id)

    def delete(self, profile_id: str) -> None:
        with self._mutation_lock():
            rows = self._read_rows()
            if not any(row["record_type"] == "profile" and row["profile_id"] == profile_id for row in rows):
                raise ProfileNotFoundError("Profile not found.")
            self._write_rows([row for row in rows if row["profile_id"] != profile_id])

    @contextmanager
    def _mutation_lock(self):
        """Serialize read-modify-replace mutations across application processes."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        lock_path = self.path.with_suffix(f"{self.path.suffix}.lock")
        with lock_path.open("a+") as lock_file:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)

    def _read_rows(self) -> list[dict]:
        if not self.path.exists():
            return []
        try:
            table = pq.read_table(self.path)
        except Exception as exc:
            raise ProfileStoreError("Saved profile store is corrupt; it was not changed.") from exc
        if set(table.column_names) != set(_COLUMNS):
            raise ProfileStoreError("Saved profile store has an unsupported schema; it was not changed.")
        try:
            rows = table.select(list(_COLUMNS)).to_pylist()
            if any(row["schema_version"] != SCHEMA_VERSION or row["record_type"] not in {"profile", "feature"} for row in rows):
                raise ValueError
            return rows
        except Exception as exc:
            raise ProfileStoreError("Saved profile store is corrupt; it was not changed.") from exc

    def _write_rows(self, rows: list[dict]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        table = pa.Table.from_pylist(rows, schema=_SCHEMA)
        descriptor, temporary_name = tempfile.mkstemp(prefix=".profiles-", suffix=".parquet", dir=self.path.parent)
        os.close(descriptor)
        temporary_path = Path(temporary_name)
        try:
            pq.write_table(table, temporary_path)
            os.replace(temporary_path, self.path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def _profile_rows(
        self, profile_id: str, name: str, source: dict, mapping: dict, geojson: dict, created: str, updated: str,
    ) -> list[dict]:
        metadata = _empty_row()
        metadata.update({
            "schema_version": SCHEMA_VERSION, "record_type": "profile", "profile_id": profile_id,
            "profile_name": name, **source, **mapping, "created_at": created, "updated_at": updated,
        })
        rows = [metadata]
        for sort_order, feature in enumerate(geojson["features"]):
            row = _empty_row()
            row.update({
                "schema_version": SCHEMA_VERSION, "record_type": "feature", "profile_id": profile_id,
                "profile_name": name, "sort_order": sort_order,
                "longitude": float(feature["geometry"]["coordinates"][0]),
                "latitude": float(feature["geometry"]["coordinates"][1]),
                **feature["properties"],
            })
            rows.append(row)
        return rows

    @staticmethod
    def _source_config(row: dict) -> dict:
        return {key: row[key] for key in ("source_type", "sheet_url", "csv_path", "sqlite_path", "sqlite_table", "header_row")}

    @staticmethod
    def _field_mapping(row: dict) -> dict:
        return {key: row[key] for key in ("point_id_field", "x_coord_field", "y_coord_field", "description_field", "point_color")}

    @staticmethod
    def _profile_summary(row: dict) -> dict:
        return {key: row[key] for key in ("profile_id", "profile_name", "created_at", "updated_at")}


def _empty_row() -> dict:
    return {column: None for column in _COLUMNS}


def _profile_name(value: object) -> str:
    name = str(value or "").strip()
    if not name or len(name) > 60:
        raise SourceConfigurationError("Provide a profile name of up to 60 characters.")
    return name


def _timestamp() -> str:
    return datetime.now(UTC).isoformat()
