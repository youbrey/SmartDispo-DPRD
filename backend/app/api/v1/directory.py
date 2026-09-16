from fastapi import APIRouter, Depends
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep, require_permission
from app.models.entities import OrganizationalUnit, Role, User
from app.schemas.common import DispositionTargetOption

router = APIRouter(prefix="/directory", tags=["directory"])


@router.get("/disposition-targets", response_model=list[DispositionTargetOption])
async def disposition_targets(
    session: SessionDep,
    _: CurrentUser,
    __: object = Depends(require_permission("disposition.create")),
) -> list[DispositionTargetOption]:
    units = list(
        (
            await session.execute(
                select(OrganizationalUnit)
                .where(OrganizationalUnit.active.is_(True))
                .order_by(OrganizationalUnit.name)
            )
        ).scalars()
    )
    roles = list((await session.execute(select(Role).order_by(Role.name))).scalars())
    users = list(
        (
            await session.execute(
                select(User).where(User.active.is_(True)).order_by(User.full_name)
            )
        ).scalars()
    )
    return [
        *[
            DispositionTargetOption(
                target_type="UNIT", target_id=unit.id, label=unit.name, subtitle=f"Unit / AKD · {unit.code}"
            )
            for unit in units
        ],
        *[
            DispositionTargetOption(
                target_type="ROLE", target_id=role.id, label=role.name, subtitle=f"Role · {role.code}"
            )
            for role in roles
        ],
        *[
            DispositionTargetOption(
                target_type="USER", target_id=user.id, label=user.full_name, subtitle="Pengguna"
            )
            for user in users
        ],
    ]
