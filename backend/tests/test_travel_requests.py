from datetime import date, time

import pytest
from pydantic import ValidationError

from app.schemas.common import TravelMemberInput, TravelRequestCreate, TravelRequestUpdate
from app.services.travel_requests import travel_content


def payload(**changes) -> TravelRequestCreate:
    values = {
        "sender_name": "Komisi I",
        "sender_position": "Pimpinan Komisi I",
        "organizational_unit": "Komisi I",
        "activity_type": "CONSULTATION",
        "destinations": ["Kementerian Dalam Negeri"],
        "purpose": "Koordinasi pelaksanaan pemerintahan daerah",
        "material": "Pelaksanaan tugas dan fungsi DPRD",
        "general_problem": "Diperlukan penyelarasan regulasi",
        "current_condition": "Pelaksanaan belum seragam",
        "efforts": "Melakukan rapat internal dan pengumpulan data",
        "start_date": date(2026, 9, 21),
        "end_date": date(2026, 9, 23),
        "activity_time": time(9, 0),
        "place": "Jakarta",
        "members": [
            TravelMemberInput(name="Anggota DPRD A", position="Anggota", member_group="EXECUTOR"),
            TravelMemberInput(name="Staf A", position="Pendamping", member_group="ACCOMPANYING"),
        ],
    }
    values.update(changes)
    return TravelRequestCreate(**values)


def test_travel_content_reuses_dynamic_members_and_calculates_duration() -> None:
    content = travel_content(payload())
    assert content["duration_days"] == 3
    assert content["destinations"] == ["Kementerian Dalam Negeri"]
    assert [item["name"] for item in content["members"]] == ["Anggota DPRD A", "Staf A"]


def test_travel_request_rejects_invalid_dates_and_missing_executor() -> None:
    with pytest.raises(ValidationError):
        payload(start_date=date(2026, 9, 23), end_date=date(2026, 9, 21))
    with pytest.raises(ValidationError):
        payload(members=[TravelMemberInput(name="Staf A", member_group="ACCOMPANYING")])


def test_travel_request_rejects_duplicate_destinations_and_members() -> None:
    with pytest.raises(ValidationError):
        payload(destinations=["Jakarta", " jakarta "])
    with pytest.raises(ValidationError):
        payload(
            members=[
                TravelMemberInput(name="Anggota A", member_group="EXECUTOR"),
                TravelMemberInput(name="anggota a", member_group="EXECUTOR"),
            ]
        )


def test_version_content_does_not_persist_concurrency_metadata() -> None:
    update = TravelRequestUpdate(**payload().model_dump(), expected_lock_version=2, change_reason="Ubah tujuan")
    content = travel_content(update)
    assert "expected_lock_version" not in content
    assert "change_reason" not in content
