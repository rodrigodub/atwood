import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from atwood.services.point_sources import (
    DEFAULT_FIELD_MAPPING,
    DEFAULT_SOURCE_CONFIG,
    SourceConfigurationError,
    build_geojson,
    get_available_source_options,
    inspect_source,
    parse_field_mapping,
    parse_source_config,
)

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).parent
templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates")


def create_app() -> FastAPI:
    # -------------------------- VERSION --------------------------
    app = FastAPI(title="Atwood", 
                  version="0.2.3")
    # -------------------------------------------------------------
    app.mount("/static", StaticFiles(directory=PACKAGE_ROOT / "static"), name="static")

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    def home(request: Request) -> HTMLResponse:
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "app_version": app.version,
                "default_source_config": DEFAULT_SOURCE_CONFIG,
                "default_field_mapping": DEFAULT_FIELD_MAPPING,
                "available_source_options": get_available_source_options(),
            },
        )

    @app.get("/source/inspect/")
    def inspect_point_source(request: Request) -> JSONResponse:
        try:
            source_config = parse_source_config(request.query_params)
            payload = inspect_source(source_config)
        except SourceConfigurationError as exc:
            return JSONResponse({"error": exc.user_message}, status_code=400)
        except Exception:
            logger.exception("Could not inspect the selected point source.")
            return JSONResponse({"error": "Could not inspect the selected source."}, status_code=400)
        return JSONResponse(payload)

    @app.get("/source/data/")
    def point_source_data(request: Request) -> JSONResponse:
        try:
            source_config = parse_source_config(request.query_params)
            field_mapping = parse_field_mapping(request.query_params)
            payload = {"geojson": build_geojson(source_config, field_mapping)}
        except SourceConfigurationError as exc:
            return JSONResponse({"error": exc.user_message}, status_code=400)
        except Exception:
            logger.exception("Could not build point source geojson.")
            return JSONResponse({"error": "Could not load point data."}, status_code=400)
        return JSONResponse(payload)

    return app


app = create_app()
