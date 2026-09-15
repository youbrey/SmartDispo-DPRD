from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select

from app.core.config import get_settings
from app.core.dependencies import CurrentUser, SessionDep
from app.core.security import create_token, decode_token, token_digest, verify_password
from app.models.entities import RefreshToken, User
from app.schemas.common import RefreshRequest, TokenPair

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenPair)
async def login(session: SessionDep, form: OAuth2PasswordRequestForm = Depends()) -> TokenPair:
    user = (await session.execute(select(User).where(User.username == form.username))).scalar_one_or_none()
    if not user or not user.active or not verify_password(form.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Nama pengguna atau kata sandi salah")
    settings = get_settings()
    access = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes))
    refresh = create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_days))
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
    if not stored or not user or not user.active:
        raise HTTPException(status_code=401, detail="Refresh token tidak valid")
    stored.revoked_at = datetime.now(UTC)
    settings = get_settings()
    access = create_token(str(user.id), "access", timedelta(minutes=settings.access_token_minutes))
    refresh = create_token(str(user.id), "refresh", timedelta(days=settings.refresh_token_days))
    session.add(
        RefreshToken(
            user_id=user.id,
            token_hash=token_digest(refresh),
            expires_at=datetime.now(UTC) + timedelta(days=settings.refresh_token_days),
        )
    )
    await session.commit()
    return TokenPair(access_token=access, refresh_token=refresh)


@router.get("/me")
async def me(user: CurrentUser) -> dict:
    return {"id": str(user.id), "username": user.username, "full_name": user.full_name}
