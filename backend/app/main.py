import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import router
from app.core.config import get_settings
from app.services.push import push_configured, push_worker
from app.services.rate_limit import rate_limiter


@asynccontextmanager
async def lifespan(_: FastAPI):
    stop = asyncio.Event()
    worker = asyncio.create_task(push_worker(stop)) if push_configured() else None
    try:
        yield
    finally:
        stop.set()
        if worker:
            await worker


app = FastAPI(
    title="SmartDispo DPRD Kota Bitung API",
    version="0.4.0",
    lifespan=lifespan,
    docs_url="/docs" if get_settings().env != "production" else None,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Device-ID"],
)


@app.middleware("http")
async def enforce_rate_limit(request: Request, call_next):
    settings = get_settings()
    is_login = request.url.path == "/api/v1/auth/login"
    limit = settings.login_rate_limit_per_minute if is_login else settings.api_rate_limit_per_minute
    client_ip = request.client.host if request.client else "unknown"
    group = "login" if is_login else "api"
    allowed, remaining = await rate_limiter.allow(f"{client_ip}:{group}", limit)
    if not allowed:
        return JSONResponse(
            status_code=429,
            content={"detail": "Terlalu banyak permintaan. Coba kembali sebentar lagi."},
            headers={"Retry-After": "60", "X-RateLimit-Remaining": "0"},
        )
    response = await call_next(request)
    response.headers["X-RateLimit-Limit"] = str(limit)
    response.headers["X-RateLimit-Remaining"] = str(remaining)
    return response


@app.middleware("http")
async def request_id(request: Request, call_next):
    request_id_value = request.headers.get("X-Request-ID", str(uuid4()))
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id_value
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


@app.get("/health", tags=["system"])
async def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(router)
