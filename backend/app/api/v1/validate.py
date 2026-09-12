from fastapi import APIRouter, Depends, Query
from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.services.validate_service import ValidateService

router = APIRouter()


@router.get("", response_model=Dict[str, Any])
@router.get("/", response_model=Dict[str, Any])
@router.get("/report", response_model=Dict[str, Any])
async def validate_timetable_default(
    version_id: int = Query(5),
    db: AsyncSession = Depends(get_db)
):
    return await ValidateService.validate_timetable(db=db, version_id=version_id)


@router.get("/report/{version_id}", response_model=Dict[str, Any])
@router.get("/{version_id}", response_model=Dict[str, Any])
async def validate_timetable_by_id(
    version_id: int,
    db: AsyncSession = Depends(get_db)
):
    return await ValidateService.validate_timetable(db=db, version_id=version_id)
