from datetime import UTC, datetime
from uuid import UUID

import jwt
from fastapi import APIRouter, Depends, HTTPException, Query, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.core.security import decode_token
from app.db.session import SessionLocal
from app.models.entities import ChatMember, ChatMessage, ChatRoom, Notification, User, UserDevice
from app.services.audit import record_audit
from app.services.realtime import realtime_hub

router = APIRouter(tags=["communications"])


class DeviceRegistration(BaseModel):
    device_fingerprint: str = Field(min_length=16, max_length=255)
    fcm_token: str | None = Field(default=None, max_length=4096)


class ChatRoomCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    document_id: UUID | None = None
    member_ids: list[UUID] = Field(default_factory=list, max_length=200)


class ChatMessageCreate(BaseModel):
    body: str = Field(min_length=1, max_length=8000)


@router.get("/notifications")
async def notifications(
    session: SessionDep,
    user: CurrentUser,
    unread_only: bool = False,
    limit: int = Query(default=100, ge=1, le=200),
) -> list[dict]:
    query = select(Notification).where(Notification.user_id == user.id)
    if unread_only:
        query = query.where(Notification.read_at.is_(None))
    rows = list((await session.execute(query.order_by(Notification.created_at.desc()).limit(limit))).scalars())
    return [
        {
            "id": str(row.id),
            "event_type": row.event_type,
            "title": row.title,
            "body": row.body,
            "payload": row.payload,
            "read_at": row.read_at,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/notifications/{notification_id}/read", status_code=204)
async def mark_notification_read(notification_id: UUID, session: SessionDep, user: CurrentUser) -> None:
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notifikasi tidak ditemukan")
    notification.read_at = datetime.now(UTC)
    await session.commit()


@router.get("/devices")
async def devices(session: SessionDep, user: CurrentUser) -> list[dict]:
    rows = list(
        (
            await session.execute(
                select(UserDevice).where(UserDevice.user_id == user.id).order_by(UserDevice.created_at.desc())
            )
        ).scalars()
    )
    return [
        {
            "id": str(row.id),
            "device_fingerprint": row.device_fingerprint,
            "registered_at": row.created_at,
            "revoked_at": row.revoked_at,
        }
        for row in rows
    ]


@router.post("/devices/register")
async def register_device(
    payload: DeviceRegistration,
    session: SessionDep,
    user: CurrentUser,
) -> dict:
    device = (
        await session.execute(select(UserDevice).where(UserDevice.device_fingerprint == payload.device_fingerprint))
    ).scalar_one_or_none()
    if device and device.user_id != user.id:
        raise HTTPException(status_code=409, detail="Perangkat telah terdaftar pada akun lain")
    if not device:
        device = UserDevice(
            user_id=user.id,
            device_fingerprint=payload.device_fingerprint,
            fcm_token=payload.fcm_token,
        )
        session.add(device)
    else:
        device.fcm_token = payload.fcm_token
        device.revoked_at = None
    await session.commit()
    await session.refresh(device)
    return {"id": str(device.id), "revoked_at": device.revoked_at}


@router.post("/devices/{device_id}/revoke", status_code=204)
async def revoke_device(device_id: UUID, session: SessionDep, user: CurrentUser) -> None:
    device = await session.get(UserDevice, device_id)
    if not device or device.user_id != user.id:
        raise HTTPException(status_code=404, detail="Perangkat tidak ditemukan")
    device.revoked_at = datetime.now(UTC)
    device.fcm_token = None
    record_audit(
        session,
        actor_user_id=user.id,
        action="DEVICE_REVOKED",
        entity_type="UserDevice",
        entity_id=device.id,
    )
    await session.commit()


@router.get("/chat/rooms")
async def chat_rooms(
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("chat.use")),
) -> list[dict]:
    rows = (
        await session.execute(
            select(ChatRoom)
            .join(ChatMember, ChatMember.room_id == ChatRoom.id)
            .where(ChatMember.user_id == user.id)
            .order_by(ChatRoom.updated_at.desc())
        )
    ).scalars()
    return [
        {
            "id": str(row.id),
            "name": row.name,
            "document_id": str(row.document_id) if row.document_id else None,
            "updated_at": row.updated_at,
        }
        for row in rows
    ]


@router.post("/chat/rooms", status_code=201)
async def create_chat_room(
    payload: ChatRoomCreate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("chat.use")),
) -> dict:
    member_ids = set(payload.member_ids) | {user.id}
    existing_users = set(
        (await session.execute(select(User.id).where(User.id.in_(member_ids), User.active.is_(True)))).scalars()
    )
    if member_ids != existing_users:
        raise HTTPException(status_code=422, detail="Satu atau lebih anggota tidak ditemukan")
    room = ChatRoom(name=payload.name.strip(), document_id=payload.document_id)
    session.add(room)
    await session.flush()
    session.add_all(ChatMember(room_id=room.id, user_id=member_id) for member_id in member_ids)
    await session.commit()
    return {"id": str(room.id), "name": room.name}


async def _require_room_member(session: SessionDep, room_id: UUID, user_id: UUID) -> ChatRoom:
    room = await session.get(ChatRoom, room_id)
    membership = (
        await session.execute(select(ChatMember.id).where(ChatMember.room_id == room_id, ChatMember.user_id == user_id))
    ).scalar_one_or_none()
    if not room or not membership:
        raise HTTPException(status_code=404, detail="Ruang chat tidak ditemukan")
    return room


@router.get("/chat/rooms/{room_id}/messages")
async def chat_messages(
    room_id: UUID,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("chat.use")),
    limit: int = Query(default=100, ge=1, le=200),
) -> list[dict]:
    await _require_room_member(session, room_id, user.id)
    rows = list(
        (
            await session.execute(
                select(ChatMessage, User.full_name)
                .join(User, User.id == ChatMessage.sender_id)
                .where(ChatMessage.room_id == room_id)
                .order_by(ChatMessage.created_at.desc())
                .limit(limit)
            )
        ).all()
    )
    return [
        {
            "id": str(message.id),
            "sender_id": str(message.sender_id),
            "sender_name": sender_name,
            "body": message.body,
            "created_at": message.created_at,
        }
        for message, sender_name in reversed(rows)
    ]


@router.post("/chat/rooms/{room_id}/messages", status_code=201)
async def create_chat_message(
    room_id: UUID,
    payload: ChatMessageCreate,
    session: SessionDep,
    user: CurrentUser,
    _: object = Depends(require_permission("chat.use")),
) -> dict:
    room = await _require_room_member(session, room_id, user.id)
    message = ChatMessage(room_id=room_id, sender_id=user.id, body=payload.body.strip())
    session.add(message)
    room.updated_at = datetime.now(UTC)
    member_ids = list(
        (
            await session.execute(
                select(ChatMember.user_id).where(
                    ChatMember.room_id == room_id,
                    ChatMember.user_id != user.id,
                )
            )
        ).scalars()
    )
    for member_id in member_ids:
        session.add(
            Notification(
                user_id=member_id,
                event_type="NEW_CHAT_MESSAGE",
                title=f"Pesan baru di {room.name}",
                body=f"{user.full_name}: {message.body[:160]}",
                payload={"room_id": str(room.id)},
            )
        )
    await session.commit()
    await session.refresh(message)
    result = {
        "id": str(message.id),
        "sender_id": str(user.id),
        "sender_name": user.full_name,
        "body": message.body,
        "created_at": message.created_at.isoformat(),
    }
    await realtime_hub.broadcast(room_id, {"event": "NEW_CHAT_MESSAGE", "message": result})
    return result


@router.websocket("/chat/rooms/{room_id}/ws")
async def chat_websocket(websocket: WebSocket, room_id: UUID, access_token: str) -> None:
    try:
        claims = decode_token(access_token)
        if claims.get("type") != "access":
            raise ValueError("wrong token type")
        user_id = UUID(claims["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        await websocket.close(code=4401, reason="Kredensial tidak valid")
        return
    async with SessionLocal() as session:
        user = await session.get(User, user_id)
        membership = (
            await session.execute(
                select(ChatMember.id).where(ChatMember.room_id == room_id, ChatMember.user_id == user_id)
            )
        ).scalar_one_or_none()
        if not user or not user.active or claims.get("ver") != user.token_version:
            await websocket.close(code=4401, reason="Akun tidak aktif")
            return
        if not membership:
            await websocket.close(code=4403, reason="Bukan anggota ruang")
            return
        await realtime_hub.connect(room_id, websocket)
        try:
            await websocket.send_json({"event": "CONNECTED", "room_id": str(room_id)})
            while True:
                message = await websocket.receive_json()
                if message.get("event") == "PING":
                    await websocket.send_json({"event": "PONG"})
        except WebSocketDisconnect:
            pass
        finally:
            await realtime_hub.disconnect(room_id, websocket)
