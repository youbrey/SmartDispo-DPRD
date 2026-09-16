from datetime import date

import pytest
from pydantic import ValidationError

from app.schemas.common import DispositionCreate, DispositionTargetInput, IncomingLetterCreate
from app.services.dispositions import DPRD_DIRECTIVES, SETWAN_DIRECTIVES
from app.services.incoming_letters import incoming_content


def test_incoming_letter_selects_correct_disposition_sheet() -> None:
    payload = IncomingLetterCreate(
        route_type="DPRD",
        sender="Kementerian Dalam Negeri",
        letter_number="100/123",
        letter_date=date(2026, 9, 15),
        received_date=date(2026, 9, 16),
        agenda_number="AG-001",
        agenda_date=date(2026, 9, 16),
        subject="Koordinasi penyelenggaraan pemerintahan daerah",
        priority="PENTING",
    )
    assert incoming_content(payload)["sheet_type"] == "DISPOSITION_DPRD"


def test_incoming_letter_rejects_received_date_before_letter_date() -> None:
    with pytest.raises(ValidationError):
        IncomingLetterCreate(
            route_type="SETWAN",
            sender="Instansi A",
            letter_number="001",
            letter_date=date(2026, 9, 16),
            received_date=date(2026, 9, 15),
            agenda_number="AG-002",
            agenda_date=date(2026, 9, 15),
            subject="Permohonan koordinasi",
            priority="BIASA",
        )


def test_disposition_requires_unique_directives_and_single_target_kind() -> None:
    with pytest.raises(ValidationError):
        DispositionCreate(actor_role="CHAIRMAN", directives=["FOLLOW_UP", "follow_up"])
    with pytest.raises(ValidationError):
        DispositionTargetInput()


def test_dprd_and_setwan_directives_are_separate() -> None:
    assert "FORWARD_COMMISSION_I" in DPRD_DIRECTIVES
    assert "FORWARD_COMMISSION_I" not in SETWAN_DIRECTIVES
    assert "CREATE_REVIEW_ADVICE" in SETWAN_DIRECTIVES
    assert "CREATE_REVIEW_ADVICE" not in DPRD_DIRECTIVES
