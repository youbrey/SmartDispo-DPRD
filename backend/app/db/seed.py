import asyncio
import os
from hashlib import sha256
from pathlib import Path

from sqlalchemy import select

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.entities import (
    ChatMember,
    ChatRoom,
    DocumentTemplate,
    DocumentTemplateVersion,
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
)
from app.services.templates import TEMPLATE_DEFINITIONS

PERMISSIONS = {
    "document.create": "Membuat dokumen",
    "document.read": "Membaca dokumen",
    "document.edit": "Mengubah draft atau dokumen yang dikembalikan",
    "document.submit": "Mengirim dokumen ke workflow",
    "document.upload": "Mengunggah lampiran dokumen",
    "document.download": "Mengunduh dokumen dan lampiran",
    "document.print": "Mencetak dokumen final",
    "meeting_request.create": "Membuat permintaan rapat",
    "meeting_request.edit": "Mengubah permintaan rapat milik sendiri",
    "travel_request.create": "Membuat permintaan perjalanan dinas",
    "travel_request.edit": "Mengubah permintaan perjalanan dinas milik sendiri",
    "incoming_letter.create": "Mencatat dan mengagendakan surat masuk",
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
    "chat.use": "Menggunakan chat umum dan chat dokumen",
    "device.manage": "Mengelola dan mencabut perangkat",
    "archive.read": "Membaca arsip dokumen selesai",
    "integration.manage": "Mengelola integrasi SIPS",
}


async def seed() -> None:
    username = os.getenv("SMARTDISPO_BOOTSTRAP_ADMIN_USERNAME", "admin")
    password = os.getenv("SMARTDISPO_BOOTSTRAP_ADMIN_PASSWORD")
    if not password or len(password) < 12:
        raise RuntimeError("Set SMARTDISPO_BOOTSTRAP_ADMIN_PASSWORD minimal 12 karakter")
    async with SessionLocal() as session:
        role = (await session.execute(select(Role).where(Role.code == "ADMIN"))).scalar_one_or_none()
        if not role:
            role = Role(code="ADMIN", name="Administrator Sistem", system=True)
            session.add(role)
        user = (await session.execute(select(User).where(User.username == username))).scalar_one_or_none()
        if not user:
            user = User(
                username=username,
                full_name="Administrator SmartDispo",
                password_hash=hash_password(password),
                access_level=100,
            )
            session.add(user)
        await session.flush()
        for code, description in PERMISSIONS.items():
            permission = (await session.execute(select(Permission).where(Permission.code == code))).scalar_one_or_none()
            if not permission:
                permission = Permission(code=code, description=description)
                session.add(permission)
                await session.flush()
            role_permission = (
                await session.execute(
                    select(RolePermission).where(
                        RolePermission.role_id == role.id,
                        RolePermission.permission_id == permission.id,
                    )
                )
            ).scalar_one_or_none()
            if not role_permission:
                session.add(RolePermission(role_id=role.id, permission_id=permission.id))
        user_role = (
            await session.execute(select(UserRole).where(UserRole.user_id == user.id, UserRole.role_id == role.id))
        ).scalar_one_or_none()
        if not user_role:
            session.add(UserRole(user_id=user.id, role_id=role.id))
        general_room = (
            await session.execute(select(ChatRoom).where(ChatRoom.name == "Umum", ChatRoom.document_id.is_(None)))
        ).scalar_one_or_none()
        if not general_room:
            general_room = ChatRoom(name="Umum")
            session.add(general_room)
            await session.flush()
        general_member = (
            await session.execute(
                select(ChatMember).where(
                    ChatMember.room_id == general_room.id,
                    ChatMember.user_id == user.id,
                )
            )
        ).scalar_one_or_none()
        if not general_member:
            session.add(ChatMember(room_id=general_room.id, user_id=user.id))
        template_root = Path(get_settings().template_dir)
        for code, name, filename in TEMPLATE_DEFINITIONS.values():
            source = template_root / filename
            if not source.exists():
                raise RuntimeError(f"Template bawaan tidak ditemukan: {source}")
            template = (
                await session.execute(select(DocumentTemplate).where(DocumentTemplate.code == code))
            ).scalar_one_or_none()
            if not template:
                template = DocumentTemplate(code=code, name=name)
                session.add(template)
                await session.flush()
            version = (
                await session.execute(
                    select(DocumentTemplateVersion).where(
                        DocumentTemplateVersion.template_id == template.id,
                        DocumentTemplateVersion.version == 1,
                    )
                )
            ).scalar_one_or_none()
            if not version:
                session.add(
                    DocumentTemplateVersion(
                        template_id=template.id,
                        version=1,
                        object_key=f"builtin/{filename}",
                        sha256_hash=sha256(source.read_bytes()).hexdigest(),
                        active=True,
                    )
                )
        await session.commit()


if __name__ == "__main__":
    asyncio.run(seed())
