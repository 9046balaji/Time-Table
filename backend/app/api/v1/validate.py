from fastapi import APIRouter, Depends
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.validate_service import ValidateService

router = APIRouter()


@router.get("/{version_id}", response_model=Dict[str, Any])
async def validate_timetable(
    version_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await ValidateService.validate_timetable(db=db, version_id=version_id)
