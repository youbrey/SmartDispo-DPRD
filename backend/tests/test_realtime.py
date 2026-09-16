from uuid import uuid4

import pytest

from app.services.realtime import RealtimeHub


class FakeSocket:
    def __init__(self) -> None:
        self.accepted = False
        self.messages: list[dict] = []

    async def accept(self) -> None:
        self.accepted = True

    async def send_json(self, payload: dict) -> None:
        self.messages.append(payload)


@pytest.mark.asyncio
async def test_realtime_hub_broadcasts_only_to_connected_room() -> None:
    hub = RealtimeHub()
    room_id = uuid4()
    other_room_id = uuid4()
    socket = FakeSocket()
    other_socket = FakeSocket()
    await hub.connect(room_id, socket)  # type: ignore[arg-type]
    await hub.connect(other_room_id, other_socket)  # type: ignore[arg-type]
    await hub.broadcast(room_id, {"event": "NEW_CHAT_MESSAGE"})
    assert socket.accepted
    assert socket.messages == [{"event": "NEW_CHAT_MESSAGE"}]
    assert other_socket.messages == []
    await hub.disconnect(room_id, socket)  # type: ignore[arg-type]
