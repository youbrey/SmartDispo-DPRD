import os

import httpx
import pytest

from app.db.session import engine
from app.main import app

pytestmark = pytest.mark.skipif(
    os.getenv("SMARTDISPO_RUN_INTEGRATION") != "1",
    reason="Integration test membutuhkan PostgreSQL terisolasi",
)


@pytest.fixture(autouse=True)
async def dispose_database_pool_after_test():
    """Keep asyncpg connections bound to the event loop that created them."""
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_meeting_request_reaches_completed_workflow() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "integration-admin-password"},
        )
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        device_id = "github-actions-integration"
        registered = await client.post(
            "/api/v1/devices/register",
            headers=headers,
            json={"device_fingerprint": device_id},
        )
        assert registered.status_code == 200, registered.text
        headers["X-Device-ID"] = device_id

        profile = await client.get("/api/v1/auth/me", headers=headers)
        assert profile.status_code == 200, profile.text
        assert "meeting_request.create" in profile.json()["permissions"]
        user_id = profile.json()["id"]

        types = await client.get("/api/v1/meeting-types", headers=headers)
        assert types.status_code == 200, types.text
        assert any(item["code"] == "HEARING" for item in types.json())

        workflow = await client.post(
            "/api/v1/admin/workflows",
            headers=headers,
            json={
                "name": "Integration Meeting Approval",
                "document_type": "MEETING_REQUEST",
                "steps": [
                    {
                        "step_key": "ADMIN_APPROVAL",
                        "name": "Persetujuan Administrator",
                        "assignment_rule": {"user_id": user_id},
                        "allowed_actions": ["APPROVE"],
                    }
                ],
            },
        )
        assert workflow.status_code == 201, workflow.text
        published = await client.post(
            f"/api/v1/admin/workflows/{workflow.json()['id']}/publish",
            headers=headers,
        )
        assert published.status_code == 200, published.text

        created = await client.post(
            "/api/v1/meeting-requests",
            headers=headers,
            json={
                "sender_name": "Staf Tata Usaha",
                "sender_position": "Pengadministrasi Perkantoran",
                "meeting_type_code": "HEARING",
                "purpose": "Membahas aspirasi masyarakat Kota Bitung",
                "scheduled_at": "2026-09-21T10:00:00+08:00",
                "place": "Ruang Rapat Komisi I",
                "attire": "Pakaian dinas harian",
                "invitees": [
                    {"name": "Dinas Perhubungan", "institution": "Pemerintah Kota Bitung"},
                    {"name": "Bagian Hukum", "institution": "Sekretariat Daerah"},
                ],
            },
        )
        assert created.status_code == 201, created.text
        document_id = created.json()["document_id"]

        submitted = await client.post(f"/api/v1/documents/{document_id}/submit", headers=headers)
        assert submitted.status_code == 200, submitted.text
        assert submitted.json()["status"] == "IN_PROGRESS"

        tasks = await client.get("/api/v1/tasks/mine", headers=headers)
        assert tasks.status_code == 200, tasks.text
        task = next(item for item in tasks.json() if item["step_key"] == "ADMIN_APPROVAL")
        completed = await client.post(
            f"/api/v1/tasks/{task['id']}/actions",
            headers=headers,
            json={
                "action": "APPROVE",
                "expected_instance_lock_version": task["instance_lock_version"],
                "device_id": device_id,
            },
        )
        assert completed.status_code == 200, completed.text

        result = await client.get(f"/api/v1/meeting-requests/{document_id}", headers=headers)
        assert result.status_code == 200, result.text
        assert result.json()["document_status"] == "COMPLETED"
        assert [invitee["name"] for invitee in result.json()["invitees"]] == [
            "Dinas Perhubungan",
            "Bagian Hukum",
        ]


@pytest.mark.asyncio
async def test_travel_request_persists_dynamic_members() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "integration-admin-password"},
        )
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        created = await client.post(
            "/api/v1/travel-requests",
            headers=headers,
            json={
                "sender_name": "Komisi I",
                "sender_position": "Pimpinan Komisi I",
                "organizational_unit": "Komisi I",
                "activity_type": "WORK_VISIT",
                "destinations": ["DPRD Kota Depok", "DPRD Kota Bogor"],
                "purpose": "Studi penerapan administrasi pemerintahan",
                "material": "Pelaksanaan administrasi perjalanan dinas",
                "general_problem": "Diperlukan perbandingan tata kelola",
                "current_condition": "Proses saat ini masih dilakukan terpisah",
                "efforts": "Menghimpun dokumen dan melakukan rapat internal",
                "start_date": "2026-09-21",
                "end_date": "2026-09-23",
                "activity_time": "09:00:00",
                "place": "Depok dan Bogor",
                "members": [
                    {"name": "Anggota DPRD A", "position": "Anggota", "member_group": "EXECUTOR"},
                    {"name": "Staf Pendamping A", "position": "Staf", "member_group": "ACCOMPANYING"},
                ],
            },
        )
        assert created.status_code == 201, created.text
        assert created.json()["duration_days"] == 3
        assert [item["member_group"] for item in created.json()["members"]] == [
            "EXECUTOR",
            "ACCOMPANYING",
        ]


@pytest.mark.asyncio
async def test_incoming_letter_requires_officeholder_disposition_before_task_completion() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            data={"username": "admin", "password": "integration-admin-password"},
        )
        assert login.status_code == 200, login.text
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        profile = await client.get("/api/v1/auth/me", headers=headers)
        user_id = profile.json()["id"]
        registered = await client.post(
            "/api/v1/devices/register",
            headers=headers,
            json={"device_fingerprint": "incoming-integration-device"},
        )
        assert registered.status_code == 200, registered.text
        headers["X-Device-ID"] = "incoming-integration-device"

        roles = await client.get("/api/v1/admin/roles", headers=headers)
        chairman = next((role for role in roles.json() if role["code"] == "CHAIRMAN"), None)
        if chairman is None:
            created_role = await client.post(
                "/api/v1/admin/roles",
                headers=headers,
                json={"code": "CHAIRMAN", "name": "Ketua DPRD", "permission_ids": []},
            )
            assert created_role.status_code == 201, created_role.text
            chairman_id = created_role.json()["id"]
        else:
            chairman_id = chairman["id"]
        assigned = await client.post(
            "/api/v1/admin/role-assignments",
            headers=headers,
            json={
                "role_id": chairman_id,
                "user_id": user_id,
                "valid_from": "2026-01-01",
                "metadata": {},
            },
        )
        assert assigned.status_code == 201, assigned.text

        workflow = await client.post(
            "/api/v1/admin/workflows",
            headers=headers,
            json={
                "name": "Integration Incoming Chairman",
                "document_type": "INCOMING_CHAIRMAN",
                "steps": [
                    {
                        "step_key": "CHAIRMAN_DISPOSITION",
                        "name": "Disposisi Ketua",
                        "assignment_rule": {"user_id": user_id},
                        "allowed_actions": ["DISPOSITION"],
                    }
                ],
            },
        )
        assert workflow.status_code == 201, workflow.text
        published = await client.post(
            f"/api/v1/admin/workflows/{workflow.json()['id']}/publish",
            headers=headers,
        )
        assert published.status_code == 200, published.text

        created = await client.post(
            "/api/v1/incoming-letters",
            headers=headers,
            json={
                "route_type": "DPRD",
                "sender": "Pemerintah Kota Bitung",
                "letter_number": "INT/DPRD/001",
                "letter_date": "2026-09-15",
                "received_date": "2026-09-16",
                "agenda_number": "INT-AGENDA-DPRD-001",
                "agenda_date": "2026-09-16",
                "subject": "Permohonan rapat koordinasi integrasi",
                "priority": "PENTING",
            },
        )
        assert created.status_code == 201, created.text
        document_id = created.json()["document_id"]
        submitted = await client.post(f"/api/v1/documents/{document_id}/submit", headers=headers)
        assert submitted.status_code == 200, submitted.text
        tasks = await client.get("/api/v1/tasks/mine", headers=headers)
        task = next(item for item in tasks.json() if item["document_id"] == document_id)

        premature = await client.post(
            f"/api/v1/tasks/{task['id']}/actions",
            headers=headers,
            json={
                "action": "DISPOSITION",
                "expected_instance_lock_version": task["instance_lock_version"],
                "device_id": "incoming-integration-device",
            },
        )
        assert premature.status_code == 409, premature.text
        disposition = await client.post(
            f"/api/v1/documents/{document_id}/dispositions",
            headers=headers,
            json={
                "actor_role": "CHAIRMAN",
                "directives": ["FOLLOW_UP"],
                "note": "Tindak lanjuti sesuai mekanisme.",
            },
        )
        assert disposition.status_code == 201, disposition.text
        completed = await client.post(
            f"/api/v1/tasks/{task['id']}/actions",
            headers=headers,
            json={
                "action": "DISPOSITION",
                "expected_instance_lock_version": task["instance_lock_version"],
                "device_id": "incoming-integration-device",
            },
        )
        assert completed.status_code == 200, completed.text
        result = await client.get(f"/api/v1/documents/{document_id}", headers=headers)
        assert result.json()["status"] == "COMPLETED"
