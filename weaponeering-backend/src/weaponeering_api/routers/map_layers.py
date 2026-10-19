from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import User
from weaponeering_api.services import map_service

router = APIRouter(tags=["map"])


@router.get("/map/layers")
async def get_map_layers(
    scenario_id: UUID = Query(...),
    transport_id: UUID | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> dict:
    """Scenario-scoped map layers (desktop-compatible payloads)."""
    return await map_service.build_map_layers(
        db,
        scenario_id,
        selected_transport_id=transport_id,
    )
