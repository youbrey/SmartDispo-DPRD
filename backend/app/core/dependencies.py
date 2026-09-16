from typing import Annotated
from uuid import UUID

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import decode_token
from app.db.session import get_session
from app.models.entities import Permission, RolePermission, User, UserDevice, UserRole

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")
SessionDep = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(session: SessionDep, token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kredensial tidak valid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_error
        user_id = UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError) as exc:
        raise credentials_error from exc
    user = await session.get(User, user_id)
    if not user or not user.active or payload.get("ver") != user.token_version:
        raise credentials_error
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


async def permissions_for_user(session: AsyncSession, user_id: UUID) -> set[str]:
    query = (
        select(Permission.code)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .join(UserRole, UserRole.role_id == RolePermission.role_id)
        .where(UserRole.user_id == user_id)
    )
    return set((await session.execute(query)).scalars())


async def has_permission(session: AsyncSession, user_id: UUID, permission_code: str) -> bool:
    return permission_code in await permissions_for_user(session, user_id)


def require_permission(permission_code: str):
    async def checker(session: SessionDep, user: CurrentUser) -> User:
        if not await has_permission(session, user.id, permission_code):
            raise HTTPException(status_code=403, detail="Izin tidak mencukupi")
        return user

    return checker


async def ensure_active_device(
    session: AsyncSession,
    user_id: UUID,
    device_fingerprint: str | None,
) -> UserDevice:
    if not device_fingerprint:
        raise HTTPException(status_code=403, detail="Perangkat aktif wajib digunakan untuk tindakan ini")
    device = (
        await session.execute(
            select(UserDevice).where(
                UserDevice.user_id == user_id,
                UserDevice.device_fingerprint == device_fingerprint,
                UserDevice.revoked_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if not device:
        raise HTTPException(status_code=403, detail="Perangkat belum terdaftar atau telah dicabut")
    return device
