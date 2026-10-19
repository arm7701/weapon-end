from __future__ import annotations

import logging
from typing import Any

import httpx

from weaponeering_api.config import Settings

logger = logging.getLogger(__name__)


class RtafMfaError(Exception):
    def __init__(self, message: str, *, status_code: int = 502, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


def _is_auth_rejected(payload: Any) -> bool:
    if not isinstance(payload, dict):
        return True

    result = str(payload.get("result") or payload.get("status") or "").strip().lower()
    if payload.get("success") is False or payload.get("ok") is False:
        return True
    if payload.get("authorized") is False:
        return True
    if result in {"process-error", "error", "failed", "denied", "rejected"}:
        return True
    if not payload.get("token"):
        return True
    return False


async def login_with_otp(settings: Settings, user: str, otp: str) -> dict[str, Any]:
    """เรียก RTAF MFA login แล้วคืน JSON ของ upstream เมื่อสำเร็จ"""
    # [DEV-TEMP-START] ลบส่วนนี้ออกเมื่อส่งมอบงาน
    if otp in {"123456", "000000"}:
        import uuid as _uuid

        return {
            "result": "Process-Complete",
            "user": user,
            "user_name": f"น.อ. {user} (Dev Mode)",
            "rank": "น.อ.",
            "rankID": "10",
            "fname": user,
            "lname": "RTAF",
            "user_position": "นายทหารวางแผนยุทธการ",
            "user_orgname": "ศูนย์ซอฟต์แวร์กองทัพอากาศ",
            "user_orgname_code": "SWC",
            "user_role": "admin",
            "token": f"dev-token-{_uuid.uuid4().hex}",
            "challenge": "dev-otp-bypass",
            "login_mode": "dev-bypass",
        }
    # [DEV-TEMP-END]
    payload = {"user": user, "pass": otp}

    try:
        async with httpx.AsyncClient(
            timeout=settings.rtaf_mfa_timeout_seconds,
            verify=settings.rtaf_mfa_verify_ssl,
        ) as client:
            response = await client.post(
                settings.rtaf_mfa_url,
                json=payload,
                headers={
                    "Accept": "application/json",
                    "Content-Type": "application/json",
                },
            )
    except httpx.TimeoutException as exc:
        logger.exception("RTAF MFA timeout: %s", settings.rtaf_mfa_url)
        raise RtafMfaError(
            "บริการ RTAF ใช้เวลาตอบกลับนานเกินไป กรุณาลองใหม่",
            status_code=502,
            details=str(exc),
        ) from exc
    except httpx.HTTPError as exc:
        logger.exception("RTAF MFA connection failed: %s", settings.rtaf_mfa_url)
        raise RtafMfaError(
            "ไม่สามารถเชื่อมต่อบริการยืนยันตัวตน RTAF ได้ "
            f"({type(exc).__name__}: {exc})",
            status_code=502,
            details=str(exc),
        ) from exc

    try:
        data = response.json()
    except ValueError:
        data = {"raw": response.text[:500]}

    if response.is_success and not _is_auth_rejected(data):
        return data if isinstance(data, dict) else {"result": "ok", "data": data}

    if response.status_code in {401, 403} or _is_auth_rejected(data):
        message = "อีเมลหรือ OTP ไม่ถูกต้อง"
        if isinstance(data, dict):
            message = str(data.get("message") or data.get("detail") or data.get("error") or message)
        raise RtafMfaError(message, status_code=401, details=data)

    logger.error("RTAF MFA unexpected response status=%s body=%s", response.status_code, data)
    raise RtafMfaError(
        "บริการยืนยันตัวตน RTAF ตอบกลับผิดพลาด",
        status_code=502,
        details=data,
    )
