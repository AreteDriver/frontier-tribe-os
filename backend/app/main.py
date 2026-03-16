import logging
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.middleware.base import BaseHTTPMiddleware

from app.auth.routes import router as auth_router
from app.config import settings
from app.db.models import Base
from app.db.session import engine
from app.modules.census.routes import router as census_router
from app.modules.forge.routes import router as forge_router
from app.modules.ledger.routes import router as ledger_router
from app.modules.alerts.routes import router as alerts_router
from app.modules.intel.routes import router as intel_router
from app.modules.warden.routes import router as warden_router
from app.modules.watch.routes import router as watch_router
from app.rate_limit import limiter

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Inject CSP, HSTS, and security headers on every response."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https://images.evetech.net; "
            "connect-src 'self' https://esi.evetech.net https://fullnode.mainnet.sui.io; "
            "frame-src https://ef-map.com; "
            "object-src 'none'; "
            "frame-ancestors 'none'"
        )
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
        response.headers["Permissions-Policy"] = (
            "camera=(), microphone=(), payment=(), geolocation=()"
        )
        return response


class RequestIdMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request/response for log correlation."""

    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = str(uuid.uuid4())[:8]
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Structured logging
    from app.logging_config import configure_logging

    configure_logging(settings.log_level)

    # Create tables on startup (dev only — use Alembic in prod)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Start background World API poller if enabled
    poller = None
    if settings.enable_poller:
        from app.modules.watch.poller import WorldAPIPoller

        poller = WorldAPIPoller()
        await poller.start()

    yield

    if poller:
        await poller.stop()
    await engine.dispose()


app = FastAPI(
    title="Frontier Tribe OS",
    description="Operations platform for EVE Frontier Tribes and Syndicates",
    version="0.1.0",
    lifespan=lifespan,
)

# --- Rate limiter state ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Global exception handler ---


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    logger.exception("Unhandled error [%s]: %s", request_id, exc)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "request_id": request_id},
    )


# --- Middleware (LIFO order: last added = first executed) ---
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(auth_router)
app.include_router(census_router)
app.include_router(forge_router)
app.include_router(ledger_router)
app.include_router(warden_router)
app.include_router(alerts_router)
app.include_router(intel_router)
app.include_router(watch_router)


@app.get("/health")
@limiter.exempt
async def health():
    return {"status": "ok", "service": "frontier-tribe-os"}
