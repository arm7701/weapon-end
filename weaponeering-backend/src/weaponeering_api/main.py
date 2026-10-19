from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from weaponeering_api import __version__
from weaponeering_api.config import get_settings
from weaponeering_api.db import check_database
from weaponeering_api.routers import auth as auth_router
from weaponeering_api.routers import detection as detection_router
from weaponeering_api.routers import logistics as logistics_router
from weaponeering_api.routers import map_layers as map_layers_router
from weaponeering_api.routers import phase0 as phase0_router
from weaponeering_api.routers import scenarios as scenarios_router
from weaponeering_api.routers import targets as targets_router
from weaponeering_api.routers import weaponeering as weaponeering_router
from weaponeering_api.routers import wing as wing_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description=(
            "Backend สำหรับ Weaponeering website\n\n"
            "Phase 0: foundation (users/sessions/scenarios/audit)\n"
            "Phase 2: targets (cards/coordinates/recognition/review)\n"
            "Phase 3: assets / logistics (orgs/platforms/depots/routes)\n"
            "Phase 4: wing database (wings/units/aircraft/pilots/depots)\n"
            "Phase 5: weaponeering / ranking / deployment / plan options\n"
            "Phase 6: detection / map extras (team markers, ground transport)\n"
            "Map layers: /api/map/layers (desktop-compatible)\n"
            "โค้ด desktop ต้นฉบับอยู่ใน `maap_app` และถูกเก็บไว้ครบเพื่ออ้างอิง"
        ),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health() -> dict:
        db = await check_database()
        status = "ok" if db.get("status") == "ok" else "degraded"
        return {
            "status": status,
            "version": __version__,
            "phase": "6-detection",
            "database": db,
        }

    prefix = settings.api_prefix
    app.include_router(auth_router.router, prefix=prefix)
    app.include_router(phase0_router.router, prefix=prefix)
    app.include_router(scenarios_router.router, prefix=prefix)
    app.include_router(targets_router.router, prefix=prefix)
    app.include_router(logistics_router.router, prefix=prefix)
    app.include_router(wing_router.router, prefix=prefix)
    app.include_router(weaponeering_router.router, prefix=prefix)
    app.include_router(detection_router.router, prefix=prefix)
    app.include_router(map_layers_router.router, prefix=prefix)
    return app


app = create_app()


def run() -> None:
    import uvicorn

    uvicorn.run(
        "weaponeering_api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )


if __name__ == "__main__":
    run()
