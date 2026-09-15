import asyncio
import os

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import Permission, Role, RolePermission, User, UserRole

PERMISSIONS = {
    "document.create": "Membuat dokumen",
    "document.read": "Membaca dokumen",
    "document.edit": "Mengubah draft atau dokumen yang dikembalikan",
    "document.submit": "Mengirim dokumen ke workflow",
    "task.sign": "Menandatangani dokumen",
    "task.verify": "Memverifikasi dokumen",
    "task.coordinate": "Memberikan paraf koordinasi",
    "task.approve": "Menyetujui dokumen",
    "task.return": "Mengembalikan dokumen",
    "disposition.create": "Membuat disposisi",
    "workflow.manage": "Mengelola workflow",
    "user.manage": "Mengelola pengguna",
    "role.manage": "Mengelola role dan permission",
    "template.manage": "Mengelola template dokumen",
    "admin.dashboard.read": "Membaca dashboard administrator",
    "audit.read": "Membaca audit log",
}


async def seed() -> None:
    username = os.getenv("SMARTDISPO_BOOTSTRAP_ADMIN_USERNAME", "admin")
    password = os.getenv("SMARTDISPO_BOOTSTRAP_ADMIN_PASSWORD")
    if not password or len(password) < 12:
        raise RuntimeError("Set SMARTDISPO_BOOTSTRAP_ADMIN_PASSWORD minimal 12 karakter")
    async with SessionLocal() as session:
        if (await session.execute(select(User).where(User.username == username))).scalar_one_or_none():
            return
        role = Role(code="ADMIN", name="Administrator Sistem", system=True)
        user = User(
            username=username,
            full_name="Administrator SmartDispo",
            password_hash=hash_password(password),
            access_level=100,
        )
        session.add_all([role, user])
        await session.flush()
        for code, description in PERMISSIONS.items():
            permission = Permission(code=code, description=description)
            session.add(permission)
            await session.flush()
            session.add(RolePermission(role_id=role.id, permission_id=permission.id))
        session.add(UserRole(user_id=user.id, role_id=role.id))
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
