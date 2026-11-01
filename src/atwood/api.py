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
from atwood.services.profile_persistence import (
    DuplicateProfileNameError,
    ProfileNotFoundError,
    ProfileStore,
    ProfileStoreError,
)

logger = logging.getLogger(__name__)

PACKAGE_ROOT = Path(__file__).parent
templates = Jinja2Templates(directory=PACKAGE_ROOT / "templates")


def create_app() -> FastAPI:
    # -------------------------- VERSION --------------------------
    app = FastAPI(title="Atwood", 
                  version="0.2.7")
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

    @app.get("/profiles/")
    def list_profiles() -> JSONResponse:
        try:
            return JSONResponse({"profiles": ProfileStore().list_profiles()})
        except ProfileStoreError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/profiles/")
    async def create_profile(request: Request) -> JSONResponse:
        try:
            payload = await request.json()
            if not isinstance(payload, dict):
                raise SourceConfigurationError("Provide profile details.")
            profile = ProfileStore().create(
                payload.get("profile_name"),
                parse_source_config(payload.get("source_config", {})),
                parse_field_mapping(payload.get("field_mapping", {})),
            )
            return JSONResponse(profile, status_code=201)
        except DuplicateProfileNameError as exc:
            return JSONResponse({"error": str(exc)}, status_code=409)
        except SourceConfigurationError as exc:
            return JSONResponse({"error": exc.user_message}, status_code=400)
        except ProfileStoreError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        except Exception:
            logger.exception("Could not save profile.")
            return JSONResponse({"error": "Could not save profile."}, status_code=400)

    @app.get("/profiles/{profile_id}")
    def get_profile(profile_id: str) -> JSONResponse:
        try:
            return JSONResponse(ProfileStore().get_profile(profile_id))
        except ProfileNotFoundError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except ProfileStoreError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.post("/profiles/{profile_id}/refresh")
    def refresh_profile(profile_id: str) -> JSONResponse:
        try:
            return JSONResponse(ProfileStore().refresh(profile_id))
        except ProfileNotFoundError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except SourceConfigurationError as exc:
            return JSONResponse({"error": exc.user_message}, status_code=400)
        except ProfileStoreError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        except Exception:
            logger.exception("Could not refresh profile.")
            return JSONResponse({"error": "Could not refresh profile."}, status_code=400)

    @app.delete("/profiles/{profile_id}")
    def delete_profile(profile_id: str) -> JSONResponse:
        try:
            ProfileStore().delete(profile_id)
            return JSONResponse(status_code=204, content=None)
        except ProfileNotFoundError as exc:
            return JSONResponse({"error": str(exc)}, status_code=404)
        except ProfileStoreError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    return app


app = create_app()
