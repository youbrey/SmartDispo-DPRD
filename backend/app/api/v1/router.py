from fastapi import APIRouter

from app.api.v1 import (
    admin,
    attachments,
    auth,
    communications,
    dispositions,
    documents,
    incoming_letters,
    meeting_requests,
    sips,
    tasks,
    travel_requests,
)

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(meeting_requests.router)
router.include_router(travel_requests.router)
router.include_router(incoming_letters.router)
router.include_router(dispositions.router)
router.include_router(tasks.router)
router.include_router(admin.router)
router.include_router(attachments.router)
router.include_router(communications.router)
router.include_router(sips.router)
