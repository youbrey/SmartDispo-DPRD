"""Add notification push outbox marker.

Revision ID: 0003_notification_push_outbox
Revises: 0002_meeting_types
"""

import sqlalchemy as sa

from alembic import op

revision = "0003_notification_push_outbox"
down_revision = "0002_meeting_types"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("notifications", sa.Column("push_sent_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_notifications_push_sent_at", "notifications", ["push_sent_at"])


def downgrade() -> None:
    op.drop_index("ix_notifications_push_sent_at", table_name="notifications")
    op.drop_column("notifications", "push_sent_at")
