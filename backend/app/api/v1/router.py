from fastapi import APIRouter

from app.api.v1 import admin, auth, documents, meeting_requests, tasks

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(meeting_requests.router)
router.include_router(tasks.router)
router.include_router(admin.router)
