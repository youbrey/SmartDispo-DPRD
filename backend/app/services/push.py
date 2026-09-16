import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
from google.auth.transport.requests import Request as GoogleAuthRequest
from google.oauth2 import service_account
from sqlalchemy import select

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.models.entities import Notification, UserDevice

FCM_SCOPE = "https://www.googleapis.com/auth/firebase.messaging"


def push_configured() -> bool:
    settings = get_settings()
    return bool(
        settings.firebase_project_id
        and settings.firebase_service_account_file
        and Path(settings.firebase_service_account_file).is_file()
    )


def _access_token() -> str:
    settings = get_settings()
    credentials = service_account.Credentials.from_service_account_file(
        settings.firebase_service_account_file,
        scopes=[FCM_SCOPE],
    )
    credentials.refresh(GoogleAuthRequest())
    if not credentials.token:
        raise RuntimeError("Firebase access token tidak tersedia")
    return credentials.token


async def _deliver(notification: Notification, tokens: list[str]) -> bool:
    if not tokens:
        return True
    settings = get_settings()
    token = await asyncio.to_thread(_access_token)
    endpoint = f"https://fcm.googleapis.com/v1/projects/{settings.firebase_project_id}/messages:send"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(timeout=15) as client:
        results = await asyncio.gather(
            *[
                client.post(
                    endpoint,
                    headers=headers,
                    json={
                        "message": {
                            "token": device_token,
                            "notification": {"title": notification.title, "body": notification.body},
                            "data": {
                                "event_type": notification.event_type,
                                **{
                                    key: value if isinstance(value, str) else json.dumps(value)
                                    for key, value in notification.payload.items()
                                },
                            },
                            "android": {"priority": "high"},
                        }
                    },
                )
                for device_token in tokens
            ],
            return_exceptions=True,
        )
    return all(not isinstance(result, Exception) and result.is_success for result in results)


async def process_push_outbox() -> int:
    async with SessionLocal() as session:
        rows = list(
            (
                await session.execute(
                    select(Notification)
                    .where(Notification.push_sent_at.is_(None))
                    .order_by(Notification.created_at)
                    .limit(50)
                    .with_for_update(skip_locked=True)
                )
            ).scalars()
        )
        delivered = 0
        for notification in rows:
            tokens = list(
                (
                    await session.execute(
                        select(UserDevice.fcm_token).where(
                            UserDevice.user_id == notification.user_id,
                            UserDevice.revoked_at.is_(None),
                            UserDevice.fcm_token.is_not(None),
                        )
                    )
                ).scalars()
            )
            if await _deliver(notification, tokens):
                notification.push_sent_at = datetime.now(UTC)
                delivered += 1
        await session.commit()
        return delivered


async def push_worker(stop: asyncio.Event) -> None:
    settings = get_settings()
    while not stop.is_set():
        try:
            await process_push_outbox()
        except Exception:
            # The outbox is intentionally retried; API transactions must remain independent from FCM availability.
            pass
        try:
            await asyncio.wait_for(stop.wait(), timeout=settings.push_poll_seconds)
        except TimeoutError:
            continue
