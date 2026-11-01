from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atwood.api import app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    datasets = tmp_path / "datasets"
    datasets.mkdir()
    (datasets / "points.csv").write_text(
        "id,longitude,latitude,description\nA,10.5,20.5,Alpha\n", encoding="utf-8"
    )
    monkeypatch.setenv("ATWOOD_DATA_ROOT", str(tmp_path))
    return TestClient(app)


def _payload() -> dict:
    return {
        "profile_name": "Places",
        "source_config": {"source_type": "csv", "csv_path": "datasets/points.csv", "header_row": 1},
        "field_mapping": {
            "point_id_field": "id", "x_coord_field": "longitude", "y_coord_field": "latitude",
            "description_field": "description", "point_color": "#123456",
        },
    }


def test_profile_create_list_load_delete_and_cached_load(client: TestClient, tmp_path: Path) -> None:
    created = client.post("/profiles/", json=_payload())
    assert created.status_code == 201
    created_profile = created.json()
    profile_id = created_profile["profile_id"]
    assert client.get("/profiles/").json() == {"profiles": [{
        "profile_id": profile_id,
        "profile_name": "Places",
        "created_at": created_profile["created_at"],
        "updated_at": created_profile["updated_at"],
    }]}

    (tmp_path / "datasets" / "points.csv").unlink()
    loaded = client.get(f"/profiles/{profile_id}")
    assert loaded.status_code == 200
    assert loaded.json()["geojson"]["features"][0]["properties"]["point_id"] == "A"
    assert client.delete(f"/profiles/{profile_id}").status_code == 204
    assert client.get("/profiles/").json()["profiles"] == []


def test_profile_refresh_refetches_source(client: TestClient, tmp_path: Path) -> None:
    profile_id = client.post("/profiles/", json=_payload()).json()["profile_id"]
    (tmp_path / "datasets" / "points.csv").write_text(
        "id,longitude,latitude,description\nB,30.5,40.5,Bravo\n",
        encoding="utf-8",
    )

    response = client.post(f"/profiles/{profile_id}/refresh")

    assert response.status_code == 200
    assert response.json()["geojson"]["features"][0]["properties"]["point_id"] == "B"
    assert client.get(f"/profiles/{profile_id}").json()["geojson"] == response.json()["geojson"]


def test_profile_api_reports_validation_conflicts_and_missing_profiles(client: TestClient) -> None:
    assert client.post("/profiles/", json=[]).status_code == 400

    created = client.post("/profiles/", json=_payload())
    assert created.status_code == 201
    duplicate = client.post("/profiles/", json=_payload())
    assert duplicate.status_code == 409
    assert 'A profile named "Places" already exists.' == duplicate.json()["error"]

    for method, path in (
        ("get", "/profiles/missing"),
        ("post", "/profiles/missing/refresh"),
        ("delete", "/profiles/missing"),
    ):
        response = getattr(client, method)(path)
        assert response.status_code == 404
        assert response.json() == {"error": "Profile not found."}


def test_profile_api_leaves_a_corrupt_store_unchanged(client: TestClient, tmp_path: Path) -> None:
    store_path = tmp_path / "datasets" / "profiles.parquet"
    corrupt_contents = b"not parquet"
    store_path.write_bytes(corrupt_contents)

    response = client.post("/profiles/", json=_payload())

    assert response.status_code == 500
    assert response.json()["error"] == "Saved profile store is corrupt; it was not changed."
    assert store_path.read_bytes() == corrupt_contents


def test_page_contains_server_profile_flow(client: TestClient) -> None:
    page = client.get("/")

    assert page.status_code == 200
    assert 'id="source-selection-modal"' in page.text
    assert 'id="field-mapping-modal"' in page.text
    assert 'id="profile-name-modal"' in page.text
    assert "1. Select source" in page.text
    assert "2. Map fields" in page.text
    assert "3. Save profile" in page.text
    assert 'id="wizard-inspect-source-button"' in page.text
    assert 'id="wizard-validate-mapping-button"' in page.text
    assert 'id="new-profile-button"' in page.text
    assert "newOption.textContent = 'New +'" in page.text
    assert "profileDropdownMenu.appendChild(newItem);" in page.text
    assert "localStorage" not in page.text
