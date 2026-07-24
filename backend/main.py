from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal
from app.models.base import BaseModel
from app.api.v1.router import api_v1_router
from app.services.seed_service import SeedService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup if they don't exist
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    # Seed baseline database if empty
    async with AsyncSessionLocal() as db:
        try:
            await SeedService.auto_seed_if_empty(db)
        except Exception as e:
            print(f"[Lifespan Seed Error] {e}")

    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

# CORS configuration with explicit origins when allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


app.include_router(api_v1_router, prefix=settings.API_V1_STR)
