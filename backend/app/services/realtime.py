import asyncio
from collections import defaultdict
from uuid import UUID

from fastapi import WebSocket


class RealtimeHub:
    def __init__(self) -> None:
        self._rooms: dict[UUID, set[WebSocket]] = defaultdict(set)
        self._lock = asyncio.Lock()

    async def connect(self, room_id: UUID, websocket: WebSocket) -> None:
        await websocket.accept()
        async with self._lock:
            self._rooms[room_id].add(websocket)

    async def disconnect(self, room_id: UUID, websocket: WebSocket) -> None:
        async with self._lock:
            connections = self._rooms.get(room_id)
            if not connections:
                return
            connections.discard(websocket)
            if not connections:
                self._rooms.pop(room_id, None)

    async def broadcast(self, room_id: UUID, payload: dict) -> None:
        async with self._lock:
            connections = tuple(self._rooms.get(room_id, ()))
        stale: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except RuntimeError:
                stale.append(websocket)
        for websocket in stale:
            await self.disconnect(room_id, websocket)


realtime_hub = RealtimeHub()
