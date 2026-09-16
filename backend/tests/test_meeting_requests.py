from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.schemas.common import MeetingInviteeInput, MeetingRequestCreate, MeetingRequestUpdate
from app.services.meeting_requests import meeting_content


def payload(**changes) -> MeetingRequestCreate:
    values = {
        "sender_name": "Sekretariat Komisi I",
        "sender_position": "Staf Tata Usaha",
        "meeting_type_code": "HEARING",
        "purpose": "Membahas aspirasi masyarakat",
        "scheduled_at": datetime(2026, 9, 21, 10, 0, tzinfo=UTC),
        "place": "Ruang Rapat Komisi I",
        "attire": "Pakaian dinas harian",
        "invitees": [MeetingInviteeInput(name="Dinas Perhubungan", institution="Pemerintah Kota Bitung")],
    }
    values.update(changes)
    return MeetingRequestCreate(**values)


def test_content_uses_only_selected_meeting_type_and_dynamic_invitees() -> None:
    content = meeting_content(payload(), "Rapat Dengar Pendapat")
    assert content["meeting_type_name"] == "Rapat Dengar Pendapat"
    assert content["meeting_type_code"] == "HEARING"
    assert content["invitees"] == [{"name": "Dinas Perhubungan", "institution": "Pemerintah Kota Bitung"}]
    assert "Rapat Paripurna" not in str(content)


def test_request_rejects_more_than_twenty_invitees() -> None:
    invitees = [MeetingInviteeInput(name=f"Undangan {index}") for index in range(21)]
    with pytest.raises(ValidationError):
        payload(invitees=invitees)


def test_request_rejects_naive_datetime_and_duplicate_invitee() -> None:
    with pytest.raises(ValidationError):
        payload(scheduled_at=datetime(2026, 9, 21, 10, 0))
    duplicate = [MeetingInviteeInput(name="Bagian Hukum"), MeetingInviteeInput(name="bagian hukum")]
    with pytest.raises(ValidationError):
        payload(invitees=duplicate)


def test_version_content_does_not_persist_concurrency_metadata() -> None:
    update = MeetingRequestUpdate(**payload().model_dump(), expected_lock_version=4, change_reason="Ubah jadwal")
    content = meeting_content(update, "Rapat Dengar Pendapat")
    assert "expected_lock_version" not in content
    assert "change_reason" not in content
