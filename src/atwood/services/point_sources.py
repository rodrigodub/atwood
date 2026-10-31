from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import pandas as pd


DEFAULT_GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1Rfi0fp23VAyOvlJJ9qQzTmdXk-zz1AADKKEIrWSyyOM/edit?usp=sharing"
DEFAULT_SOURCE_CONFIG = {
    "source_type": "google_sheet",
    "sheet_url": DEFAULT_GOOGLE_SHEET_URL,
    "csv_path": "datasets/whc-sites-2023-rn.csv",
    "sqlite_path": "db.sqlite3",
    "sqlite_table": "",
    "header_row": 3,
}
DEFAULT_FIELD_MAPPING = {
    "point_id_field": "ID",
    "x_coord_field": "Longitude",
    "y_coord_field": "Latitude",
    "description_field": "Aircraft",
    "point_color": "#3388FF",
}
DEFAULT_POINT_COLOR = "#3388FF"
HEX_COLOR_RE = re.compile(r"^#(?:[0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")
SQLITE_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


class SourceConfigurationError(ValueError):
    def __init__(self, user_message: str):
        super().__init__(user_message)
        self.user_message = user_message


def get_available_source_options() -> dict:
    return {
        "csv_files": _list_project_files(("*.csv",)),
        "sqlite_files": _list_project_files(("*.sqlite", "*.sqlite3", "*.db")),
    }


def inspect_source(source_config: dict) -> dict:
    dataframe, tables = _load_source_dataframe(source_config, include_tables=True)
    if dataframe.empty and not list(dataframe.columns):
        return {
            "fields": [],
            "preview_rows": [],
            "row_count": 0,
            "sqlite_tables": tables,
        }
    dataframe = _prepare_dataframe(dataframe, source_config["source_type"])
    return {
        "fields": dataframe.columns.tolist(),
        "preview_rows": _dataframe_preview(dataframe),
        "row_count": int(len(dataframe.index)),
        "sqlite_tables": tables,
    }


def build_geojson(source_config: dict, field_mapping: dict) -> dict:
    dataframe, _ = _load_source_dataframe(source_config, include_tables=False)
    dataframe = _prepare_dataframe(dataframe, source_config["source_type"])
    _validate_mapping(dataframe, field_mapping)

    point_color = _normalize_hex_color(field_mapping.get("point_color"))
    if point_color is None:
        raise SourceConfigurationError("Choose a valid point colour.")

    mapped = dataframe[
        [
            field_mapping["point_id_field"],
            field_mapping["x_coord_field"],
            field_mapping["y_coord_field"],
            field_mapping["description_field"],
        ]
    ].copy()
    mapped.columns = ["point_id", "x_coord", "y_coord", "description"]

    mapped["x_coord"] = pd.to_numeric(mapped["x_coord"], errors="coerce")
    mapped["y_coord"] = pd.to_numeric(mapped["y_coord"], errors="coerce")

    invalid_coordinate_rows = mapped[mapped["x_coord"].isna() | mapped["y_coord"].isna()]
    if not invalid_coordinate_rows.empty:
        raise SourceConfigurationError(
            f"Found {len(invalid_coordinate_rows.index)} row(s) with invalid X/Y coordinate values."
        )

    mapped["display_hex_colour"] = point_color
    mapped["point_id"] = mapped["point_id"].where(~mapped["point_id"].isna(), "").astype(str)
    mapped["description"] = mapped["description"].where(~mapped["description"].isna(), "").astype(str)

    features = []
    for row in mapped.itertuples(index=False):
        features.append(
            {
                "type": "Feature",
                "geometry": {"type": "Point", "coordinates": [row.x_coord, row.y_coord]},
                "properties": {
                    "point_id": row.point_id,
                    "description": row.description,
                    "display_hex_colour": row.display_hex_colour,
                },
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def parse_source_config(query_dict) -> dict:
    source_type = query_dict.get("source_type", DEFAULT_SOURCE_CONFIG["source_type"])
    if source_type not in {"google_sheet", "csv", "sqlite"}:
        raise SourceConfigurationError("Choose a valid source type.")

    header_row = query_dict.get("header_row", DEFAULT_SOURCE_CONFIG["header_row"])
    try:
        header_row = int(header_row)
    except (TypeError, ValueError) as exc:
        raise SourceConfigurationError("Header row must be a positive number.") from exc

    if header_row < 1:
        raise SourceConfigurationError("Header row must be a positive number.")

    return {
        "source_type": source_type,
        "sheet_url": query_dict.get("sheet_url", DEFAULT_SOURCE_CONFIG["sheet_url"]).strip(),
        "csv_path": query_dict.get("csv_path", DEFAULT_SOURCE_CONFIG["csv_path"]).strip(),
        "sqlite_path": query_dict.get("sqlite_path", DEFAULT_SOURCE_CONFIG["sqlite_path"]).strip(),
        "sqlite_table": query_dict.get("sqlite_table", "").strip(),
        "header_row": header_row,
    }


def parse_field_mapping(query_dict) -> dict:
    return {
        "point_id_field": query_dict.get("point_id_field", "").strip(),
        "x_coord_field": query_dict.get("x_coord_field", "").strip(),
        "y_coord_field": query_dict.get("y_coord_field", "").strip(),
        "description_field": query_dict.get("description_field", "").strip(),
        "point_color": query_dict.get("point_color", DEFAULT_FIELD_MAPPING["point_color"]).strip(),
    }


def _load_source_dataframe(source_config: dict, include_tables: bool) -> tuple[pd.DataFrame, list[str]]:
    source_type = source_config["source_type"]
    if source_type == "google_sheet":
        return _load_google_sheet_dataframe(source_config), []
    if source_type == "csv":
        return _load_csv_dataframe(source_config), []
    return _load_sqlite_dataframe(source_config, include_tables)


def _load_google_sheet_dataframe(source_config: dict) -> pd.DataFrame:
    sheet_url = source_config["sheet_url"]
    if not sheet_url:
        raise SourceConfigurationError("Provide a Google Sheet URL.")
    csv_export_url = _google_sheet_csv_url(sheet_url)
    try:
        return pd.read_csv(csv_export_url, header=source_config["header_row"] - 1)
    except HTTPError as exc:
        if exc.code in {401, 403}:
            raise SourceConfigurationError(
                "Could not access Google Sheet. Please check that sharing is set to 'Anyone with the link can view'."
            ) from exc
        if exc.code == 404:
            raise SourceConfigurationError("Google Sheet not found. Please check the URL.") from exc
        raise SourceConfigurationError(
            f"Could not download Google Sheet data (HTTP {exc.code})."
        ) from exc
    except URLError as exc:
        raise SourceConfigurationError(
            "Could not connect to Google Sheets. Please check the URL and your network connection."
        ) from exc
    except SourceConfigurationError:
        raise
    except Exception as exc:
        raise SourceConfigurationError(
            f"Could not parse Google Sheet data: {exc}"
        ) from exc


def _load_csv_dataframe(source_config: dict) -> pd.DataFrame:
    csv_path = _resolve_project_file(source_config["csv_path"], "CSV file", ("*.csv",))
    return pd.read_csv(csv_path, header=source_config["header_row"] - 1)


def _load_sqlite_dataframe(source_config: dict, include_tables: bool) -> tuple[pd.DataFrame, list[str]]:
    sqlite_path = _resolve_project_file(
        source_config["sqlite_path"],
        "SQLite database",
        ("*.sqlite", "*.sqlite3", "*.db"),
    )
    with sqlite3.connect(sqlite_path) as connection:
        tables = [
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            ).fetchall()
        ]
        table_dataframes = _load_sqlite_table_dataframes(connection, tables)
        if not include_tables and not source_config["sqlite_table"]:
            raise SourceConfigurationError("Choose a SQLite table.")
        if include_tables and not source_config["sqlite_table"]:
            return pd.DataFrame(), tables
        if source_config["sqlite_table"] not in table_dataframes:
            raise SourceConfigurationError("Choose a valid SQLite table.")
        dataframe = table_dataframes[source_config["sqlite_table"]]
    return dataframe, tables


def _prepare_dataframe(dataframe: pd.DataFrame, source_type: str) -> pd.DataFrame:
    prepared = dataframe.copy()
    if prepared.empty:
        prepared = prepared.copy()
    prepared.columns = [str(column) for column in prepared.columns]
    prepared.insert(0, "Row ID", range(1, len(prepared.index) + 1))
    if "Display Hex Colour" not in prepared.columns:
        prepared["Display Hex Colour"] = _default_colors(prepared, source_type)
    return prepared


def _default_colors(dataframe: pd.DataFrame, source_type: str) -> pd.Series:
    if "Status" in dataframe.columns:
        return dataframe["Status"].map(
            {
                "Travelled": "#6682FF",
                "Planned": "#E7180B",
                "UNESCO": "#66FF85",
            }
        ).fillna(DEFAULT_POINT_COLOR)
    if source_type == "csv":
        return pd.Series(["#66FF85"] * len(dataframe.index), index=dataframe.index)
    return pd.Series([DEFAULT_POINT_COLOR] * len(dataframe.index), index=dataframe.index)


def _validate_mapping(dataframe: pd.DataFrame, field_mapping: dict) -> None:
    field_values = {key: value for key, value in field_mapping.items() if key != "point_color"}
    missing = [key for key, value in field_values.items() if not value]
    if missing:
        raise SourceConfigurationError("Choose all required field mappings before rendering the map.")

    fields = set(dataframe.columns)
    invalid = [value for value in field_values.values() if value not in fields]
    if invalid:
        raise SourceConfigurationError("One or more selected fields are no longer available in the source.")


def _normalize_hex_color(value) -> str | None:
    if pd.isna(value):
        return None
    text = str(value).strip()
    if not HEX_COLOR_RE.match(text):
        return None
    return text.upper()


def _resolve_project_file(path_value: str, label: str, patterns: tuple[str, ...]) -> Path:
    if not path_value:
        raise SourceConfigurationError(f"Provide a {label.lower()} path.")

    candidate = Path(path_value).as_posix()
    if candidate.startswith("/") or ".." in Path(candidate).parts:
        raise SourceConfigurationError(f"{label} path must stay inside the project directory.")
    available_files = set(_list_project_files(patterns))
    if candidate not in available_files:
        raise SourceConfigurationError(f"{label} was not found.")
    return _project_root() / candidate


def _google_sheet_csv_url(sheet_url: str) -> str:
    parsed = urlparse(sheet_url)
    if parsed.netloc in {"docs.google.com", "www.docs.google.com"} and "/spreadsheets/d/" in parsed.path:
        match = re.search(r"/spreadsheets/d/([^/]+)", parsed.path)
        if not match:
            raise SourceConfigurationError("Provide a valid Google Sheet URL.")
        query_params = parse_qs(parsed.query)
        fragment_params = parse_qs(parsed.fragment)
        gid = fragment_params.get("gid", query_params.get("gid", ["0"]))[0]
        return urlunparse(
            (
                parsed.scheme or "https",
                parsed.netloc,
                f"/spreadsheets/d/{match.group(1)}/gviz/tq",
                "",
                urlencode({"tqx": "out:csv", "gid": gid}),
                "",
            )
        )
    if parsed.scheme in {"http", "https"}:
        return sheet_url
    raise SourceConfigurationError("Provide a valid Google Sheet URL.")


def _list_project_files(patterns: tuple[str, ...]) -> list[str]:
    project_root = _project_root()
    files = set()
    for pattern in patterns:
        for path in project_root.rglob(pattern):
            relative_path = path.relative_to(project_root)
            if (
                path.is_file()
                and not {".git", ".venv", "__pycache__", "node_modules"}.intersection(relative_path.parts)
            ):
                files.add(relative_path.as_posix())
    return sorted(files)


def _project_root() -> Path:
    return Path(os.environ.get("ATWOOD_DATA_ROOT", Path.cwd())).resolve()


def _dataframe_preview(dataframe: pd.DataFrame, limit: int = 5) -> list[dict]:
    preview = dataframe.head(limit).astype(object)
    # Casting to object dtype first ensures None survives instead of being
    # silently coerced back to NaN by pandas (NaN is not valid JSON and
    # breaks response.json() parsing in the browser, e.g. Safari raises
    # "SyntaxError: The string did not match the expected pattern.").
    preview = preview.where(pd.notna(preview), None)
    return preview.to_dict(orient="records")


def _validate_sqlite_identifier(identifier: str) -> str:
    if not SQLITE_IDENTIFIER_RE.match(identifier):
        raise SourceConfigurationError("Choose a valid SQLite table.")
    return identifier


def _load_sqlite_table_dataframes(connection: sqlite3.Connection, tables: list[str]) -> dict[str, pd.DataFrame]:
    dataframes = {}
    for table_name in tables:
        safe_table_name = _validate_sqlite_identifier(table_name)
        cursor = connection.execute(f'SELECT * FROM "{safe_table_name}"')
        rows = cursor.fetchall()
        columns = [column[0] for column in cursor.description or []]
        dataframes[table_name] = pd.DataFrame(rows, columns=columns)
    return dataframes
