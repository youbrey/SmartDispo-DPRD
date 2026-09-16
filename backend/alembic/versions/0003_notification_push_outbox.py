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
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("notifications")}
    if "push_sent_at" not in column_names:
        op.add_column(
            "notifications",
            sa.Column("push_sent_at", sa.DateTime(timezone=True), nullable=True),
        )

    # Recreate the inspector after DDL because PostgreSQL inspector results are cached.
    inspector = sa.inspect(bind)
    index_names = {index["name"] for index in inspector.get_indexes("notifications")}
    if "ix_notifications_push_sent_at" not in index_names:
        op.create_index("ix_notifications_push_sent_at", "notifications", ["push_sent_at"])


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    index_names = {index["name"] for index in inspector.get_indexes("notifications")}
    if "ix_notifications_push_sent_at" in index_names:
        op.drop_index("ix_notifications_push_sent_at", table_name="notifications")

    inspector = sa.inspect(bind)
    column_names = {column["name"] for column in inspector.get_columns("notifications")}
    if "push_sent_at" in column_names:
        op.drop_column("notifications", "push_sent_at")
