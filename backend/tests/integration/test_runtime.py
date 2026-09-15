import os

import httpx
import pytest

from app.main import app

pytestmark = pytest.mark.skipif(
    os.getenv("SMARTDISPO_RUN_INTEGRATION") != "1",
    reason="Integration test membutuhkan PostgreSQL terisolasi",
)


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
                "device_id": "github-actions-integration",
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
