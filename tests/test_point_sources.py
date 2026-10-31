import sqlite3
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from atwood.api import app
from atwood.services.point_sources import _google_sheet_csv_url


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    datasets_dir = tmp_path / "datasets"
    datasets_dir.mkdir()
    (datasets_dir / "points.csv").write_text(
        "point_code,x_coord,y_coord,details,display_colour\n"
        "A1,10.5,20.5,Alpha,#123abc\n"
        "B2,11.5,21.5,Bravo,#abcdef\n",
        encoding="utf-8",
    )

    with sqlite3.connect(tmp_path / "points.sqlite3") as connection:
        connection.execute(
            "CREATE TABLE places (code TEXT, lng REAL, lat REAL, summary TEXT, colour TEXT)"
        )
        connection.execute(
            "INSERT INTO places VALUES (?, ?, ?, ?, ?)",
            ("C3", 30.5, 40.5, "Charlie", "#112233"),
        )

    monkeypatch.setenv("ATWOOD_DATA_ROOT", str(tmp_path))
    return TestClient(app)


def test_home_page_renders(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert "Map data settings" in response.text
    assert "Atwood" in response.text


def test_inspect_csv_source_returns_fields_and_preview(client: TestClient) -> None:
    response = client.get(
        "/source/inspect/",
        params={
            "source_type": "csv",
            "csv_path": "datasets/points.csv",
            "header_row": 1,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["row_count"] == 2
    assert "Row ID" in payload["fields"]
    assert "Display Hex Colour" in payload["fields"]
    assert payload["preview_rows"][0]["point_code"] == "A1"


def test_inspect_sqlite_source_lists_tables_before_selection(client: TestClient) -> None:
    response = client.get(
        "/source/inspect/",
        params={"source_type": "sqlite", "sqlite_path": "points.sqlite3"},
    )

    assert response.status_code == 200
    assert response.json()["sqlite_tables"] == ["places"]
    assert response.json()["row_count"] == 0


def test_render_csv_source_returns_geojson(client: TestClient) -> None:
    response = client.get(
        "/source/data/",
        params={
            "source_type": "csv",
            "csv_path": "datasets/points.csv",
            "header_row": 1,
            "point_id_field": "point_code",
            "x_coord_field": "x_coord",
            "y_coord_field": "y_coord",
            "description_field": "details",
            "point_color": "#123abc",
        },
    )

    assert response.status_code == 200
    features = response.json()["geojson"]["features"]
    assert len(features) == 2
    assert features[0]["properties"] == {
        "point_id": "A1",
        "description": "Alpha",
        "display_hex_colour": "#123ABC",
    }


def test_local_file_paths_must_stay_inside_project(client: TestClient) -> None:
    response = client.get(
        "/source/inspect/",
        params={
            "source_type": "csv",
            "csv_path": "../outside.csv",
            "header_row": 1,
        },
    )

    assert response.status_code == 400
    assert "inside the project directory" in response.json()["error"]


def test_google_sheet_csv_url_conversion() -> None:
    assert _google_sheet_csv_url(
        "https://docs.google.com/spreadsheets/d/1ABC123xyz/edit#gid=987654"
    ) == "https://docs.google.com/spreadsheets/d/1ABC123xyz/gviz/tq?tqx=out%3Acsv&gid=987654"
