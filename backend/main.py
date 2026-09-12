from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import engine, AsyncSessionLocal, ensure_database, get_db
from app.api.v1.router import api_v1_router
from app.services.seed_service import SeedService


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_database()

    # Seed baseline database if empty
    async with AsyncSessionLocal() as db:
        try:
            await SeedService.auto_seed_if_empty(db)
        except Exception as e:
            print(f"[Lifespan Seed Error] {e}")

    yield


from app.core.exceptions import DomainException, rfc7807_domain_exception_handler


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)

app.add_exception_handler(DomainException, rfc7807_domain_exception_handler)

# CORS configuration with explicit origins when allow_credentials=True
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["Health"])
@app.get(f"{settings.API_V1_STR}/health", tags=["Health"])
async def health_check():
    return {
        "status": "ok",
        "project": settings.PROJECT_NAME,
        "version": settings.VERSION,
    }


app.include_router(api_v1_router, prefix=settings.API_V1_STR)

# Global compatibility route aliases for legacy or frontend calls
@app.get(f"{settings.API_V1_STR}/versions", tags=["Timetable"], include_in_schema=False)
async def versions_alias(db=Depends(get_db)):
    from app.api.v1.timetable import list_timetable_versions
    return await list_timetable_versions(db=db)

