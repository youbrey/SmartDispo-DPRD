from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, SessionDep, permissions_for_user
from app.core.security import create_token, decode_token, token_digest, verify_password
from app.models.entities import RefreshToken, Role, RoleAssignment, User, UserRole
from app.schemas.common import RefreshRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(session: SessionDep, form: OAuth2PasswordRequestForm = Depends()) -> TokenPair:
    user = (await session.execute(select(User).where(User.username == form.username))).scalar_one_or_none()
    if not user or not user.active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Nama pengguna atau kata sandi salah")
    settings = get_settings()
    access = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes), user.token_version)
    refresh = create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_days), user.token_version)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_digest(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    await session.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
async def refresh_tokens(payload: RefreshRequest, session: SessionDep) -> TokenPair:
    try:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh":
            raise ValueError("wrong token type")
        user_id = claims["sub"]
    except Exception as exc:
        raise HTTPException(status_code=401, detail="Refresh token tidak valid") from exc
    stored = (
        await session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_digest(payload.refresh_token),
                RefreshToken.revoked_at.is_(None),
                RefreshToken.expires_at > datetime.now(UTC),
            )
        )
    ).scalar_one_or_none()
    user = await session.get(User, UUID(user_id))
    if not stored or not user or not user.active or claims.get("ver") != user.token_version:
        raise HTTPException(status_code=401, detail="Refresh token tidak valid")
    stored.revoked_at = datetime.now(UTC)
    settings = get_settings()
    access = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes), user.token_version)
    refresh = create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_days), user.token_version)
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_digest(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    await session.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/logout", status_code=204)
async def logout(payload: RefreshRequest, session: SessionDep) -> None:
    stored = (
        await session.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_digest(payload.refresh_token),
                RefreshToken.revoked_at.is_(None),
            )
        )
    ).scalar_one_or_none()
    if stored:
        stored.revoked_at = datetime.now(UTC)
        await session.commit()


@router.get("/me")
async def me(user: CurrentUser, session: SessionDep) -> dict:
    permissions = sorted(await permissions_for_user(session, user.id))
    role_codes = sorted(
        (
            await session.execute(
                select(Role.code).join(UserRole, UserRole.role_id == Role.id).where(UserRole.user_id == user.id)
            )
        ).scalars()
    )
    today = datetime.now(UTC).date()
    active_role_codes = sorted(
        (
            await session.execute(
                select(Role.code)
                .join(RoleAssignment, RoleAssignment.role_id == Role.id)
                .where(
                    RoleAssignment.user_id == user.id,
                    RoleAssignment.active.is_(True),
                    RoleAssignment.valid_from <= today,
                    (RoleAssignment.valid_until.is_(None) | (RoleAssignment.valid_until >= today)),
                )
            )
        ).scalars()
    )
    return {
        "id": str(user.id),
        "username": user.username,
        "full_name": user.full_name,
        "permissions": permissions,
        "role_codes": role_codes,
        "active_role_codes": active_role_codes,
    }
