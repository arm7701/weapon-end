from typing import Any
import re

from pydantic import BaseModel, Field, field_validator


class MfaLoginRequest(BaseModel):
    """Body ที่ frontend ส่งมา: user (ไม่ใส่ @rtaf.mi.th) + OTP 6 หลัก"""

    user: str = Field(..., min_length=1, max_length=80)
    pass_: str = Field(..., alias="pass", min_length=6, max_length=6)

    model_config = {
        "populate_by_name": True,
    }

    @field_validator("user")
    @classmethod
    def normalize_user(cls, value: str) -> str:
        user = re.sub(r"@rtaf\.mi\.th$", "", value.strip().lower(), flags=re.IGNORECASE)
        if not user or not re.fullmatch(r"[a-z0-9._-]+", user, flags=re.IGNORECASE):
            raise ValueError("กรุณากรอก Email ทอ. โดยไม่ต้องใส่ @rtaf.mi.th")
        return user

    @field_validator("pass_")
    @classmethod
    def validate_otp(cls, value: str) -> str:
        otp = value.strip()
        if not otp.isdigit() or len(otp) != 6:
            raise ValueError("กรุณากรอก OTP 6 หลักให้ถูกต้อง")
        return otp


class MfaLoginResponse(BaseModel):
    """ส่งต่อข้อมูลหลักจาก RTAF MFA + ฟิลด์ที่เว็บใช้ต่อ"""

    result: str
    user: str
    user_name: str | None = None
    rank: str | None = None
    fname: str | None = None
    lname: str | None = None
    user_position: str | None = None
    user_orgname: str | None = None
    user_orgname_code: str | None = None
    user_role: str | None = None
    token: str
    challenge: str | None = None
    login_mode: str | None = None
    messages: dict[str, Any] | None = None
    user_hris: dict[str, Any] | None = None
