from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import AuditLog


def record_audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID | None,
    action: str,
    entity_type: str,
    entity_id: UUID | None,
    before: dict | None = None,
    after: dict | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
) -> None:
    session.add(
        AuditLog(
            occurred_at=datetime.now(UTC),
            actor_user_id=actor_user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before_data=before,
            after_data=after,
            request_id=request_id,
            ip_address=ip_address,
        )
    )
