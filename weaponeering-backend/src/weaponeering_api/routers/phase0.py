from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.db import get_db
from weaponeering_api.deps.auth import get_current_user
from weaponeering_api.models import AuditEvent, User
from weaponeering_api.schemas.common import AuditEventOut, UserMeOut

router = APIRouter(tags=["phase-0"])


@router.get("/me", response_model=UserMeOut)
async def me(user: User = Depends(get_current_user)) -> UserMeOut:
    return UserMeOut.model_validate(user)


@router.get("/audit-events", response_model=list[AuditEventOut])
async def list_audit_events(
    limit: int = Query(default=50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list[AuditEventOut]:
    result = await db.execute(
        select(AuditEvent).order_by(AuditEvent.created_at.desc()).limit(limit)
    )
    return [AuditEventOut.model_validate(row) for row in result.scalars().all()]
