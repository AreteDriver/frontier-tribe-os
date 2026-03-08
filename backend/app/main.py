from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.auth.routes import router as auth_router
from app.config import settings
from app.db.models import Base
from app.db.session import engine
from app.modules.census.routes import router as census_router
from app.modules.forge.routes import router as forge_router
from app.modules.ledger.routes import router as ledger_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (dev only — use Alembic in prod)
    if settings.environment == "development":
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Frontier Tribe OS",
    description="Operations platform for EVE Frontier Tribes and Syndicates",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(census_router)
app.include_router(forge_router)
app.include_router(ledger_router)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "frontier-tribe-os"}
