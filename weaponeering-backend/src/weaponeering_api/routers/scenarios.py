from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import User
from weaponeering_api.schemas.scenario import (
    ScenarioCreate,
    ScenarioListItem,
    ScenarioOut,
    ScenarioUpdate,
)
from weaponeering_api.services import scenario_service

router = APIRouter(prefix="/scenarios", tags=["scenarios"])


@router.get("", response_model=list[ScenarioListItem])
async def list_scenarios(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[ScenarioListItem]:
    rows = await scenario_service.list_scenarios(db)
    return [ScenarioListItem.model_validate(row) for row in rows]


@router.post("", response_model=ScenarioOut, status_code=status.HTTP_201_CREATED)
async def create_scenario(
    body: ScenarioCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScenarioOut:
    scenario = await scenario_service.create_scenario(db, body, user)
    return ScenarioOut.model_validate(scenario)


@router.get("/{scenario_id}", response_model=ScenarioOut)
async def get_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> ScenarioOut:
    scenario = await scenario_service.get_scenario(db, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="ไม่พบ scenario")
    return ScenarioOut.model_validate(scenario)


@router.patch("/{scenario_id}", response_model=ScenarioOut)
async def update_scenario(
    scenario_id: UUID,
    body: ScenarioUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ScenarioOut:
    scenario = await scenario_service.get_scenario(db, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="ไม่พบ scenario")
    updated = await scenario_service.update_scenario(db, scenario, body, user)
    return ScenarioOut.model_validate(updated)


@router.delete("/{scenario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scenario(
    scenario_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    scenario = await scenario_service.get_scenario(db, scenario_id)
    if scenario is None:
        raise HTTPException(status_code=404, detail="ไม่พบ scenario")
    await scenario_service.delete_scenario(db, scenario, user)
