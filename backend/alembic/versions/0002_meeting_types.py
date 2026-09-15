"""Add configurable meeting type master data."""

from alembic import op

revision = "0002_meeting_types"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

MEETING_TYPES = [
    ("00000000-0000-0000-0001-000000000001", "PLENARY", "Rapat Paripurna", 10),
    ("00000000-0000-0000-0001-000000000002", "LEADERSHIP", "Rapat Pimpinan DPRD", 20),
    ("00000000-0000-0000-0001-000000000003", "FRACTION", "Rapat Fraksi", 30),
    ("00000000-0000-0000-0001-000000000004", "CONSULTATION", "Rapat Konsultasi", 40),
    ("00000000-0000-0000-0001-000000000005", "BAMUS", "Rapat Badan Musyawarah", 50),
    ("00000000-0000-0000-0001-000000000006", "COMMISSION", "Rapat Komisi", 60),
    ("00000000-0000-0000-0001-000000000007", "JOINT_COMMISSION", "Rapat Gabungan Komisi", 70),
    ("00000000-0000-0000-0001-000000000008", "BAPEMPERDA", "Rapat Bapemperda", 80),
    ("00000000-0000-0000-0001-000000000009", "BANGGAR", "Rapat Badan Anggaran", 90),
    ("00000000-0000-0000-0001-000000000010", "BK", "Rapat Badan Kehormatan", 100),
    ("00000000-0000-0000-0001-000000000011", "PANSUS", "Rapat Panitia Khusus", 110),
    ("00000000-0000-0000-0001-000000000012", "WORK_MEETING", "Rapat Kerja", 120),
    ("00000000-0000-0000-0001-000000000013", "HEARING", "Rapat Dengar Pendapat", 130),
    ("00000000-0000-0000-0001-000000000014", "PUBLIC_HEARING", "Rapat Dengar Pendapat Umum", 140),
    ("00000000-0000-0000-0001-000000000015", "LEADERS_MEMBERS", "Rapat Pimpinan dan Anggota DPRD", 150),
]


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS meeting_types (
            id UUID PRIMARY KEY,
            code VARCHAR(80) NOT NULL UNIQUE,
            name VARCHAR(255) NOT NULL,
            sort_order INTEGER NOT NULL DEFAULT 0,
            active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS ix_meeting_types_active ON meeting_types (active)")
    for item_id, code, name, sort_order in MEETING_TYPES:
        escaped_name = name.replace("'", "''")
        op.execute(
            f"""
            INSERT INTO meeting_types (id, code, name, sort_order, active, created_at, updated_at)
            VALUES ('{item_id}', '{code}', '{escaped_name}', {sort_order}, TRUE, NOW(), NOW())
            ON CONFLICT (code) DO NOTHING
            """
        )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS meeting_types")
