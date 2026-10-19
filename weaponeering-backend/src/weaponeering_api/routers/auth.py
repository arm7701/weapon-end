from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.config import Settings, get_settings
from weaponeering_api.db import get_db
from weaponeering_api.schemas.auth import MfaLoginRequest, MfaLoginResponse
from weaponeering_api.services.auth_persist import (
    create_auth_session,
    upsert_user_from_mfa,
    write_audit,
)
from weaponeering_api.services.rtaf_mfa import RtafMfaError, login_with_otp

router = APIRouter(tags=["auth"])


@router.post("/mfa/login", response_model=MfaLoginResponse)
async def mfa_login(
    body: MfaLoginRequest,
    settings: Settings = Depends(get_settings),
    db: AsyncSession = Depends(get_db),
) -> MfaLoginResponse:
    """
    เข้าสู่ระบบด้วย Email ทอ. + OTP จาก RTAF Super App

    สำเร็จแล้วจะ upsert ผู้ใช้ + สร้าง auth_session ใน PostgreSQL (ผ่าน pgpool)
    """
    try:
        data = await login_with_otp(settings, body.user, body.pass_)
    except RtafMfaError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc

    try:
        response = MfaLoginResponse.model_validate(data)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="รูปแบบข้อมูลจากบริการ RTAF ไม่ครบถ้วน",
        ) from exc

    user = await upsert_user_from_mfa(db, data)
    await create_auth_session(
        db,
        user,
        access_token=response.token,
        challenge=response.challenge,
        login_mode=response.login_mode,
    )
    await write_audit(
        db,
        actor=user.username,
        event_type="auth.login",
        entity_type="user",
        entity_id=str(user.id),
        details={"login_mode": response.login_mode},
    )
    await db.commit()
    return response
