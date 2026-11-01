import multiprocessing
import os
from pathlib import Path

import pytest

from atwood.services.profile_persistence import (
    DuplicateProfileNameError,
    ProfileStore,
    ProfileStoreError,
    resolve_store_path,
)

def _create_profile_in_process(store_path: str, data_root: str, profile_name: str) -> None:
    os.environ["ATWOOD_DATA_ROOT"] = data_root
    ProfileStore(Path(store_path)).create(profile_name, _source(), _mapping())


def _source() -> dict:
    return {
        "source_type": "csv", "sheet_url": "", "csv_path": "datasets/points.csv",
        "sqlite_path": "", "sqlite_table": "", "header_row": 1,
    }


def _mapping() -> dict:
    return {
        "point_id_field": "id", "x_coord_field": "longitude", "y_coord_field": "latitude",
        "description_field": "description", "point_color": "#123456",
    }


def _geojson() -> dict:
    return {"type": "FeatureCollection", "features": [{
        "type": "Feature", "geometry": {"type": "Point", "coordinates": [10.5, 20.5]},
        "properties": {"point_id": "A", "description": "Alpha", "display_hex_colour": "#123456"},
    }]}


def test_empty_store_and_round_trip(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.parquet")
    monkeypatch.setattr("atwood.services.profile_persistence.build_geojson", lambda *_: _geojson())

    assert store.list_profiles() == []
    created = store.create("Places", _source(), _mapping())

    loaded = store.get_profile(created["profile_id"])
    assert loaded["profile_name"] == "Places"
    assert loaded["source_config"] == _source()
    assert loaded["field_mapping"] == _mapping()
    assert loaded["geojson"] == _geojson()
    assert store.list_profiles() == [{
        "profile_id": created["profile_id"],
        "profile_name": "Places",
        "created_at": created["created_at"],
        "updated_at": created["updated_at"],
    }]


def test_empty_feature_collection_and_duplicate_name(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.parquet")
    monkeypatch.setattr(
        "atwood.services.profile_persistence.build_geojson",
        lambda *_: {"type": "FeatureCollection", "features": []},
    )
    created = store.create("Empty", _source(), _mapping())

    assert store.get_profile(created["profile_id"])["geojson"]["features"] == []
    with pytest.raises(DuplicateProfileNameError):
        store.create("empty", _source(), _mapping())


def test_corrupt_store_is_not_overwritten(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "profiles.parquet"
    path.write_bytes(b"not parquet")
    store = ProfileStore(path)
    monkeypatch.setattr("atwood.services.profile_persistence.build_geojson", lambda *_: _geojson())

    with pytest.raises(ProfileStoreError):
        store.create("Places", _source(), _mapping())
    assert path.read_bytes() == b"not parquet"


def test_delete_removes_metadata_and_features(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profiles.parquet")
    monkeypatch.setattr("atwood.services.profile_persistence.build_geojson", lambda *_: _geojson())
    created = store.create("Places", _source(), _mapping())

    store.delete(created["profile_id"])

    assert store.list_profiles() == []


def test_profile_store_environment_override(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    path = tmp_path / "custom.parquet"
    monkeypatch.setenv("ATWOOD_PROFILE_STORE", str(path))

    assert resolve_store_path() == path


def test_concurrent_creates_keep_both_profiles(tmp_path: Path) -> None:
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    (datasets / "points.csv").write_text(
        "id,longitude,latitude,description\nA,10.5,20.5,Alpha\n", encoding="utf-8"
    )
    store_path = tmp_path / "profiles.parquet"
    context = multiprocessing.get_context("spawn")
    processes = [
        context.Process(
            target=_create_profile_in_process,
            args=(str(store_path), str(tmp_path), name),
        )
        for name in ("One", "Two")
    ]
    for process in processes:
        process.start()
    for process in processes:
        process.join(timeout=20)

    assert all(process.exitcode == 0 for process in processes)
    assert {profile["profile_name"] for profile in ProfileStore(store_path).list_profiles()} == {"One", "Two"}
