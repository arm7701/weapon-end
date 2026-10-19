from __future__ import annotations

import base64
import json
import uuid
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from weaponeering_api.models import AuditEvent, AuthSession, User


def _parse_jwt_exp(token: str) -> datetime | None:
    try:
        parts = token.split(".")
        if len(parts) < 2:
            return None
        payload_b64 = parts[1] + "=" * (-len(parts[1]) % 4)
        payload = json.loads(base64.urlsafe_b64decode(payload_b64.encode("utf-8")))
        exp = payload.get("exp")
        if not exp:
            return None
        return datetime.fromtimestamp(int(exp), tz=UTC)
    except Exception:  # noqa: BLE001
        return None


async def upsert_user_from_mfa(db: AsyncSession, mfa: dict[str, Any]) -> User:
    username = str(mfa.get("user") or "").strip().lower()
    if not username:
        raise ValueError("missing user in MFA payload")

    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(id=uuid.uuid4(), username=username)
        db.add(user)

    user.user_name = mfa.get("user_name")
    user.rank = mfa.get("rank")
    user.rank_id = str(mfa.get("rankID") or mfa.get("rank_id") or "") or None
    user.fname = mfa.get("fname")
    user.lname = mfa.get("lname")
    user.user_position = mfa.get("user_position")
    user.user_orgname = mfa.get("user_orgname")
    user.user_orgname_code = str(mfa.get("user_orgname_code") or "") or None
    user.user_role = mfa.get("user_role")
    user.profile_json = mfa
    return user


async def create_auth_session(
    db: AsyncSession,
    user: User,
    *,
    access_token: str,
    challenge: str | None,
    login_mode: str | None,
) -> AuthSession:
    # revoke previous active sessions for this token collision safety
    existing = await db.execute(select(AuthSession).where(AuthSession.access_token == access_token))
    for row in existing.scalars().all():
        row.revoked_at = datetime.now(tz=UTC)

    session = AuthSession(
        id=uuid.uuid4(),
        user_id=user.id,
        access_token=access_token,
        challenge=challenge,
        login_mode=login_mode,
        expires_at=_parse_jwt_exp(access_token),
    )
    db.add(session)
    return session


async def get_session_by_token(db: AsyncSession, token: str) -> AuthSession | None:
    result = await db.execute(
        select(AuthSession).where(
            AuthSession.access_token == token,
            AuthSession.revoked_at.is_(None),
        )
    )
    session = result.scalar_one_or_none()
    if session is None:
        return None
    if session.expires_at and session.expires_at < datetime.now(tz=UTC):
        session.revoked_at = datetime.now(tz=UTC)
        await db.commit()
        return None
    return session


async def write_audit(
    db: AsyncSession,
    *,
    actor: str,
    event_type: str,
    entity_type: str,
    entity_id: str,
    details: dict[str, Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        id=uuid.uuid4(),
        actor=actor,
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        details_json=details or {},
    )
    db.add(event)
    return event
