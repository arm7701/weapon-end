from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import User
from weaponeering_api.schemas.target import (
    HumanReviewCreate,
    HumanReviewOut,
    TargetCardCreate,
    TargetCardListItem,
    TargetCardOut,
    TargetCardUpdate,
    TargetRecognitionIn,
    TargetRecognitionOut,
)
from weaponeering_api.services import target_service

router = APIRouter(tags=["targets"])


@router.get("/targets", response_model=list[TargetCardListItem])
async def list_targets(
    scenario_id: UUID | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    review_status: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[TargetCardListItem]:
    rows = await target_service.list_targets(
        db,
        scenario_id=scenario_id,
        status=status_filter,
        review_status=review_status,
    )
    return [TargetCardListItem.model_validate(row) for row in rows]


@router.post("/targets", response_model=TargetCardOut, status_code=status.HTTP_201_CREATED)
async def create_target(
    body: TargetCardCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TargetCardOut:
    try:
        card = await target_service.create_target(db, body, user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return TargetCardOut.model_validate(card)


@router.get("/targets/{target_id}", response_model=TargetCardOut)
async def get_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> TargetCardOut:
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise HTTPException(status_code=404, detail="ไม่พบเป้าหมาย")
    return TargetCardOut.model_validate(card)


@router.patch("/targets/{target_id}", response_model=TargetCardOut)
async def update_target(
    target_id: UUID,
    body: TargetCardUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TargetCardOut:
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise HTTPException(status_code=404, detail="ไม่พบเป้าหมาย")
    updated = await target_service.update_target(db, card, body, user)
    return TargetCardOut.model_validate(updated)


@router.delete("/targets/{target_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_target(
    target_id: UUID,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> None:
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise HTTPException(status_code=404, detail="ไม่พบเป้าหมาย")
    await target_service.delete_target(db, card, user)


@router.post(
    "/targets/{target_id}/recognitions",
    response_model=TargetRecognitionOut,
    status_code=status.HTTP_201_CREATED,
)
async def add_recognition(
    target_id: UUID,
    body: TargetRecognitionIn,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> TargetRecognitionOut:
    card = await target_service.get_target(db, target_id)
    if card is None:
        raise HTTPException(status_code=404, detail="ไม่พบเป้าหมาย")
    row = await target_service.add_recognition(db, card, body, user)
    return TargetRecognitionOut.model_validate(row)


@router.post(
    "/reviews",
    response_model=HumanReviewOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_review(
    body: HumanReviewCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HumanReviewOut:
    try:
        record = await target_service.create_review(db, body, user)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return HumanReviewOut.model_validate(record)
